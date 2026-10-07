# -*- coding: utf-8 -*-
"""Publishers — post to social platforms via their official APIs."""
import os

import requests

GRAPH_VERSION = "v21.0"


def _page_identity(token):
    r = requests.get(
        f"https://graph.facebook.com/{GRAPH_VERSION}/me",
        params={"fields": "id,name", "access_token": token},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def get_page_info():
    """Return {'id','name'} for the connected Facebook Page, or None."""
    token = os.environ.get("PAGE_ACCESS_TOKEN", "")
    if not token:
        return None
    try:
        return _page_identity(token)
    except Exception:
        return None


def publish_facebook_post(text, scheduled_unix=None):
    """Publish now, or schedule (unix timestamp, 10 min – 75 days ahead).

    Returns (ok: bool, message: str)."""
    token = os.environ.get("PAGE_ACCESS_TOKEN", "")
    if not token:
        return False, "PAGE_ACCESS_TOKEN سیٹ نہیں ہے"
    text = (text or "").strip()
    if not text:
        return False, "پوسٹ کا متن خالی ہے"
    try:
        page_id = _page_identity(token)["id"]
        payload = {"message": text, "access_token": token}
        if scheduled_unix:
            payload["published"] = "false"
            payload["scheduled_publish_time"] = str(int(scheduled_unix))
        r = requests.post(
            f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}/feed",
            data=payload,
            timeout=20,
        )
        j = r.json()
        if "id" in j:
            what = "پوسٹ شیڈول ہو گئی" if scheduled_unix else "پوسٹ شائع ہو گئی"
            return True, f"{what} — ID: {j['id']}"
        err = j.get("error", {}).get("message", "نامعلوم خرابی")
        return False, f"فیس بک نے مسترد کر دیا: {err}"
    except Exception as e:
        return False, f"رابطے میں خرابی: {e}"
