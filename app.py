# -*- coding: utf-8 -*-
"""
PMML Social Media Portal — Phase 1
- Dashboard: connected accounts status
- Composer: publish / schedule posts to the Facebook Page
- FAQ editor: bot auto-reply answers (data/faqs.json)
- Inbox: log of incoming Messenger + WhatsApp messages with bot replies
- Webhook: Meta calls this for incoming messages (no login required)
"""
import json
import os
from datetime import datetime
from functools import wraps

import requests
from flask import (
    Flask, jsonify, redirect, render_template, request, session, url_for,
)

from bot_engine import find_reply, load_faqs, save_faqs
from publishers import get_page_info, publish_facebook_post

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "please-change-me-urgent")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
INBOX_LOG = os.path.join(DATA, "inbox.jsonl")

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "")
GRAPH_VERSION = "v21.0"
MAX_INBOX = 200


# ---------------- auth ----------------
def login_required(f):
    @wraps(f)
    def decorated(*a, **k):
        if not session.get("authed"):
            return redirect(url_for("login"))
        return f(*a, **k)
    return decorated


@app.get("/login")
def login():
    if session.get("authed"):
        return redirect(url_for("dashboard"))
    return render_template("login.html", error=None)


@app.post("/login")
def login_post():
    if not PORTAL_PASSWORD:
        return render_template("login.html",
                               error="PORTAL_PASSWORD سرور پر سیٹ نہیں ہے")
    if request.form.get("password", "") == PORTAL_PASSWORD:
        session["authed"] = True
        return redirect(url_for("dashboard"))
    return render_template("login.html", error="غلط پاس ورڈ")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- dashboard ----------------
@app.get("/")
def index():
    return redirect(url_for("dashboard"))


@app.get("/dashboard")
@login_required
def dashboard():
    page = get_page_info()
    faqs = load_faqs()
    inbox_count = count_inbox()
    wa_ok = bool(WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID)
    return render_template(
        "dashboard.html",
        page=page,
        faq_count=len(faqs.get("faqs", [])),
        inbox_count=inbox_count,
        wa_ok=wa_ok,
        page_token_set=bool(PAGE_ACCESS_TOKEN),
    )


# ---------------- composer ----------------
@app.get("/composer")
@login_required
def composer():
    page = get_page_info()
    return render_template("composer.html", page=page, result=None, ok=None)


@app.post("/composer")
@login_required
def composer_post():
    page = get_page_info()
    text = request.form.get("text", "")
    mode = request.form.get("mode", "now")
    scheduled_unix = None
    if mode == "schedule":
        when = request.form.get("when", "")
        try:
            dt = datetime.strptime(when, "%Y-%m-%dT%H:%M")
            scheduled_unix = int(dt.timestamp())
        except ValueError:
            return render_template("composer.html", page=page,
                                   result="تاریخ/وقت درست نہیں", ok=False)
    ok, result = publish_facebook_post(text, scheduled_unix)
    return render_template("composer.html", page=page, result=result, ok=ok)


# ---------------- FAQ editor ----------------
@app.get("/faqs")
@login_required
def faqs():
    data = load_faqs()
    return render_template("faqs.html", faqs=data.get("faqs", []),
                           default_reply=data.get("default_reply", ""))


@app.get("/faqs/edit/<int:idx>")
@login_required
def faq_edit(idx):
    data = load_faqs()
    items = data.get("faqs", [])
    if idx < 0 or idx >= len(items):
        return redirect(url_for("faqs"))
    return render_template("faq_edit.html", idx=idx, item=items[idx])


@app.post("/faqs/edit/<int:idx>")
@login_required
def faq_edit_post(idx):
    data = load_faqs()
    items = data.get("faqs", [])
    if idx < 0 or idx >= len(items):
        return redirect(url_for("faqs"))
    keywords = [k.strip() for k in request.form.get("keywords", "").split(",")
                if k.strip()]
    answer = request.form.get("answer", "").strip()
    if keywords and answer:
        items[idx] = {"keywords": keywords, "answer": answer}
        save_faqs(data)
    return redirect(url_for("faqs"))


@app.post("/faqs/default")
@login_required
def faq_default_post():
    data = load_faqs()
    answer = request.form.get("answer", "").strip()
    if answer:
        data["default_reply"] = answer
        save_faqs(data)
    return redirect(url_for("faqs"))


# ---------------- inbox log ----------------
def count_inbox():
    if not os.path.exists(INBOX_LOG):
        return 0
    with open(INBOX_LOG, encoding="utf-8") as f:
        return sum(1 for _ in f)


def read_inbox(limit=50):
    rows = []
    if os.path.exists(INBOX_LOG):
        with open(INBOX_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass
    return rows[-limit:][::-1]


def log_inbox(platform, sender, text, reply):
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "platform": platform,
        "sender": sender,
        "text": text,
        "reply": reply,
    }
    rows = []
    if os.path.exists(INBOX_LOG):
        with open(INBOX_LOG, encoding="utf-8") as f:
            rows = [l for l in f if l.strip()]
    rows.append(json.dumps(entry, ensure_ascii=False) + "\n")
    rows = rows[-MAX_INBOX:]
    with open(INBOX_LOG, "w", encoding="utf-8") as f:
        f.writelines(rows)


@app.get("/inbox")
@login_required
def inbox():
    return render_template("inbox.html", rows=read_inbox())


# ---------------- webhook (Meta calls this; no login) ----------------
def send_messenger_reply(recipient_id, text):
    if not PAGE_ACCESS_TOKEN:
        return
    requests.post(
        f"https://graph.facebook.com/{GRAPH_VERSION}/me/messages",
        params={"access_token": PAGE_ACCESS_TOKEN},
        json={"recipient": {"id": recipient_id},
              "messaging_type": "RESPONSE",
              "message": {"text": text}},
        timeout=15,
    )


def send_whatsapp_reply(to, text):
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID):
        return
    requests.post(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages",
        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
        json={"messaging_product": "whatsapp", "to": to,
              "type": "text", "text": {"body": text}},
        timeout=15,
    )


@app.get("/webhook")
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token and token == VERIFY_TOKEN:
        return challenge, 200
    return "verification failed", 403


@app.post("/webhook")
def webhook_receive():
    data = request.get_json(force=True, silent=True) or {}
    obj = data.get("object")
    if obj == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender = (event.get("sender") or {}).get("id")
                message = event.get("message") or {}
                text = message.get("text")
                if sender and text and not message.get("is_echo"):
                    reply = find_reply(text)
                    log_inbox("facebook", sender, text, reply)
                    try:
                        send_messenger_reply(sender, reply)
                    except Exception:
                        pass
    elif obj == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value") or {}
                for msg in value.get("messages", []):
                    if msg.get("type") == "text":
                        sender = msg.get("from")
                        text = (msg.get("text") or {}).get("body")
                        if sender and text:
                            reply = find_reply(text)
                            log_inbox("whatsapp", sender, text, reply)
                            try:
                                send_whatsapp_reply(sender, reply)
                            except Exception:
                                pass
    return jsonify({"status": "ok"}), 200


@app.get("/health")
def health():
    return "portal running", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
