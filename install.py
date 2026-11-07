"""Installs the hire-athul-lesson-maker skill and its 12 agents into your Claude Code folder (~/.claude).

    python install.py              # copy the skill and agents, then pip install the requirements
    python install.py --no-pip     # copy only (skip the Python packages)

After it runs, start a NEW Claude Code session and type:
    /hire-athul-lesson-maker <lesson title> | <learning objective>
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAUDE = Path.home() / ".claude"
SKILL = "hire-athul-lesson-maker"


def main() -> int:
    skill_dst = CLAUDE / "skills" / SKILL
    agents_dst = CLAUDE / "agents"
    skill_dst.mkdir(parents=True, exist_ok=True)
    agents_dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(HERE / SKILL, skill_dst, dirs_exist_ok=True)
    # the skill reads this file to find app/gate.py and app/scraper.py (this folder)
    (skill_dst / "project_root.txt").write_text(str(HERE), encoding="utf-8")
    agents = sorted((HERE / "agents").glob("kl-*.md"))
    for f in agents:
        shutil.copy2(f, agents_dst / f.name)
    print(f"Skill installed:  {skill_dst}")
    print(f"Agents installed: {len(agents)} files in {agents_dst}")
    print(f"Project root:     {HERE}  (keep this folder; the skill runs its code from here)")
    if "--no-pip" not in sys.argv:
        print("\nInstalling Python packages (scrapling can take a minute)...")
        code = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(HERE / "requirements.txt")]).returncode
        if code:
            print("pip failed: run  python -m pip install -r requirements.txt  yourself, then re-run the skill.")
    print("\nDone. Start a NEW Claude Code session, then run:\n"
          "  /hire-athul-lesson-maker HTTP Requests and Responses | Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
