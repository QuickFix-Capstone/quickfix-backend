import base64
import json
import urllib.parse
import urllib.request

class HttpError(Exception):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body

def _read_resp(resp):
    data = resp.read()
    try:
        txt = data.decode("utf-8")
    except Exception:
        txt = str(data)
    return txt

def post_json(url, payload, headers=None, timeout=20):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k,v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            txt = _read_resp(resp)
            if resp.status >= 400:
                raise HttpError(resp.status, txt)
            return json.loads(txt)
    except urllib.error.HTTPError as e:
        txt = _read_resp(e)
        raise HttpError(e.code, txt)

def post_form(url, form_dict, headers=None, timeout=20):
    data = urllib.parse.urlencode(form_dict).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    if headers:
        for k,v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            txt = _read_resp(resp)
            if resp.status >= 400:
                raise HttpError(resp.status, txt)
            return json.loads(txt)
    except urllib.error.HTTPError as e:
        txt = _read_resp(e)
        raise HttpError(e.code, txt)

def basic_auth_header(user, password):
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"

def bearer(token):
    return f"Bearer {token}"


def get_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, method="GET")
    if headers:
        for k,v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            txt = _read_resp(resp)
            if resp.status >= 400:
                raise HttpError(resp.status, txt)
            return json.loads(txt)
    except urllib.error.HTTPError as e:
        txt = _read_resp(e)
        raise HttpError(e.code, txt)
