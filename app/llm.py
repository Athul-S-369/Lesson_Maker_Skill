"""LLM client (httpx, no SDK): Anthropic Messages API plus an optional OpenAI-compatible
second vendor for QC. Features: retries, forced tool-use JSON (with text-JSON fallback),
token/usage tracking with a per-stage budget, and a disk cache for deterministic calls."""
import contextvars
import hashlib
import json
import re
import time
from contextlib import contextmanager

import httpx

from .config import get_settings

API_URL = "https://api.anthropic.com/v1/messages"


class LLMError(Exception):
    pass


class LLMTruncated(LLMError):
    pass


# ---------------- usage tracking ----------------
_usage: contextvars.ContextVar = contextvars.ContextVar("llm_usage", default=None)


@contextmanager
def track():
    """Collects token usage for every LLM call made inside the block (also enforces the stage budget)."""
    u = {"calls": 0, "cached": 0, "input_tokens": 0, "output_tokens": 0, "models": {}}
    token = _usage.set(u)
    try:
        yield u
    finally:
        _usage.reset(token)


def _record(model: str, tin: int, tout: int, cached: bool = False) -> None:
    u = _usage.get()
    if u is None:
        return
    if cached:
        u["cached"] += 1
        return
    u["calls"] += 1
    u["input_tokens"] += tin
    u["output_tokens"] += tout
    m = u["models"].setdefault(model, {"input_tokens": 0, "output_tokens": 0})
    m["input_tokens"] += tin
    m["output_tokens"] += tout


def _check_budget() -> None:
    u = _usage.get()
    if u and u["input_tokens"] + u["output_tokens"] > get_settings().stage_token_budget:
        raise LLMError(f"Token budget for this step exceeded ({get_settings().stage_token_budget} tokens). "
                       "Raise STAGE_TOKEN_BUDGET in .env if this is expected.")


def cost_usd(usage: dict) -> float | None:
    s = get_settings()
    if s.price_in is None or s.price_out is None:
        return None
    return round(usage["input_tokens"] / 1e6 * s.price_in + usage["output_tokens"] / 1e6 * s.price_out, 4)


# ---------------- disk cache (temperature 0 only) ----------------
def _cache_path(key: str):
    d = get_settings().data_dir / "_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.txt"


def _cache_key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def _cache_get(key: str):
    if not get_settings().llm_cache:
        return None
    try:
        return _cache_path(key).read_text(encoding="utf-8")
    except OSError:
        return None


CACHE_MAX_FILES = 1500


def _cache_put(key: str, text: str) -> None:
    if get_settings().llm_cache and text:
        try:
            p = _cache_path(key)
            p.write_text(text, encoding="utf-8")
            files = list(p.parent.glob("*.txt"))
            if len(files) > CACHE_MAX_FILES:          # keep the cache bounded: drop the oldest quarter
                for old in sorted(files, key=lambda f: f.stat().st_mtime)[:CACHE_MAX_FILES // 4]:
                    old.unlink(missing_ok=True)
        except OSError:
            pass


# ---------------- transport ----------------
def _post_with_retries(url: str, body: dict, headers: dict, label: str, max_tokens: int, adjustable: bool = True):
    last = "unknown error"
    for attempt in range(3):
        _check_budget()
        try:
            r = httpx.post(url, json=body, headers=headers, timeout=180)
        except httpx.HTTPError as e:
            last = f"network error: {e}"
        else:
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}: {r.text[:300]}"
            retry_after = r.headers.get("retry-after", "")
            if retry_after.isdigit():
                time.sleep(min(int(retry_after), 30))
            if adjustable and r.status_code == 400 and "temperature" in r.text and "temperature" in body:
                del body["temperature"]
                continue
            if r.status_code not in (408, 409, 429, 500, 502, 503, 504, 529):
                break
        time.sleep(2 ** attempt)
    raise LLMError(f"{label} API call failed: {last}")


def _anthropic(system: str, user: str, model: str, max_tokens: int, temperature, tool: dict | None = None):
    s = get_settings()
    if not s.anthropic_key:
        raise LLMError("ANTHROPIC_API_KEY is not set.")
    body = {"model": model, "max_tokens": max_tokens, "system": system,
            "messages": [{"role": "user", "content": user}]}
    if temperature is not None:
        body["temperature"] = temperature
    if tool:
        body["tools"] = [tool]
        body["tool_choice"] = {"type": "tool", "name": tool["name"]}
    headers = {"x-api-key": s.anthropic_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    r = _post_with_retries(API_URL, body, headers, f"Claude ({model})", max_tokens)
    data = r.json()
    use = data.get("usage") or {}
    _record(model, int(use.get("input_tokens", 0)), int(use.get("output_tokens", 0)))
    if data.get("stop_reason") == "max_tokens":
        raise LLMTruncated(f"Model output was cut off at {max_tokens} tokens ({model}).")
    parts = data.get("content", [])
    if tool:
        for p in parts:
            if p.get("type") == "tool_use" and isinstance(p.get("input"), dict):
                return p["input"]
        return None
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


def _openai(system: str, user: str, model: str, max_tokens: int, temperature) -> str:
    s = get_settings()
    if not s.openai_key:
        raise LLMError("OPENAI_API_KEY is not set (QC_PROVIDER=openai).")
    body = {"model": model, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if temperature is not None:
        body["temperature"] = temperature
    r = _post_with_retries(f"{s.openai_base}/chat/completions", body,
                           {"Authorization": f"Bearer {s.openai_key}", "content-type": "application/json"},
                           f"OpenAI-compatible ({model})", max_tokens)
    data = r.json()
    use = data.get("usage") or {}
    _record(model, int(use.get("prompt_tokens", 0)), int(use.get("completion_tokens", 0)))
    choice = (data.get("choices") or [{}])[0]
    if choice.get("finish_reason") == "length":
        raise LLMTruncated(f"Model output was cut off at {max_tokens} tokens ({model}).")
    return (choice.get("message") or {}).get("content") or ""


def complete(system: str, user: str, *, model: str, max_tokens: int = 4000,
             temperature: float | None = None, provider: str = "anthropic") -> str:
    key = None
    if temperature == 0:
        key = _cache_key("text", provider, model, system, user, max_tokens)
        hit = _cache_get(key)
        if hit is not None:
            _record(model, 0, 0, cached=True)
            return hit
    out = _openai(system, user, model, max_tokens, temperature) if provider == "openai" \
        else _anthropic(system, user, model, max_tokens, temperature)
    if key:
        _cache_put(key, out)
    return out


# ---------------- JSON ----------------
def extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise LLMError("Model did not return JSON.")
    try:
        out = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise LLMError(f"Model returned malformed JSON: {e}") from e
    if not isinstance(out, dict):
        raise LLMError("Model returned JSON that is not an object.")
    return out


JSON_TOOL = {"name": "emit_result",
             "description": "Return the complete answer as one JSON object matching the schema described in the instructions.",
             "input_schema": {"type": "object", "additionalProperties": True}}


def _text_json(sys_json, user, model, max_tokens, temperature, provider) -> dict:
    return extract_json(complete(sys_json, user, model=model, max_tokens=max_tokens,
                                 temperature=temperature, provider=provider))


def complete_json(system: str, user: str, *, model: str, max_tokens: int = 6000,
                  temperature: float | None = None, provider: str = "anthropic") -> dict:
    """Preferred path on Anthropic: forced tool-use (schema-valid object, no code fences to strip).
    Falls back to text JSON if the tool call is unavailable; retries once on bad/truncated output."""
    sys_json = system + "\n\nReturn ONLY one valid JSON object. No prose, no code fences."
    key = _cache_key("json", provider, model, system, user, max_tokens) if temperature == 0 else None
    if key:
        hit = _cache_get(key)
        if hit:
            try:
                out = json.loads(hit)
                _record(model, 0, 0, cached=True)
                return out
            except json.JSONDecodeError:
                pass
    result = None
    if provider == "anthropic":
        try:
            result = _anthropic(sys_json, user, model, max_tokens, temperature, tool=JSON_TOOL)
        except LLMTruncated:
            result = None
        except LLMError as e:
            if "ANTHROPIC_API_KEY" in str(e):
                raise
            result = None  # e.g. tool use unsupported -> fall back to text mode below
    if result is None:
        try:
            result = _text_json(sys_json, user, model, max_tokens, temperature, provider)
        except LLMTruncated:
            more = min(16000, int(max_tokens * 1.7))
            result = _text_json(sys_json, user + "\n\nYour previous reply was cut off. Be more concise "
                                "(fewer items, shorter strings) and reply with only the JSON object.",
                                model, more, temperature, provider)
        except LLMError as e:
            if "API call failed" in str(e) or "not set" in str(e):
                raise
            result = _text_json(sys_json, user + "\n\nYour previous reply was not valid JSON. "
                                "Reply again with only the JSON object.", model, max_tokens, temperature, provider)
    if key:
        _cache_put(key, json.dumps(result, ensure_ascii=False))
    return result
