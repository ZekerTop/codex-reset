import json
import os
import uuid

from curl_cffi import requests as cf_requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BACKEND_API = "https://chatgpt.com/backend-api"
PROXIES = {"https": "http://127.0.0.1:10808", "http": "http://127.0.0.1:10808"}


@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def build_headers(token, account_id):
    return {
        "Authorization": f"Bearer {token}",
        "ChatGPT-Account-Id": account_id,
        "OAI-Language": "zh-CN",
        "originator": "Codex Desktop",
        "Content-Type": "application/json",
    }


def clean_json(raw):
    raw = raw.lstrip("\ufeff\u200b\u200c\u200d").strip()
    if raw and raw[0] != "{":
        i = raw.find("{")
        if i >= 0:
            raw = raw[i:]
    return raw


def parse_session(s):
    data = json.loads(clean_json(s))
    token = data.get("accessToken")
    if not token:
        raise ValueError("缺少 accessToken")
    aid = (data.get("account") or {}).get("id") or (data.get("user") or {}).get("id")
    if not aid:
        raise ValueError("缺少 account.id 或 user.id")
    return token, aid


def cg(method, path, token, account_id, **kw):
    """chatgpt.com API 请求封装"""
    url = f"{BACKEND_API}{path}"
    h = build_headers(token, account_id)
    fn = cf_requests.get if method == "GET" else cf_requests.post
    return fn(url, headers=h, impersonate="chrome", proxies=PROXIES, timeout=20, **kw)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/check-session", methods=["POST"])
def check_session():
    body = request.get_json(silent=True)
    if not body or not body.get("session_json", "").strip():
        return jsonify({"error": "请粘贴 session JSON"}), 400
    try:
        token, aid = parse_session(body["session_json"])
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    result = {}

    # eligibility
    try:
        r = cg("GET", "/referrals/invite/eligibility", token, aid,
               params={"referral_key": "codex_referral_persistent_invite"})
        if r.status_code == 401:
            return jsonify({"error": "Token 已过期"}), 401
        try:
            result["eligibility"] = r.json()
        except Exception:
            result["eligibility"] = {"status_code": r.status_code, "raw": r.text[:300]}
    except Exception as e:
        return jsonify({"error": f"查询资格失败: {e}"}), 502

    # credits
    try:
        r = cg("GET", "/wham/rate-limit-reset-credits", token, aid)
        result["credits"] = r.json() if r.status_code < 400 else None
    except Exception:
        result["credits"] = None

    # usage
    try:
        r = cg("GET", "/wham/usage", token, aid)
        result["usage"] = r.json() if r.status_code < 400 else None
    except Exception:
        result["usage"] = None

    result["access_token"] = token
    result["account_id"] = aid
    return jsonify(result)


@app.route("/api/send-invite", methods=["POST"])
def send_invite():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "无效请求"}), 400
    token = body.get("access_token")
    aid = body.get("account_id")
    emails = body.get("emails", [])
    if not token or not aid:
        return jsonify({"error": "缺少凭据"}), 400
    if not emails:
        return jsonify({"error": "请输入至少一个邮箱"}), 400

    try:
        r = cg("POST", "/wham/referrals/invite", token, aid,
               json={"referral_key": "codex_referral_persistent_invite", "emails": emails})
        if r.status_code == 401:
            return jsonify({"error": "Token 已过期"}), 401
        if r.status_code >= 400:
            return jsonify({"error": f"发送失败 ({r.status_code}): {r.text[:300]}"}), r.status_code
        return jsonify({"result": r.json()})
    except Exception as e:
        return jsonify({"error": f"发送失败: {e}"}), 502


@app.route("/api/consume-credit", methods=["POST"])
def consume_credit():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "无效请求"}), 400
    token = body.get("access_token")
    aid = body.get("account_id")
    cid = body.get("credit_id")
    if not all([token, aid, cid]):
        return jsonify({"error": "缺少参数"}), 400

    rid = str(uuid.uuid4())
    try:
        r = cg("POST", "/wham/rate-limit-reset-credits/consume", token, aid,
               json={"credit_id": cid, "redeem_request_id": rid})
        if r.status_code == 401:
            return jsonify({"error": "Token 已过期"}), 401
        if r.status_code >= 400:
            return jsonify({"error": f"重置失败 ({r.status_code}): {r.text[:300]}"}), r.status_code
        return jsonify({"result": r.json(), "redeem_request_id": rid})
    except Exception as e:
        return jsonify({"error": f"重置失败: {e}"}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
