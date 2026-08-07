#!/usr/bin/env python3
import html as html_lib
import os, re, sys, time
import urllib.error, urllib.parse, urllib.request

URL = "https://www.mikachan.it/"
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


def telegram(msg):
    token, chat_id = os.environ.get("TOKEN", ""), os.environ.get("CHAT_ID", "")
    if not token or not chat_id:
        print("TOKEN or CHAT_ID is missing/empty", file=sys.stderr)
        return False
    data = urllib.parse.urlencode({
        "chat_id": chat_id, "text": msg, "parse_mode": "HTML",
    }).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
            print("telegram ok:", r.read().decode()[:300])
            return True
    except urllib.error.HTTPError as e:
        print(f"telegram HTTP {e.code}: {e.read().decode()[:300]}", file=sys.stderr)
    except Exception as e:
        print(f"telegram failed: {e}", file=sys.stderr)
    return False


def main():
    for attempt in range(3):
        try:
            text = visible_text(fetch(URL))
            break
        except Exception as e:
            print(f"attempt {attempt + 1} failed: {e}", file=sys.stderr)
            time.sleep(5)
    else:
        telegram("⚠️ Check Mikachan fallito: sito irraggiungibile")
        return 1

    if SANITY_MARKER not in text:
        telegram("⚠️ Check Mikachan fallito: pagina inattesa")
        return 1

    if FULL_PHRASE in text:
        print("available=False")
        telegram("Not available yet :'(")
    else:
        print("available=True")
        telegram(f'<b>Disponibilità trovata su Mikachan!</b>\n<a href="{URL}">Vai al sito</a>')
    return 0


if __name__ == "__main__":
    sys.exit(main())
