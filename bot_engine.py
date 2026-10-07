# -*- coding: utf-8 -*-
"""Bot reply engine — reads FAQs from data/faqs.json (editable via portal UI)."""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FAQ_FILE = os.path.join(BASE, "data", "faqs.json")


def load_faqs():
    with open(FAQ_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_faqs(data):
    tmp = FAQ_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FAQ_FILE)


def find_reply(text, data=None):
    data = data if data is not None else load_faqs()
    t = (text or "").strip().lower()
    for item in data.get("faqs", []):
        if any(kw.lower() in t for kw in item.get("keywords", [])):
            return item["answer"]
    return data.get("default_reply", "")
