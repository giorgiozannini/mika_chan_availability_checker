from playwright.sync_api import sync_playwright
import json
import os
import time

URL = "https://www.mikachan.it/"
STATE_FILE = "last_availability.json"


def send_telegram(message):
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")

    import requests
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    )


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"available": False}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


for attempt in range(3):
    print(f"Attempt {attempt+1}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(URL, timeout=60000)
            page.wait_for_timeout(5000)  # wait for JS to load

            content = page.content()
            
            unavailable_phrase = "Al momento le prenotazioni risultano al completo."
            
            # If the phrase is NOT present, bookings are available
            is_available = unavailable_phrase not in content

            state = load_state()

            if is_available and not state["available"]:
                print("🚨 NEW AVAILABILITY FOUND")

                message = f"""
<b>Disponibilità trovata su Mikachan!</b>

<a href="{URL}">Vai al sito</a>
"""
                send_telegram(message)

            save_state({"available": is_available})

            browser.close()

    except Exception as e:
        print("Error:", e)
        time.sleep(5)
        continue
    else:
        break
