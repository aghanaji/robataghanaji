import os
import requests
from flask import Flask, request, jsonify
from urllib.parse import quote_plus

TOKEN = os.environ.get("BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text):
    try:
        requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)
    except Exception as e:
        print("send_message error:", e)

def send_photo_by_url(chat_id, url, caption=""):
    try:
        requests.post(f"{API_URL}/sendPhoto", json={"chat_id": chat_id, "photo": url, "caption": caption}, timeout=30)
    except Exception as e:
        print("send_photo_by_url error:", e)

def send_video_by_url(chat_id, url, caption=""):
    try:
        requests.post(f"{API_URL}/sendVideo", json={"chat_id": chat_id, "video": url, "caption": caption}, timeout=30)
    except Exception as e:
        print("send_video_by_url error:", e)

PROXIES = [
    "https://igram.world/api/instagram.php?url=",
    "https://instadownloader.co/instagram/api?url=",
    "https://api.snapinsta.app/v2/?url=",
    "https://api.vxtiktok.com/instagram?url=",
]

def find_media_url(insta_url):
    debug = []
    for base in PROXIES:
        try:
            api = base + quote_plus(insta_url)
            r = requests.get(api, headers={"User-Agent":"Mozilla/5.0"}, timeout=12)
            status = r.status_code
            txt = r.text[:1200]
            debug.append(f"{base} status={status} body_snippet={txt.replace(chr(10),' ')[:300]}")
            try:
                j = r.json()
                if isinstance(j, dict):
                    for key in ("url","download","download_url","video","video_url","media","links"):
                        if key in j:
                            val = j[key]
                            if isinstance(val, str) and val.startswith("http"):
                                return val, debug
                            if isinstance(val, list) and len(val)>0:
                                first = val[0]
                                if isinstance(first, dict):
                                    for subk in ("download_url","url","video","video_url"):
                                        if subk in first and isinstance(first[subk], str):
                                            return first[subk], debug
                                elif isinstance(first, str) and first.startswith("http"):
                                    return first, debug
            except:
                pass

            import re
            m = re.search(r'https?://[^"\'>\s]+?\.(?:mp4|jpg|jpeg|png)(\?[^"\'>\s]*)?', r.text, re.IGNORECASE)
            if m:
                return m.group(0), debug

        except Exception as e:
            debug.append(f"{base} ERROR {str(e)[:200]}")
            continue
    return None, debug

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
    except:
        return "OK", 200

    if not data or "message" not in data:
        return "OK", 200

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "") or ""

    if "instagram.com" not in text:
        send_message(chat_id, "لینک اینستاگرام بفرست تا دانلود کنم.")
        return "OK", 200

    send_message(chat_id, "⏳ در حال پیدا کردن لینک مستقیم...")

    media_url, debug = find_media_url(text)

    debug_msg = "\n\n".join(debug[:4])

    if not media_url:
        send_message(chat_id, "❌ نتونستم فایل رو پیدا کنم:\n" + debug_msg[:900])
        return "OK", 200

    send_message(chat_id, "✅ لینک مستقیم پیدا شد. در حال ارسال...")

    lower = media_url.split("?")[0].lower()

    try:
        if lower.endswith((".mp4",".mov",".webm",".mkv")):
            send_video_by_url(chat_id, media_url)
        elif lower.endswith((".jpg",".jpeg",".png",".gif",".webp")):
            send_photo_by_url(chat_id, media_url)
        else:
            send_message(chat_id, media_url)
    except Exception as e:
        send_message(chat_id, "خطای تلگرام: " + str(e)[:200])

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
