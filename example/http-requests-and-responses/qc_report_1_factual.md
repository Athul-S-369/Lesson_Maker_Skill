# QC report 1: factual accuracy

Source: second-pass `factcheck.json` (the first pass is kept in `factcheck_pass1.json`). Gate checks from `gate_report.json`.

## Verdict counts

| Verdict | Claims |
|---|---|
| supported | 140 |
| partially_supported | 3 |
| unsupported | 0 |
| contradicted | 0 |
| unverifiable | 3 |
| **Total** | **146** |

By kind: claim 124, quiz 22.

Related gate checks: evidence (146 claims checked), coverage (45/45), support (140 supported, 3 partial, 3 weak), contradictions (pass), fact_issues (pass).

Note: the `summary` text in factcheck.json says 145 claims checked (139 supported). The claims array holds 146 entries (140 supported), which matches the gate's count. The table and counts above use the claims array.

## First pass

The first pass (factcheck_pass1.json) checked 137 claims and found 7 minor issues (F1-F7). 5 were applied (F1, F2, F4, F5, F6); F3 and F7 had no replacement and stay `needs_human`. The second pass verified the applied fixes and found no new issues.

## Release-pass edits

The release pass made two cosmetic edits (pedagogy issues P1 and P4). Neither removed or changed a checked claim: all 146 claim quotes still occur verbatim in the final lesson, and the gate re-run passed.

## Issues

| ID | Severity | Category | Status | Problem | Note |
|---|---|---|---|---|---|
| F1 | minor | misleading | applied | Presented as a general statement of the spec, but the only S1 text on this is in the POST section ('...depending on the result of processing the POST request'). The same POST-specific sentence is the basis for 'The server chooses the status code, not the browser [S1].' in section 5. | Pass 2: the replacement is in lesson.md verbatim and matches S1. The two neighbouring general sentences ('the browser does not decide the status code; the server does [S1]' and 'The server chooses the status code, not the browser [S1].') still rest on POST-specific S1 text and remain partially_supported. That is acceptable (the claim is true and S1 is the best available) but could be cited more broadly. |
| F2 | minor | misleading | applied | Cited S8 does not support a blanket 'sensitive means POST' rule. For sensitive safe reads it recommends GET over a secure connection instead of moving data into a POST body ('Rather than moving my account number from the URI into the body of a POST request, my bank allows me to establish a secure HTTP connection'). S1 and S5 support POST for passwords and large data, and S1 says POST helps 'particularly when there is no benefit from caching'. | Pass 2: the replacement is in lesson.md verbatim. The POST rule is now limited to large data and URL-excluded secrets (S5, S1), and HTTPS is applied to either method (S8). Now supported. |
| F3 | minor | unsupported | needs_human | Only partly supported. S2 covers the path and query string and S14 covers the scheme. None of the cited sources names 'host' as a URL component. S10 adds nothing about URL parts. | No replacement provided; left for a human. Unchanged in pass 2. |
| F4 | minor | unsupported | applied | 'permission missing' is not in S9 or S10. S12 mentions only 'missing Authentication'. The permission framing for 403 comes from S7, which is not cited here. | Pass 2: the replacement row is in lesson.md verbatim and nearly quotes S12 ('such as malformed syntax, missing Authentication , or a non-existent resource'). Now supported. The examples column still lists 403, which the meaning cell does not name, but 'such as' marks the list as non-exhaustive and section 5 covers 403 with S7. |
| F5 | minor | misleading | applied | S12 states this flatly, but it is too absolute. S11 says 404 resources 'may be available in the future. Subsequent requests by the client are permissible', and the lesson itself names 408 and 429 as exceptions two sentences later. A 403 may also change once access is granted (Practice H). | Pass 2: the replacement is in lesson.md verbatim. 'Usually' is now consistent with the rewritten 408/429 side note at the end of the same paragraph. |
| F6 | minor | unsupported | applied | The key's answers depend on S5 and S8 (D: HTTPS encrypts and POST alone does not; A and C: shareable GET) and on S7 (H: 403 means a permission problem). None of these is cited, so as cited, answer D is unsupported. | Pass 2: the replacement is in lesson.md verbatim. Key D and Key H are now supported by the cited S5/S8 and S7. |
| F7 | minor | source_reliability | needs_human | These lines describe what video S17 contains (a signup challenge, a 'sealed tube' image, PUT/PATCH/DELETE and 3xx passages). S17 has no transcript or text, so none of this can be checked against the sources. | No replacement provided; left for a human. Video S17 content must be checked by hand. Unchanged in pass 2. |

## Claims that are not fully supported

| # | Claim | Cited | Verdict | Note |
|---|---|---|---|---|
| 5 | URL has scheme, host, path, optional query string | S2, S10, S14 | partially_supported | S2 supports path + query string; S14 supports scheme ('The first part of a URI is a scheme'). No cited source explicitly decomposes a URL into host as a named component; S10 adds nothing on URL parts. |
| 27 | Server, not browser, decides the status code | S1 | partially_supported | S1 excerpt states this only in the POST section; the general claim is correct but the cited text is POST-specific. Unchanged in pass 2; the following sentence now correctly scopes the spec paraphrase to POST. |
| 63 | Neither method encrypts by itself |  | unverifiable | Uncited substantive claim, so there is no cited source text to quote. It agrees with S5 ('the data is encrypted along with the rest of the request' for HTTPS action URLs; 'the data will not be encrypted' for HTTP) and S8, which are cited in the following sentences. Consider adding [S5, S8] to this sentence. |
| 85 | Server chooses status code | S1 | partially_supported | Same as section 2: S1 text is POST-specific. Unchanged in pass 2. |
| 117 | Video viewing notes describe S17 content | S17 | unverifiable | S17 is a video with no transcript/text; its content cannot be verified. |
| 118 | Practice remediation pointers (pass 2, new) |  | unverifiable | Internal cross-reference, not a source claim. Checked against lesson.md: section 4 contains 'Choose with three questions' and section 5 contains the class table and 'Retrying needs care'. The pointers are accurate; there is no source text to quote. |

## Full claim table

| # | Kind | Claim | Cited | Verdict | Evidence quote | Confidence |
|---|---|---|---|---|---|---|
| 1 | claim | Signup form submission creates an account | S4 | supported | Adding a new user through a signup form. | 0.9 |
| 2 | claim | Both moments are browser-server exchanges | S5 | supported | a client (usually a web browser) sends a request to a server | 0.9 |
| 3 | claim | Client starts exchange; server replies with same rules | S5 | supported | The server answers the request using the same protocol. | 0.9 |
| 4 | claim | Request plus answer forms a request-response cycle | S10 | supported | A transaction starts with a client submitting a request to the server | 0.75 |
| 5 | claim | URL has scheme, host, path, optional query string | S2, S10, S14 | partially_supported | A query string can be appended to the path for additional information (usually in key=value format). | 0.7 |
| 6 | claim | Headers are key-value metadata e.g. browser and data wanted | S9 | supported | These headers communicate core information, such as what browser the client is using and what data is being requested. | 0.95 |
| 7 | claim | Body is the data part: form fields in request, page in response | S2, S9 | supported | This might be POST data to send to the server in a request, or some resource returned to the client in a response. | 0.9 |
| 8 | claim | Form is a convenient way to configure an HTTP request | S5 | supported | An HTML form on a web page is nothing more than a convenient user-friendly way to configure an HTTP request to send data to a server. | 0.95 |
| 9 | claim | Other methods and 1xx/3xx classes exist | S6, S10 | supported | Responses are grouped in five classes: Informational responses ( 100 – 199 ) Successful responses ( 200 – 299 ) Redirection messages ( 300 – 399 ) | 0.85 |
| 10 | claim | Every message: start line, optional headers, empty line, optional body | S2, S10 | supported | An empty line indicating the metadata of the message is complete. An optional body containing data associated with the message. | 0.85 |
| 11 | claim | Request start line: method, target, version | S2, S14 | supported | and is made of three parts: <method> <request-target> <protocol> | 0.95 |
| 12 | claim | Request headers add context e.g. accepted formats | S2 | supported | For example, a request for a resource might include the allowed formats of that resource | 0.9 |
| 13 | claim | Host header names the site when target is only a path | S2, S14 | supported | In origin form , the recipient combines an absolute path with the information in the Host header. | 0.9 |
| 14 | claim | Status line: version, 3-digit code, optional reason phrase | S2, S10, S14 | supported | The start line of a response consists of the protocol version, a status code and optionally a reason phrase | 0.95 |
| 15 | claim | Reason phrase informational; software acts on number | S2, S10 | supported | the standard explicitly specifies that status codes are machine-readable and reason phrases are human-readable | 0.9 |
| 16 | claim | Response headers describe type or caching | S2 | supported | such as its content type ( Content-Type ), or how it should be cached ( Cache-Control ) | 0.95 |
| 17 | claim | Content-Type tells kind of body data | S2, S5 | supported | the Content-Type header indicates the type of resource sent to the server | 0.9 |
| 18 | claim | Empty line ends headers; body follows | S2, S10 | supported | Empty line. Marks the end of the header. | 0.95 |
| 19 | claim | Example adapted from S3 | S3 | supported | GET /contact HTTP/1.1 Host: example.com User-Agent: curl/8.6.0 Accept: */* | 0.9 |
| 20 | claim | First line is request line; Host and Accept are request headers | S2 | supported | Headers are metadata sent with a request after the start line and before the body. | 0.85 |
| 21 | claim | Status line, Content-Type/Content-Length headers, blank line before HTML body | S2 | supported | Single-resource bodies defined by the two headers: Content-Type and Content-Length | 0.8 |
| 22 | claim | GET normally has no body because it is meant for requesting data | S1, S3, S9, S10 | supported | Requests using GET should only be used to request data | 0.9 |
| 23 | claim | POST usually carries data in body | S2, S5 | supported | When the form is submitted using the POST method, you get no data appended to the URL | 0.9 |
| 24 | claim | Request body may hold JSON | S2 | supported | but a request body could contain other types of data that the server expects | 0.9 |
| 25 | claim | Content-Type names body format | S2, S10 | supported | The Content-Type header field specifies the Internet media type of the data conveyed by the HTTP message | 0.9 |
| 26 | claim | Failed request response body often describes why | S2 | supported | it's common for the response body to describe why the request failed | 0.9 |
| 27 | claim | Server, not browser, decides the status code | S1 | partially_supported | An origin server indicates response semantics by choosing an appropriate status code depending on the result of processing the POST request | 0.75 |
| 28 | claim | Spec: for a POST, origin server signals meaning by choosing an appropriate status code (pass 2, rewritten) | S1 | supported | An origin server indicates response semantics by choosing an appropriate status code depending on the result of processing the POST request | 0.95 |
| 29 | claim | Newer versions keep semantics without text request line | S2 | supported | However the underlying semantics of the protocol are the same | 0.9 |
| 30 | claim | MDN guide uses HTTP/1.1 for readability | S2 | supported | This guide uses HTTP/1.1 messages for readability | 0.95 |
| 31 | claim | GET asks for a representation of a resource | S1, S3 | supported | The GET HTTP method requests a representation of the specified resource. | 0.95 |
| 32 | claim | GET is main way of retrieval | S1 | supported | GET is the primary mechanism of information retrieval and the focus of almost all performance optimizations. | 0.95 |
| 33 | claim | GET body undefined; some servers reject with 4xx | S1, S3 | supported | Some servers may reject the request with a 4XX client error response. | 0.95 |
| 34 | claim | Query string format | S2, S3, S5 | supported | we include a question mark ( ? ) followed by the name/value pairs, each one separated by an ampersand ( & ) | 0.95 |
| 35 | claim | GET carries data in the URL | S2, S5 | supported | Because the body is empty, if a form is sent using this method the data sent to the server is appended to the URL. | 0.95 |
| 36 | claim | Following a link sends GET; GET form builds query string | S8, S5 | supported | When HTTP URIS are used for hyperlinks in HTML, SMIL, and SVG, for example, the application determines which method will be used (generally GET). | 0.9 |
| 37 | claim | Example: query string rule and 404 for missing resource | S9, S14 | supported | HTTP / 1.1 404 Not Found indicates that it was not able to satisfy the request because the page was not found. | 0.9 |
| 38 | claim | Safe method definition | S1 | supported | the client does not request, and does not expect, any state change on the origin server as a result of applying a safe method to a target resource | 0.95 |
| 39 | claim | Safe methods may still write access logs; client not accountable | S1 | supported | most servers append request information to access log files at the completion of every response, regardless of the method | 0.95 |
| 40 | claim | Idempotent definition | S1, S13 | supported | if the intended effect on the server of multiple identical requests with that method is the same as the effect for a single such request | 0.95 |
| 41 | claim | Safe implies idempotent; response may differ | S1, S10, S13 | supported | Idempotency compares the state of the server after one request with the state after many identical requests, and the responses are allowed to differ. | 0.9 |
| 42 | claim | View counter example keeps GET idempotent | S13 | supported | The log file and the counter change with every call, but GET stays idempotent, because the client asked only to read the order and the order does not change. | 0.95 |
| 43 | claim | GET responses cacheable; GET URL bookmarkable | S1, S8, S10 | supported | The response to a GET request is cacheable; a cache MAY use it to satisfy subsequent GET and HEAD requests | 0.95 |
| 44 | claim | POST form for catalogue lookup prevents bookmarking/sharing | S8 | supported | since the site designers created a POST Web form instead of a GET Web form for this read-only operation, Dan cannot bookmark the query | 0.95 |
| 45 | claim | Safety lets crawlers and pre-fetchers work without harm | S1 | supported | to allow automated retrieval processes (spiders) and cache performance optimization (pre-fetching) to work without fear of causing harm | 0.9 |
| 46 | claim | page?do=delete on GET; fault with resource owner | S1, S8 | supported | it is the resource owner's responsibility to ensure that the action is consistent with the request method semantics | 0.9 |
| 47 | claim | GET data shows in address bar, can reach other servers' logs; sensitive values do not belong | S5, S8 | supported | my account information may appear in the advertiser's server logs | 0.9 |
| 48 | claim | GET URL alone suffices to repeat lookup | S8 | supported | HTTP GET is designed so that all information necessary for the interaction is part of the URI, thus promoting URI addressability. | 0.9 |
| 49 | claim | URL length limits in browsers and servers | S5 | supported | the POST method is preferred because some browsers limit the sizes of URLs. In addition, many servers limit the length of URLs they accept. | 0.9 |
| 50 | claim | POST asks target resource to process enclosed data | S1 | supported | The POST method requests that the target resource process the representation enclosed in the request according to the resource's own specific semantics. | 0.95 |
| 51 | claim | Typical POST uses | S1, S4, S10 | supported | Providing a block of data, such as the fields entered into an HTML form, to a data-handling process | 0.95 |
| 52 | claim | POST general-purpose; depends on resource | S1 | supported | The POST method requests that the target resource process the representation enclosed in the request according to the resource's own specific semantics. | 0.85 |
| 53 | claim | POST data in body; nothing appended to URL | S5 | supported | When the form is submitted using the POST method, you get no data appended to the URL | 0.95 |
| 54 | claim | Content-Type describes body; URL-encoded default | S4, S5 | supported | A form using application/x-www-form-urlencoded content encoding (the default) sends a request where the body contains the form data in key=value pairs | 0.95 |
| 55 | claim | 201 should include Location header | S1, S6 | supported | the origin server SHOULD send a 201 (Created) response containing a Location header field that provides an identifier for the primary resource created | 0.95 |
| 56 | claim | Repeated POST creates ord_1001 then ord_1002 | S13 | supported | Location: /orders/ord_1001 HTTP/1.1 201 Created # second call Location: /orders/ord_1002 | 0.95 |
| 57 | claim | POST not safe | S1, S8, S10 | supported | They may modify the state of the server or have other effects such as sending an email | 0.95 |
| 58 | claim | POST not guaranteed idempotent; second email | S1, S10 | supported | sending an identical POST request multiple times may further modify the state of the server or have further effects, such as sending multiple emails | 0.95 |
| 59 | claim | Client should not auto-retry non-idempotent request | S1 | supported | A client SHOULD NOT automatically retry a request with a non-idempotent method unless it has some means to know that the request semantics are actually idempotent | 0.95 |
| 60 | claim | Browsers may warn on POST resubmission; app handles duplicates | S10 | supported | it is generally up to the web application to handle cases where a POST request should not be submitted more than once | 0.95 |
| 61 | claim | POST responses typically not cached; caches built mainly around GET (pass 2, rewritten) | S1 | supported | although the overwhelming majority of cache implementations only support GET and HEAD | 0.9 |
| 62 | claim | POST result page not bookmarkable | S8 | supported | With HTTP POST, some information intended to affect change to the resource state may be part of the protocol headers, not in the URI. | 0.8 |
| 63 | claim | Neither method encrypts by itself |  | unverifiable |  | 0.7 |
| 64 | claim | HTTPS form encrypted; plain HTTP not | S5 | supported | the data is encrypted along with the rest of the request | 0.9 |
| 65 | claim | Secure protocol appropriate for GET or POST data | S8 | supported | To protect information carried by either GET or POST operations, it is often appropriate to use an underlying secure protocol such as the Secure Socket Layer | 0.95 |
| 66 | claim | POST keeps data out of address bar and URL logs | S5, S8 | supported | with a GET request the user will see the data in their URL bar | 0.85 |
| 67 | claim | Never put password in GET URL | S5 | supported | never use the GET method or you risk displaying it in the URL bar, which would be very insecure | 0.95 |
| 68 | claim | POST preferred for large inputs | S5 | supported | the POST method is preferred because some browsers limit the sizes of URLs. In addition, many servers limit the length of URLs they accept. | 0.95 |
| 69 | claim | Table: data location | S2, S5 | supported | Because the body is empty, if a form is sent using this method the data sent to the server is appended to the URL. | 0.9 |
| 70 | claim | Table: length limits | S5 | supported | the POST method is preferred because some browsers limit the sizes of URLs | 0.95 |
| 71 | claim | Table: visibility | S5, S8 | supported | my account information may appear in the advertiser's server logs | 0.85 |
| 72 | claim | Table: side effects | S1 | supported | the client does not request, and does not expect, any state change on the origin server as a result of applying a safe method to a target resource | 0.9 |
| 73 | claim | Table: repeatability | S1, S13 | supported | Of the request methods defined by this specification, PUT , DELETE , and safe request methods are idempotent. | 0.95 |
| 74 | claim | Table: caching | S1 | supported | although the overwhelming majority of cache implementations only support GET and HEAD | 0.9 |
| 75 | claim | Read-only shareable lookup: GET | S8, S10 | supported | HTTP GET promotes URI addressability so, designers should adopt it for safe operations such as simple queries. | 0.95 |
| 76 | claim | Submits/creates/changes: POST | S8, S10 | supported | POST is appropriate for other types of applications where a user request has the potential to change the state of the resource | 0.95 |
| 77 | claim | Large data or URL-excluded secrets: POST; sensitive data over HTTPS with either method (pass 2, rewritten) | S1, S5, S8 | supported | To protect information carried by either GET or POST operations, it is often appropriate to use an underlying secure protocol such as the Secure Socket Layer | 0.9 |
| 78 | claim | GET and POST not interchangeable | S1, S8 | supported | Providing a URI for a resource affords many advantages, including: linking. bookmarking. caching. | 0.9 |
| 79 | claim | Changes behind GET can be triggered by crawlers; changes belong in POST | S1, S8 | supported | Per the HTTP/1.1 specification, designers should use HTTP POST for those interactions. | 0.9 |
| 80 | claim | User agents should help users notice unsafe actions | S1 | supported | such that the user can be made aware of an unsafe action before it is requested | 0.95 |
| 81 | claim | Almost every status code can come back from POST | S1 | supported | almost all of the status codes defined by this specification could be received in a response to POST | 0.95 |
| 82 | claim | Malformed POST may get 400 | S6 | supported | The server cannot or will not process the request due to something that is perceived to be a client error (e.g., malformed request syntax | 0.85 |
| 83 | claim | First digit names class | S6, S10, S12, S14 | supported | The first digit defines the class of response. | 0.95 |
| 84 | claim | 3xx requires further action such as following Location | S9, S10, S12 | supported | 3xx. Further action required. Follow the Location header. | 0.95 |
| 85 | claim | Server chooses status code | S1 | partially_supported | An origin server indicates response semantics by choosing an appropriate status code depending on the result of processing the POST request | 0.75 |
| 86 | claim | 2xx success; 4 or 5 signals error | S9 | supported | that means there was an error and the webpage will not be displayed | 0.9 |
| 87 | claim | 2xx: received, understood, accepted | S10, S12 | supported | Success responses indicate the request was received, understood, and accepted. | 0.95 |
| 88 | claim | 4xx row: fault in request such as bad syntax, missing authentication or missing resource (pass 2, rewritten cell) | S10, S12 | supported | Client error responses indicate the request contains a problem the server cannot process, such as malformed syntax, missing Authentication , or a non-existent resource. | 0.95 |
| 89 | claim | 4xx row (full table row) | S10, S12 | supported | 4xx. Problem in the request. Change the request before retrying. | 0.9 |
| 90 | claim | 5xx: valid request, server failed; retry later | S10, S12 | supported | 5xx. Server failed a valid request. Retry later or surface the failure. | 0.95 |
| 91 | claim | 200 is not the only success code | S6 | supported | There is no content to send for this request, but the headers are useful. | 0.9 |
| 92 | claim | 200 for GET: resource in body | S6, S11 | supported | GET : The resource has been fetched and transmitted in the message body. | 0.95 |
| 93 | claim | 200 for POST describes result | S6, S11 | supported | PUT or POST : The resource describing the result of the action is transmitted in the message body. | 0.95 |
| 94 | claim | 201 Created typically after POST | S6, S1 | supported | The request succeeded, and a new resource was created as a result. This is typically the response sent after POST requests, or some PUT requests. | 0.95 |
| 95 | claim | 204 No Content | S6, S11 | supported | There is no content to send for this request, but the headers are useful. | 0.95 |
| 96 | claim | 4xx: identical request usually brings same answer (pass 2, softened) | S12 | supported | A 4xx response places the fault in the request, so repeating the same request produces the same answer. | 0.9 |
| 97 | claim | 400 Bad Request | S6 | supported | The server cannot or will not process the request due to something that is perceived to be a client error (e.g., malformed request syntax | 0.95 |
| 98 | claim | 401 lacks valid credentials, WWW-Authenticate | S7 | supported | This status code is sent with an HTTP WWW-Authenticate response header that contains information on the authentication scheme the server expects | 0.95 |
| 99 | claim | 403 valid credentials but lacks permission | S7 | supported | a 403 is returned when a request contains valid credentials, but the client does not have permissions to perform a certain action | 0.95 |
| 100 | claim | 401 vs 403 identity | S6, S7 | supported | Unlike 401 Unauthorized , the client's identity is known to the server. | 0.9 |
| 101 | claim | 404 not found; may hide existence instead of 403 | S6 | supported | Servers may also send this response instead of 403 Forbidden to hide the existence of a resource from an unauthorized client. | 0.95 |
| 102 | claim | 404 is one of many client errors | S6 | supported | Client error responses ( 400 – 499 ) | 0.85 |
| 103 | claim | Side note: 408 and 429 mean wait then retry (pass 2, rewritten) | S12 | supported | retrying a 4xx wastes requests, apart from 408 and 429 where the server invites a retry | 0.9 |
| 104 | claim | 5xx: same request later often works | S12 | supported | A 5xx response places the fault in the server, so an identical request often succeeds on a later attempt. | 0.95 |
| 105 | claim | 500 generic | S6, S11 | supported | This error is generic, indicating that the server cannot find a more appropriate 5XX status code to respond with. | 0.95 |
| 106 | claim | 502 Bad Gateway | S6, S11 | supported | The server was acting as a gateway or proxy and received an invalid response from the upstream server | 0.95 |
| 107 | claim | 503 not ready, temporary, Retry-After | S6 | supported | This response should be used for temporary conditions and the Retry-After HTTP header should, if possible, contain the estimated time | 0.95 |
| 108 | claim | GET or POST can receive 5xx | S1, S11 | supported | These response codes are applicable to any request method | 0.9 |
| 109 | claim | 5xx does not mean client erred | S10, S12 | supported | 5XX server error. The server failed to fulfill an apparently valid request. | 0.95 |
| 110 | claim | GET can be retried later with pause | S1, S12 | supported | retrying a 5xx with backoff usually clears | 0.85 |
| 111 | claim | Blind POST retry can duplicate | S1, S13 | supported | A client that sends a request and gets no answer cannot tell what happened on the server. | 0.95 |
| 112 | claim | Who must change: 4xx you, 5xx server owner | S12 | supported | The split between 4xx and 5xx assigns responsibility. | 0.9 |
| 113 | claim | Unknown code falls back on class | S10, S12 | supported | A client meeting an unfamiliar code falls back to the class, so an unrecognized 4xx gets handled as a generic client error | 0.95 |
| 114 | claim | Recap of three exchanges | S6, S1 | supported | The server cannot find the requested resource. | 0.85 |
| 115 | claim | 404 fix URL; 503 wait and retry after checking duplicate | S6, S12, S1 | supported | 5xx. Server failed a valid request. Retry later or surface the failure. | 0.85 |
| 116 | claim | Drop slogans | S6, S9, S12 | supported | The split between 4xx and 5xx assigns responsibility. | 0.9 |
| 117 | claim | Video viewing notes describe S17 content | S17 | unverifiable |  | 0.9 |
| 118 | claim | Practice remediation pointers (pass 2, new) |  | unverifiable |  | 0.9 |
| 119 | quiz | Practice key header with full citations (pass 2, rewritten) | S1, S5, S7, S8, S12 | supported | 4xx. Problem in the request. Change the request before retrying. | 0.9 |
| 120 | quiz | Key A: GET read-only, safe, idempotent, cacheable (pass 2, new) | S1, S5, S7, S8, S12 | supported | The response to a GET request is cacheable; a cache MAY use it to satisfy subsequent GET and HEAD requests | 0.95 |
| 121 | quiz | Key B: signup is POST, creates state | S1, S5, S7, S8, S12 | supported | Creating a new resource that has yet to be identified by the origin server; and | 0.9 |
| 122 | quiz | Key C: shareable search is GET | S1, S5, S7, S8, S12 | supported | Providing a URI for a resource affords many advantages, including: linking. bookmarking. caching. | 0.9 |
| 123 | quiz | Key D: POST over HTTPS | S1, S5, S7, S8, S12 | supported | the data is encrypted along with the rest of the request | 0.85 |
| 124 | quiz | Key E: 404 is client error; fix URL | S1, S5, S7, S8, S12 | supported | Client error responses indicate the request contains a problem the server cannot process, such as malformed syntax, missing Authentication , or a non-existent resource. | 0.9 |
| 125 | quiz | Key F: 201 success | S1, S5, S7, S8, S12 | supported | Success responses indicate the request was received, understood, and accepted. | 0.9 |
| 126 | quiz | Key G: 503 retry later, beware duplicate | S1, S5, S7, S8, S12 | supported | A client SHOULD NOT automatically retry a request with a non-idempotent method unless it has some means to know that the request semantics are actually idempotent | 0.9 |
| 127 | quiz | Key H: 403 permissions | S1, S5, S7, S8, S12 | supported | a 403 is returned when a request contains valid credentials, but the client does not have permissions to perform a certain action | 0.85 |
| 128 | quiz | Key I: 502 retry later | S1, S5, S7, S8, S12 | supported | 5xx. Server failed a valid request. Retry later or surface the failure. | 0.9 |
| 129 | quiz | Quiz 1 answer (b) | S2 | supported | has three parts: <protocol> <status-code> <reason-phrase> | 0.95 |
| 130 | quiz | Quiz 2 answer (a) | S1, S5 | supported | Of the request methods defined by this specification, PUT , DELETE , and safe request methods are idempotent. | 0.95 |
| 131 | quiz | Quiz 3 answer (b): recipe filter is a read-only GET; query string makes it shareable (pass 2, new question) | S5, S8, S10 | supported | since the site designers created a POST Web form instead of a GET Web form for this read-only operation, Dan cannot bookmark the query | 0.95 |
| 132 | quiz | Quiz 4 answer (a) | S9, S12 | supported | The split between 4xx and 5xx assigns responsibility. | 0.95 |
| 133 | quiz | Quiz 4 option (c) is a wrong distractor: 5xx does not mean the request was faulty (pass 2, changed option) | S9, S12 | supported | 5xx. Server failed a valid request. Retry later or surface the failure. | 0.9 |
| 134 | quiz | Quiz 5 answer (b): POST /orders with malformed body gets 400; client must fix the body (pass 2, new question) | S6, S12 | supported | The server cannot or will not process the request due to something that is perceived to be a client error (e.g., malformed request syntax | 0.9 |
| 135 | quiz | Full answer key line (pass 2) | S1, S2, S5, S6, S8, S9, S10, S12 | supported | 4xx. Problem in the request. Change the request before retrying. | 0.9 |
| 136 | claim | Wrap-up: GET reads | S1, S5 | supported | Of the request methods defined by this specification, PUT , DELETE , and safe request methods are idempotent. | 0.95 |
| 137 | claim | Wrap-up: POST submits | S1, S5, S13 | supported | If the app sends the same POST request again, the customer may get two orders and two charges. | 0.95 |
| 138 | claim | Wrap-up: first digit tells who acts | S1, S12 | supported | 4xx. Problem in the request. Change the request before retrying. | 0.95 |
| 139 | claim | HTTPS protects data for both methods | S5, S8 | supported | To protect information carried by either GET or POST operations, it is often appropriate to use an underlying secure protocol such as the Secure Socket Layer | 0.9 |
| 140 | claim | Dev tools Network tab shows requests | S2, S5 | supported | You can see HTTP messages in a browser's Network tab in the developer tools | 0.95 |
| 141 | claim | The first request below sends a search term and a page number in the query string (rule: ). | S3, S5 | supported | <query> Optional. An optional query component preceded by a question-mark ? . Often used to carry identifying information in the form of key=value pairs. | 0.9 |
| 142 | quiz | Quiz question 1: Read this raw response. Which line holds the status code, and where does the body start? Stated answer: (b): the status line is the first line (version, code, reason phrase), and an empty line ends the headers, with the body after it | S2 | supported | has three parts: <protocol> <status-code> <reason-phrase> | 0.95 |
| 143 | quiz | Quiz question 2: Which statement is accurate? Stated answer: (a): GET data travels in the query string and GET is safe and idempotent, while POST is not guaranteed idempotent, so repeating it may repeat the effect | S1, S5 | supported | Of the request methods defined by this specification, PUT , DELETE , and safe request methods are idempotent. | 0.95 |
| 144 | quiz | Quiz question 3: A recipe site lets users filter recipes by ingredient, and users often send the filtered list to friends. Which method fits, and why? Stated answer: (b): filtering is a read-only lookup, so GET fits; the filter travels in the query string, and a URL that holds it can be bookmarked and shared | S5, S8, S10 | supported | since the site designers created a POST Web form instead of a GET Web form for this read-only operation, Dan cannot bookmark the query | 0.95 |
| 145 | quiz | Quiz question 4: A friend says: "Any response with a status code means success, 200 is the only success code, and 4xx and 5xx are the same kind of error." Which correction is right? Stated answer: (a): 2xx is success and includes more than 200, a leading 4 or 5 signals an error, and 4xx is the clien | S9, S12 | supported | The split between 4xx and 5xx assigns responsibility. | 0.95 |
| 146 | quiz | Quiz question 5: A POST /orders with the body {"items":} returns 400 Bad Request. Which class is it, who must act, and what is the right next step? Stated answer: (b): 400 is a 4xx client error, here caused by malformed syntax in the body, so the client must change the request before retrying | S6, S12 | supported | A 4xx response places the fault in the request, so repeating the same request produces the same answer. | 0.9 |
