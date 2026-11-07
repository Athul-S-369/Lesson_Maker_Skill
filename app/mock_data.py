"""Offline mock data so the whole workflow runs without any API keys.

Everything produced from this module is labelled MOCK in the UI. The sample
HTTP lesson deliberately contains two flaws so the QC layers have something
real to catch in an offline demo.
"""
from urllib.parse import quote_plus

HTTP_SOURCES = [
    {"type": "web", "title": "HTTP request methods - MDN Web Docs",
     "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods",
     "snippet": "HTTP defines request methods that indicate the desired action for a resource.",
     "text": ("HTTP defines a set of request methods to indicate the desired action to be "
              "performed for a given resource. The GET method requests a representation of the "
              "specified resource. Requests using GET should only retrieve data and should not "
              "contain a request body. The POST method submits an entity to the specified "
              "resource, often causing a change in state or side effects on the server. A safe "
              "method does not alter the state of the server. GET is safe and idempotent: making "
              "the same request several times has the same effect as making it once. POST is "
              "neither safe nor idempotent, so repeating a POST may create multiple resources."),
     "published": "2024-01-15"},
    {"type": "web", "title": "HTTP response status codes - MDN Web Docs",
     "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
     "snippet": "Status codes are grouped into five classes by their first digit.",
     "text": ("HTTP response status codes indicate whether a specific HTTP request has been "
              "successfully completed. Responses are grouped in five classes: informational "
              "responses (100-199), successful responses (200-299), redirection messages "
              "(300-399), client error responses (400-499), and server error responses "
              "(500-599). 200 OK means the request succeeded. 201 Created means the request "
              "succeeded and a new resource was created, typically after a POST. 204 No Content "
              "means success with no body. 400 Bad Request means the server cannot process the "
              "request due to a client error. 401 Unauthorized means the client lacks valid "
              "authentication credentials. 403 Forbidden means the client is known but not "
              "permitted. 404 Not Found means the server cannot find the requested resource. "
              "500 Internal Server Error means the server hit an unexpected condition. 503 "
              "Service Unavailable means the server is not ready to handle the request."),
     "published": "2024-03-02"},
    {"type": "web", "title": "RFC 9110: HTTP Semantics",
     "url": "https://www.rfc-editor.org/rfc/rfc9110",
     "snippet": "The normative definition of HTTP methods and status code classes.",
     "text": ("The first digit of the status code defines the class of response. 1xx "
              "(Informational): the request was received, continuing process. 2xx (Successful): "
              "the request was successfully received, understood, and accepted. 3xx "
              "(Redirection): further action needs to be taken in order to complete the request. "
              "4xx (Client Error): the request contains bad syntax or cannot be fulfilled. 5xx "
              "(Server Error): the server failed to fulfill an apparently valid request. The GET "
              "method requests transfer of a current selected representation for the target "
              "resource. The POST method requests that the target resource process the "
              "representation enclosed in the request according to the resource's own specific "
              "semantics."),
     "published": "2022-06-01"},
    {"type": "video", "title": "HTTP Crash Course (search for a current explainer)",
     "url": "https://www.youtube.com/results?search_query=http+requests+and+responses+explained",
     "snippet": "MOCK video placeholder: run in live mode to fetch real, embeddable videos.",
     "channel": "mock", "duration_sec": 420, "video_id": None, "views": None, "published": None},
    {"type": "book", "title": "HTTP: The Definitive Guide",
     "url": "https://www.google.com/books/feeds/volumes?q=http+the+definitive+guide",
     "snippet": "Gourley and Totty. O'Reilly Media. Reference text on HTTP internals.",
     "text": "", "author": "David Gourley, Brian Totty", "published": "2002-09-27"},
]


def sources_for(title: str, objective: str) -> list[dict]:
    if "http" in (title + objective).lower():
        return [dict(s) for s in HTTP_SOURCES]
    q = quote_plus(title)
    return [
        {"type": "web", "title": f"{title} - Wikipedia search",
         "url": f"https://en.wikipedia.org/w/index.php?search={q}",
         "snippet": f"MOCK source for '{title}'. Use live mode for real research.",
         "text": f"This is placeholder reference text about {title} for offline demonstration. "
                 "Run the tool in live mode with API keys to research real sources.",
         "published": None},
        {"type": "video", "title": f"{title} - YouTube search",
         "url": f"https://www.youtube.com/results?search_query={q}",
         "snippet": "MOCK video placeholder.", "channel": "mock", "duration_sec": 420,
         "video_id": None, "views": None, "published": None},
        {"type": "book", "title": f"Books about {title}",
         "url": f"https://www.google.com/search?tbm=bks&q={q}",
         "snippet": "MOCK book placeholder.", "text": "", "author": "n/a", "published": None},
    ]


def lesson_for(title: str, objective: str, sources: list[dict]) -> str:
    web = [s["id"] for s in sources if s["type"] == "web"]
    vid = next((s["id"] for s in sources if s["type"] == "video"), None)
    w = lambda i: f"[{web[i % len(web)]}]" if web else ""
    video = f"{{{{video:{vid}}}}}" if vid else ""
    if "http" in (title + objective).lower():
        return f"""# {title}

> **Learning objective:** {objective}

## 1. Hook and objective (about 4 min)
Every time you open a web page, your browser and a server hold a short conversation. The browser sends a *request*; the server sends back a *response*. By the end of this lesson you will explain GET and POST and read the 2xx, 4xx and 5xx status families at a glance. {w(0)}

## 2. Request methods: GET and POST (about 10 min)
**GET** asks the server for a representation of a resource and should only retrieve data; it carries no request body. {w(0)} GET is *safe* (it does not change server state) and *idempotent* (repeating it has the same effect as doing it once). {w(0)}

**POST** sends data to the server to be processed, often creating a resource or causing side effects. {w(0)} Repeating a POST may create duplicates, so it is neither safe nor idempotent. {w(0)}

GET requests are always faster than POST requests, which is why you should prefer GET everywhere.

| | GET | POST |
|---|---|---|
| Purpose | Retrieve data | Submit data for processing |
| Body | No | Yes |
| Safe / idempotent | Yes / Yes | No / No |

**Example.** Loading `https://example.com/products/42` is a GET. Submitting the checkout form sends a POST with the order details in the body.

## 3. Response status code classes (about 10 min)
The first digit of the status code tells you the class. {w(2)}

- **2xx - Success.** 200 OK, 201 Created (typical after a POST), 204 No Content. {w(1)}
- **4xx - Client error.** 400 Bad Request, 401 Unauthorized, 403 Forbidden. A 404 Not Found response belongs to the 5xx server-error family because the server could not find the page. {w(1)}
- **5xx - Server error.** 500 Internal Server Error, 503 Service Unavailable. {w(1)}

Rule of thumb: 4xx means *fix your request*; 5xx means *the server has a problem*.

## 4. Watch and notice (about 6 min)
{video}
While watching, note one request and one response header you did not know about.

## 5. Practice: read the traffic (about 10 min)
[activity: 10 min] Open your browser developer tools, Network tab. Load any page, then pick three requests. For each, write the method, the status code, and which class it belongs to. Then predict what status you would get if you requested a URL that does not exist.

## 6. Knowledge check (about 5 min)
1. Which method should you use to retrieve a product page, and why?
2. A form submission creates a new account. Which method and which success code do you expect?
3. Your client receives 503. Is the fault in the request or the server?
4. Classify: 200, 301, 404, 500.
5. Why can retrying a POST be risky?

**Answers:** (1) GET, safe and idempotent. (2) POST, 201 Created. (3) The server. (4) 2xx, 3xx, 4xx, 5xx. (5) It may create duplicate resources.

## 7. Wrap-up (about 2 min)
GET reads, POST submits. The first digit of the status code tells you who should act next.
"""
    obj = objective.rstrip(".")
    return f"""# {title}

> **Learning objective:** {obj}

## 1. Hook and objective (about 4 min)
Today's goal: {obj}. {w(0)}

## 2. Core concept (about 12 min)
MOCK content. In live mode this section is synthesised from researched sources and every claim carries a citation like [S1]. {w(0)}

## 3. Worked example (about 8 min)
MOCK worked example for {title}. {w(0)}

## 4. Watch and notice (about 6 min)
{video}

## 5. Practice (about 10 min)
[activity: 10 min] Apply the concept to a small scenario of your own.

## 6. Knowledge check (about 5 min)
1. Explain the main idea in your own words.
2. Give one example.
3. Name one common mistake.

## 7. Wrap-up (about 2 min)
Recap of {title}.
"""
