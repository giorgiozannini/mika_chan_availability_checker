import html as html_lib
import json, os, re, sys, time
import urllib.parse, urllib.request

URL = "https://www.mikachan.it/"
STATE_FILE = "last_availability.json"
FULL_PHRASE = "prenotazioni risultano al completo"   # present => fully booked
SANITY_MARKER = "mikachan"                           # page really loaded?
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "it-IT,it;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, "replace")


def visible_text(raw):
    raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    text = html_lib.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).lower()


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def telegram(msg):
    data = urllib.parse.urlencode({
        "chat_id": os.environ["CHAT_ID"], "text": msg, "parse_mode": "HTML",
    }).encode()
    url = f"https://api.telegram.org/bot{os.environ['TOKEN']}/sendMessage"
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
        r.read()


def main():
    for attempt in range(3):
        try:
            text = visible_text(fetch(URL))
            break
        except Exception as e:
            print(f"attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(5)
    else:
        return 1

    if SANITY_MARKER not in text:
        print("page doesn't look like mikachan.it, not alerting", file=sys.stderr)
        return 1

    available = FULL_PHRASE not in text
    prev = load_state().get("available", False)
    print(f"available={available} previous={prev}")

    if available and not prev:
        telegram(f'<b>Disponibilità trovata su Mikachan!</b>\n<a href="{URL}">Vai al sito</a>')

    with open(STATE_FILE, "w") as f:
        json.dump({"available": available,
                   "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
