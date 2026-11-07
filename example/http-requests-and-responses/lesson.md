# HTTP Requests and Responses

> **Learning objective:** Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.

## 1. Hook and objective (about 2.5 min)

Picture two moments. First, you click a product link and a page appears. Later, you fill in a signup form, press Submit, and an account is created [S4]. Both moments are exchanges between your browser and a web server [S5]. They are different kinds of request, though. This lesson answers two questions. Which method should I use? What does the number in the reply tell me? You may suspect that GET and POST are interchangeable. Keep that suspicion in mind; we will test it.

Quick definitions. In HTTP, the party that starts an exchange is the client (typically a browser), which asks a server for something, and the server then replies following the same set of rules [S5]. One request with its answer forms a request-response cycle [S10]. A URL such as https://shop.example/search?q=pen has a scheme (https), a host (shop.example), a path (/search) and an optional query string (?q=pen) [S2, S10, S14]. Headers are metadata written as key-value pairs, for example the browser in use or the data wanted [S9]. A body is the data part of a message, such as typed form fields in a request or a page in a response [S2, S9]. A form submission is simply a convenient way to configure an HTTP request that carries the user's data to a server [S5]. Other methods (PUT, DELETE, PATCH) and the 1xx and 3xx status classes exist, but they are out of scope here [S6, S10].

Here is the objective in plain words. By the end you should be able to do six things. Describe the parts of a request and a response. Explain what GET is for. Explain what POST is for. Choose between them and justify the choice. Tell 2xx, 4xx and 5xx apart by who is responsible. Name the likely next action for a given status code. Practice and a short quiz will check each skill.

## 2. Anatomy of a request and a response (about 4 min)

Every HTTP message, request or response, has the same four-part shape: a start line, optional headers, an empty line, and an optional body [S2, S10]. The start line of a request holds three items: the method, the request target (usually a path) and the HTTP version [S2, S14]. Request headers add context, for example which formats the client accepts [S2]. The Host header names the site being asked for when the target is only a path [S2, S14].

The start line of a response is called the status line. It holds the version, a three-digit status code and an optional reason phrase, a short label for humans [S2, S10, S14]. The phrase is informational; software acts on the number [S2, S10]. Response headers describe the answer, such as its type or how it may be cached [S2]. Headers are metadata; Content-Type, for instance, tells the recipient what kind of data the body holds [S2, S5]. An empty line marks the end of the headers, and the body, if any, follows it [S2, S10].

Example (adapted from [S3]). The exchange below requests a contact page and receives it. The first line is the request line, and Host and Accept are request headers [S2]. The status line is HTTP/1.1 200 OK; Content-Type and Content-Length are response headers; the blank line separates them from the HTML body [S2].

```http
GET /contact HTTP/1.1
Host: example.com
Accept: */*

HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 1234

<html>...</html>
```

Two details prevent common mistakes. First, a body is optional. A GET request normally has none, because GET is meant for requesting data [S1, S3], while a response often carries one, such as the page above [S9, S10]. A POST request, by contrast, usually carries its data in the body, as a form submission does [S2, S5]. The body can also be structured data; a request body might hold JSON, for example [S2]. When a response has a body, Content-Type names its format, such as HTML or JSON [S2, S10]. If a request fails, the response body often describes why [S2].

Second, the browser does not decide the status code; the server does [S1]. The specification says that for a POST the origin server signals the meaning of its answer by choosing an appropriate status code [S1].

Newer protocol versions carry the same meaning without the text request line, so this layout still helps you read them [S2]. This lesson uses HTTP/1.1 notation throughout, as the MDN guide does for readability [S2]. Reading a raw message comes down to three questions. What is on the first line? Which headers follow? Is anything left after the blank line?

## 3. GET: asking for a representation (about 5 min)

GET asks the server for a representation of a resource, meaning a current view of it such as an HTML page [S1, S3]. It is the main way information is retrieved on the web [S1].

Where does GET's data travel? Not in a body. A GET request is meant only for requesting data, and a body sent with it has no generally defined meaning; some servers reject such a request with a 4xx error [S1, S3]. Instead, the data goes in the query string: a question mark after the path, then name=value pairs separated by ampersands [S2, S3, S5]. So the idea that GET cannot carry data is wrong; it carries data in the URL [S2, S5]. Following a link makes the browser send a GET [S8], and a form with method GET builds its query string from the form fields [S5].

Example. The first request below sends a search term and a page number in the query string (rule: [S3, S5]). The second asks for a product that does not exist, and the server answers 404 with a short JSON body (rule: a missing resource gets 404 [S9, S14]).

```http
GET /shop/search?q=pen&page=2 HTTP/1.1
Host: shop.example

GET /shop/products/9999 HTTP/1.1
Host: shop.example

HTTP/1.1 404 Not Found
Content-Type: application/json

{"error":"not found"}
```

Two technical words describe GET. A method is safe when the client neither asks for nor expects a state change on the server [S1]. Safe does not mean the server does nothing: it may still write access logs, but the client cannot be blamed for that [S1]. A method is idempotent when many identical requests have the same intended effect on the server as one request [S1, S13]. Every safe method is also idempotent [S1, S10, S13], so repeating a GET does not change the data you asked about, although the response itself may differ between calls [S13]. A store might count every view of an order page; the counter changes, yet GET stays idempotent because the client asked only to read [S13].

GET responses are cacheable, so a cache may reuse them [S1], and a GET URL can be bookmarked or linked [S8, S10]. A site that used a POST form for a read-only catalogue lookup would stop users from bookmarking the query or sharing it by link [S8]. These guarantees let crawlers and pre-fetching software follow links without fear of causing harm [S1].

The safe rule binds the site owner. If a link such as page?do=delete deletes something on GET, crawlers and pre-fetchers that follow links can trigger the deletion, and the fault lies with the resource owner, not with the automated visitor [S1, S8].

Because the data is in the URL, it shows in the address bar [S5] and can reach other servers' logs [S8], so sensitive values do not belong there [S5, S8]. Because a GET is designed to put all the information it needs in the URL, the URL alone is enough to repeat the lookup later [S8]. URLs also have length limits, which vary between browsers and servers, so very large inputs may not fit [S5].

## 4. POST: submitting data, and choosing between GET and POST (about 7 min)

POST asks the target resource to process the data enclosed in the request according to that resource's own rules [S1]. Typical uses include sending form fields to a handler, posting a message to a forum or blog, and creating a new resource [S1, S4, S10]. POST is a general-purpose method: what it does depends on the target resource [S1].

Where does POST's data travel? Usually in the request body, so nothing is appended to the URL [S5]. The Content-Type header describes the body, for example the URL-encoded form format that browsers use by default [S4, S5].

Example. A client creates an order and the server answers 201 Created. A server should include a Location header identifying the new resource (rule: [S1, S6]).

```http
POST /orders HTTP/1.1
Host: shop.example
Content-Type: application/json

{"items":["pen"]}

HTTP/1.1 201 Created
Location: /orders/ord_1001
```

Sending the identical request again can create a second order with a new identifier; a published example shows ord_1001 and then ord_1002 [S13]. Repeating a POST can therefore repeat its effect.

POST is not safe, because it may create or change state on the server [S1, S8, S10]. It is also not guaranteed to be idempotent: repeating it may repeat the effect, such as sending a second email [S1, S10]. For that reason, a client should not retry such a request automatically unless it has a way to know the retry is harmless or that the first attempt was never applied [S1]. Browsers may warn before a reload resubmits a POST, but handling duplicate submissions is mostly the web application's job [S10].

Responses to POST are typically not cached; caches are built mainly around GET [S1]. A page produced by a POST is typically not bookmarkable either, because the URL does not hold the submitted data [S8].

A common myth says POST is secure and GET is not. It is wrong: neither method encrypts anything by itself. A form sent to an HTTPS address has its data encrypted together with the whole request, while a form sent to a plain HTTP address gets no encryption [S5]. For data carried by either GET or POST, a secure protocol is often appropriate [S8]. Picture it this way: POST keeps data out of the address bar and URL logs [S5, S8], but HTTPS is the sealed tube around the whole message, whichever method carries it. Never put a password in a GET URL, because it may show in the address bar [S5]; use POST over HTTPS instead. For large inputs POST is preferred, because browsers and servers limit URL length [S5].

Putting it together:

| Aspect | GET | POST | Sources |
|---|---|---|---|
| Data location | query string in the URL | usually the body | [S2, S5] |
| Length limits | URL limits apply | preferred for large data | [S5] |
| Visibility | address bar, can reach logs | not in the URL | [S5, S8] |
| Side effects | safe: none requested | may create or change state | [S1] |
| Repeatability | idempotent | not guaranteed idempotent | [S1, S13] |
| Caching | cacheable | typically not cached | [S1] |

Choose with three questions. Is this a read-only lookup that people might share, bookmark or cache? Use GET [S8, S10]. Does it submit, create or change something? Use POST [S8, S10]. Is the data large, or a secret such as a password that must stay out of the URL? Use POST, and send any sensitive data over HTTPS whichever method you use [S1, S5, S8]. Example: a product lookup by ID is a GET, a signup form is a POST, and a login form is a POST over HTTPS.

So GET and POST are not interchangeable: the choice changes what is safe, cacheable, repeatable and shareable [S1, S8]. Because following a link issues a GET, changes placed behind a GET can be triggered by crawlers, which is why changes belong in POST [S1, S8]. Browsers and other user agents should help users notice an unsafe action before it is requested [S1]. Almost every status code can come back from a POST [S1]. For instance, a POST with a malformed body may be rejected with a 4xx such as 400 [S6].

## 5. Status codes: 2xx, 4xx and 5xx (about 6 min)

The first digit of a status code names its class [S6, S10, S12, S14]. Five classes exist, and this lesson covers three. The informational 1xx class and the redirecting 3xx class, where the client must take further action such as following a Location header, are out of scope [S9, S10, S12]. The server chooses the status code, not the browser [S1]. A response with a code is not automatically a success: 2xx means success, while a leading 4 or 5 signals an error [S9].

Class summary:

| Class | Meaning | Who is responsible | Usual next action | Examples |
|---|---|---|---|---|
| 2xx | received, understood, accepted [S10, S12] | nobody; it worked | use the response | 200, 201, 204 |
| 4xx | fault in the request, such as bad syntax, missing authentication or a missing resource [S10, S12] | the client | change the request before retrying [S12] | 400, 401, 403, 404 |
| 5xx | valid request, server failed [S10, S12] | the server | server side fixes it; client may retry later [S12] | 500, 502, 503 |

Success has several codes, so 200 is not the only one [S6]. 200 OK means the request succeeded; for a GET, the requested resource arrives in the response body [S6, S11]. For a POST, a 200 describes the result of the action [S6, S11]. 201 Created means a new resource now exists, typically after a POST [S6]; it normally carries a Location header and may include a representation [S1]. 204 No Content means success with nothing to send back [S6, S11].

A 4xx code blames the request, so sending the identical request again usually brings the same answer [S12]. 400 Bad Request means the server rejects a request it sees as faulty, for instance because its syntax is malformed [S6]. 401 Unauthorized means the request lacks valid credentials, and it arrives with a WWW-Authenticate header describing what the server expects [S7]. 403 Forbidden means the credentials are valid but the client lacks permission, which is the key difference from 401 [S7]. In short, 401 says the server does not know who you are, while 403 says it knows and still refuses [S6, S7]. 404 Not Found means the server cannot find the resource [S6]; a server may even answer 404 instead of 403 to hide that a resource exists [S6]. So 404 is only one of many client errors [S6]. Side note, not needed for the practice: two 4xx codes, 408 Request Timeout and 429 Too Many Requests, mean 'wait, then retry' rather than 'change the request' [S12].

A 5xx code blames the server, so waiting and sending the same request again often works [S12]. 500 Internal Server Error is a generic failure when no more specific 5xx code fits [S6, S11]. 502 Bad Gateway means a server acting as a gateway or proxy received an invalid answer from the server behind it [S6, S11]. 503 Service Unavailable means the server is not ready, for instance because it is overloaded or down for maintenance; it signals a temporary condition and may carry a Retry-After header [S6]. Either GET or POST can receive a 5xx [S1, S11]. Because a 5xx answers an apparently valid request, it does not mean the client erred [S10, S12].

Retrying needs care. A GET can usually be tried again later, ideally after a pause [S1, S12]. A POST is different: a client that gets no answer cannot tell whether the server processed it, so a blind retry can create a duplicate such as a second order [S1, S13]. To decide quickly, ask who must change something before retrying. If the answer is you, expect a 4xx; if it is the server owner, expect a 5xx [S12]. A client that meets an unfamiliar code can fall back on its class, treating an unknown 4xx as a generic client error [S10, S12].

Example. Reuse the three exchanges you have seen: GET /contact returned 200 OK, GET /shop/products/9999 returned 404 Not Found, and POST /orders returned 201 Created (rules: [S6, S1]). Now add one new line from a valid POST /orders. A 404 tells the client to fix the URL; the 503 below tells the client to wait and retry, but only after checking whether the order was already created (rules: [S6, S12, S1]).

```http
POST /orders HTTP/1.1
Host: shop.example
Content-Type: application/json

{"items":["pen"]}

HTTP/1.1 503 Service Unavailable
Retry-After: 120
```

So drop these slogans: any code means success; 200 is the only success; 4xx and 5xx are the same; 404 is the only client error; 5xx means the client erred [S6, S9, S12].

## Watch and notice (about 5 min)

{{video:S17}}

Notice three things. First, the request line, headers, blank line and body. Second, the first-digit status shortcut; pause before the signup challenge is answered. Third, the "sealed tube" pictures HTTPS, not POST. Skip the PUT, PATCH, DELETE and 3xx passages; safe and idempotent get only light treatment here.

## Practice (about 8 min)

[activity: 6 min] Work through the triage desk with pen and paper. Cover the key until you have written all nine answers. Step 1 (1 min): annotate the POST /orders request from section 4, labelling the request line, headers, blank line and body. Step 2 (2 min): pick GET or POST for items A to D and write a one-line reason. Step 3 (3 min): for items E to I, name the class, who is responsible and the next action. Then compare with the key. Missed any of A-D? Reread section 4 ('Choose with three questions'). Missed any of E-I? Reread section 5 (class table and 'Retrying needs care'). Extra: for G, write one sentence on why a retry could duplicate the order.

Items (Example scenarios):

- A. Look up one product by ID.
- B. Submit a signup form that creates an account.
- C. A search box whose results should be shareable by link.
- D. Send a password to log in. What else is needed?
- E. GET /shop/products/9999 returns 404.
- F. A valid POST /orders returns 201.
- G. A valid POST /orders returns 503.
- H. A request returns 403 after you log in.
- I. A request returns 502 from the proxy.

Key (rules from sections 4 and 5 [S1, S5, S7, S8, S12]):

- A. GET: read-only, so it is safe and idempotent, and the response is cacheable.
- B. POST: creates state.
- C. GET: shareable, bookmarkable URL.
- D. POST over HTTPS; HTTPS encrypts, POST alone does not.
- E. 4xx, client; fix the URL.
- F. 2xx, success; nothing to fix.
- G. 5xx, server; retry later, beware duplicate order.
- H. 4xx, permissions; ask for access.
- I. 5xx, gateway trouble; retry later.

## Knowledge check (about 9 min)

1. Read this raw response. Which line holds the status code, and where does the body start?

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{"error":"not found"}
```

   (a) The status code is in the Content-Type line; the body starts at the first line.
   (b) The status code is in the first line; the body starts after the blank line.
   (c) The status code is in the last line; the body starts after Content-Type.

2. Which statement is accurate?

   (a) GET sends its data in the query string and is safe and idempotent; repeating a POST may repeat its effect.
   (b) GET cannot carry data, so every request with data must be a POST.
   (c) GET and POST are interchangeable; the choice changes nothing for caching or repeating.

3. A recipe site lets users filter recipes by ingredient, and users often send the filtered list to friends. Which method fits, and why?

   (a) POST, because filters are user input and user input always goes in a body.
   (b) GET, because the lookup is read-only and the filter in the query string makes the result shareable by link.
   (c) POST, because GET responses cannot carry a list of results.

4. A friend says: "Any response with a status code means success, 200 is the only success code, and 4xx and 5xx are the same kind of error." Which correction is right?

   (a) 2xx means success (200, 201 and 204 are examples); 4xx blames the request, 5xx blames the server.
   (b) Only 200 means success; 4xx and 5xx both mean the client erred.
   (c) 2xx means success; 4xx and 5xx both mean the request was faulty, so the client should change it before retrying.

5. A `POST /orders` with the body `{"items":}` returns `400 Bad Request`. Which class is it, who must act, and what is the right next step?

   (a) 5xx; the server must recover, so the client should resend the same body later.
   (b) 4xx; the client must fix the malformed body before sending again, because resending it unchanged will fail again.
   (c) 4xx; the client should retry the identical request immediately, since 400 is temporary.

**Answers:** (1) (b): the status line is the first line (version, code, reason phrase), and an empty line ends the headers, with the body after it [S2] (2) (a): GET data travels in the query string and GET is safe and idempotent, while POST is not guaranteed idempotent, so repeating it may repeat the effect [S1, S5] (3) (b): filtering is a read-only lookup, so GET fits; the filter travels in the query string, and a URL that holds it can be bookmarked and shared [S5, S8, S10] (4) (a): 2xx is success and includes more than 200, a leading 4 or 5 signals an error, and 4xx is the client's job to fix while 5xx is the server's [S9, S12] (5) (b): 400 is a 4xx client error, here caused by malformed syntax in the body, so the client must change the request before retrying; sending it unchanged puts the same fault in front of the server again [S6, S12]

## Wrap-up (about 2 min)

Three rules to remember.

First, GET reads. Its data travels in the URL query string, and the method is safe and idempotent [S1, S5].

Second, POST submits. Its data travels in the body, and it is not guaranteed to be idempotent, so repeating it may repeat the effect [S1, S5, S13].

Third, the first digit of the status tells you who acts. A 2xx means it worked, a 4xx means fix the request, and a 5xx means the server side must fix it, with the client retrying later and taking care with POST [S1, S12].

One last correction: HTTPS, not POST, protects data in transit, and it does so for both methods [S5, S8].

Next steps. Open your browser's developer tools, choose the Network tab, and watch real requests and responses while you load a page and submit a form [S2, S5]. For each one, find the method, the status code and the class. Then compare your notes with the three rules above. When you are ready for more, study PUT, DELETE and PATCH, and the 1xx and 3xx status classes, which this lesson left out.

Good work finishing the lesson. You now have the vocabulary to read a raw HTTP exchange and the habit of asking the two key questions: which method, and who must act on the status. Keep both questions in mind whenever you build or debug a web feature, and return to the practice triage whenever you want a quick refresher. Take a short break, then retry any quiz question you missed and explain the answer aloud.
