#!/usr/bin/env python3
"""AI Ghar WhatsApp Bot — customer auto-replies (Buy/Rent/List/Wanted).

Run:  pip install -r requirements.txt && python3 bot.py
Leads: http://localhost:5000/leads
"""
from flask import Flask, request
import requests
import json
import os
from datetime import datetime

import config

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
LEADS_FILE = os.path.join(BASE, "leads.json")
LISTINGS_FILE = os.path.join(BASE, "listings.json")

sessions = {}  # phone -> {"state": str, "data": dict}


# ---------------- helpers ----------------
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_lead(lead):
    leads = load_json(LEADS_FILE, [])
    lead["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    leads.append(lead)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def send_message(to, text):
    """WhatsApp Cloud API se message bhejein. Token placeholder ho to dry-run."""
    if "PASTE" in config.WHATSAPP_TOKEN:
        print(f"[DRY-RUN -> {to}] {text[:120]}", flush=True)
        return True
    url = f"https://graph.facebook.com/v21.0/{config.PHONE_NUMBER_ID}/messages"
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"},
            json={"messaging_product": "whatsapp", "to": to,
                  "type": "text", "text": {"body": text}},
            timeout=20,
        )
        if not r.ok:
            print("WhatsApp API error:", r.status_code, r.text[:200], flush=True)
        return r.ok
    except Exception as e:
        print("send error:", e, flush=True)
        return False


def get_session(phone):
    return sessions.setdefault(phone, {"state": "MENU", "data": {}})


MENU = (
    "Assalam-o-Alaikum! \U0001f3e0 *AI Ghar* me khush aamdeed!\n\n"
    "Kya karna chahte hain? Number bhejein:\n"
    "1\ufe0f\u20e3 Ghar Kharidna (Buy)\n"
    "2\ufe0f\u20e3 Ghar Kiraye par lena (Rent)\n"
    "3\ufe0f\u20e3 Apni property list karna\n"
    "4\ufe0f\u20e3 Wanted \u2014 apni requirement batayein\n\n"
    "(Kisi bhi waqt MENU likh kar wapas aa sakte hain)"
)


def fmt_listings(kind):
    data = load_json(LISTINGS_FILE, {})
    items = data.get(kind, [])
    lines = ["\U0001f3d8\ufe0f *%s ke liye listings:*\n" % kind.upper()]
    for i, l in enumerate(items, 1):
        lines.append("%d. %s\n   \U0001f4cd %s | \U0001f4b0 %s" % (i, l["title"], l["area"], l["price"]))
    lines.append("\nPasand aye to uska *number* bhejein.")
    return "\n".join(lines)


def listing_detail(kind, idx):
    items = load_json(LISTINGS_FILE, {}).get(kind, [])
    if 0 <= idx < len(items):
        l = items[idx]
        return ("\u2b50 *%s*\n\U0001f4cd Area: %s\n\U0001f4b0 Price: %s\n\n"
                "Site visit book karna chahte hain? *HAAN* likhein." % (l["title"], l["area"], l["price"]))
    return None


# ---------------- conversation state machine ----------------
def handle_text(phone, text):
    s = get_session(phone)
    t = text.strip()
    tl = t.lower()

    # global: wapas menu
    if tl in ("menu", "start", "salam", "assalam", "assalam-o-alaikum",
               "assalam o alaikum", "aoa", "hi", "hello", "salaam"):
        s["state"] = "MENU"
        s["data"] = {}
        return MENU

    state, d = s["state"], s["data"]

    if state == "MENU":
        if t == "1":
            s["state"] = "BUY_PICK"
            return fmt_listings("buy")
        if t == "2":
            s["state"] = "RENT_PICK"
            return fmt_listings("rent")
        if t == "3":
            s["state"] = "LIST_TYPE"
            return ("Apni property list karna chahte hain. Pehle ye batayein:\n"
                      "1\ufe0f\u20e3 Bechni hai (SELL)\n"
                      "2\ufe0f\u20e3 Kiraye par deni hai (RENT)")
        if t == "4":
            s["state"] = "WANTED_BUDGET"
            return "Apna *budget* batayein (misal: 1 crore tak, ya 40 hazar/month):"
        return "Samajh nahi aya. " + MENU

    # ---- buy / rent ----
    if state in ("BUY_PICK", "RENT_PICK"):
        kind = "buy" if state == "BUY_PICK" else "rent"
        if t.isdigit():
            detail = listing_detail(kind, int(t) - 1)
            if detail:
                d["kind"], d["pick"] = kind, int(t) - 1
                s["state"] = "VISIT_CONFIRM"
                return detail
        return "Sahi number bhejein (listings me se)."

    if state == "VISIT_CONFIRM":
        if tl in ("haan", "han", "yes", "ji", "yes please"):
            s["state"] = "VISIT_NAME"
            return "Zabardast! Site visit ke liye apna *naam* bhejein:"
        s["state"] = "MENU"
        s["data"] = {}
        return "Koi baat nahi. " + MENU

    if state == "VISIT_NAME":
        d["name"] = t
        s["state"] = "VISIT_DATE"
        return "Shukriya %s! Visit ki *tareekh* batayein (misal: kal shaam, ya 10-Oct):" % t

    if state == "VISIT_DATE":
        items = load_json(LISTINGS_FILE, {}).get(d.get("kind", "buy"), [])
        prop = items[d.get("pick", 0)]["title"] if items else "-"
        save_lead({"type": "site_visit", "phone": phone, "name": d.get("name"),
                   "date": t, "property": prop, "kind": d.get("kind")})
        s["state"] = "MENU"
        s["data"] = {}
        return ("\u2705 *Site visit booked!*\n\n"
                "Property: %s\nNaam: %s\nTareekh: %s\n\n"
                "Hamari team jald rabta karegi. Shukriya! \U0001f3e0" % (prop, d.get("name"), t))

    # ---- list property ----
    if state == "LIST_TYPE":
        if t == "1":
            d["ptype"] = "SELL"
        elif t == "2":
            d["ptype"] = "RENT"
        else:
            return "1 (SELL) ya 2 (RENT) bhejein."
        s["state"] = "LIST_LOCATION"
        return "Property ki *location/area* batayein (misal: Gulgasht Colony):"

    if state == "LIST_LOCATION":
        d["location"] = t
        s["state"] = "LIST_PRICE"
        return " *Qeemat* kya hai? (misal: 1.4 crore, ya 45 hazar/month):"

    if state == "LIST_PRICE":
        d["price"] = t
        s["state"] = "LIST_AREA"
        return "Property ka *size*? (misal: 5 marla, 10 marla, 1 kanal):"

    if state == "LIST_AREA":
        d["area"] = t
        s["state"] = "LIST_NAME"
        return "Apna *naam* bhejein:"

    if state == "LIST_NAME":
        d["name"] = t
        s["state"] = "LIST_PHONE"
        return "Apna *mobile number* bhejein:"

    if state == "LIST_PHONE":
        save_lead({"type": "list_property", "phone": phone, "ptype": d.get("ptype"),
                   "location": d.get("location"), "price": d.get("price"),
                   "area": d.get("area"), "name": d.get("name"),
                   "contact": t})
        s["state"] = "MENU"
        s["data"] = {}
        return ("\u2705 *Request save ho gayi!*\n\n"
                "24 ghante me verify karke aapki property *FREE publish* kar di jayegi. Shukriya! \U0001f3e0")

    # ---- wanted ----
    if state == "WANTED_BUDGET":
        d["budget"] = t
        s["state"] = "WANTED_TYPE"
        return "Kis qisam ki property chahiye? (misal: ghar, plot, apartment, portion):"

    if state == "WANTED_TYPE":
        d["ptype"] = t
        s["state"] = "WANTED_AREA"
        return "Kis *area* me chahiye? (misal: Gulgasht, Bosan Road):"

    if state == "WANTED_AREA":
        d["area"] = t
        s["state"] = "WANTED_NAME"
        return "Apna *naam* bhejein:"

    if state == "WANTED_NAME":
        d["name"] = t
        s["state"] = "WANTED_PHONE"
        return "Apna *mobile number* bhejein:"

    if state == "WANTED_PHONE":
        save_lead({"type": "wanted", "phone": phone, "budget": d.get("budget"),
                   "ptype": d.get("ptype"), "area": d.get("area"),
                   "name": d.get("name"), "contact": t})
        s["state"] = "MENU"
        s["data"] = {}
        return ("\u2705 *Requirement save ho gayi!*\n\n"
                "Budget: %s\nType: %s\nArea: %s\n\n"
                "Matching property milte hi rabta karein ge. Shukriya! \U0001f3e0"
                % (d.get("budget"), d.get("ptype"), d.get("area")))

    s["state"] = "MENU"
    s["data"] = {}
    return MENU


# ---------------- webhook ----------------
@app.route("/webhook", methods=["GET"])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == config.VERIFY_TOKEN:
        return challenge or "", 200
    return "verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook_receive():
    data = request.get_json(silent=True) or {}
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    if msg.get("type") != "text":
                        continue
                    phone = msg.get("from", "")
                    body = msg.get("text", {}).get("body", "")
                    if phone and body:
                        reply = handle_text(phone, body)
                        send_message(phone, reply)
    except Exception as e:
        print("webhook error:", e, flush=True)
    return "OK", 200


# ---------------- leads page ----------------
LEADS_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>AI Ghar — Leads</title>
<style>body{font-family:sans-serif;max-width:900px;margin:20px auto;padding:0 12px}
h1{color:#166534}table{width:100%;border-collapse:collapse;margin:16px 0}
th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:14px}
th{background:#f0fdf4}h2{margin-top:28px;color:#15803d}.tag{display:inline-block;
background:#dcfce7;padding:2px 8px;border-radius:10px;font-size:12px}</style>
</head><body><h1>\U0001f3e0 AI Ghar — Leads</h1>__BODY__</body></html>"""

TYPE_TITLES = {"site_visit": "\U0001f4c5 Site Visit Bookings",
               "list_property": "\U0001f4dd List Property Requests",
               "wanted": "\U0001f4cb Wanted Requirements"}


@app.route("/leads")
def leads_page():
    leads = load_json(LEADS_FILE, [])
    if not leads:
        body = "<p>Abhi koi lead nahi hai.</p>"
    else:
        parts = []
        for tkey, title in TYPE_TITLES.items():
            rows = [l for l in leads if l.get("type") == tkey]
            if not rows:
                continue
            cols = [k for k in rows[0].keys() if k != "type"]
            parts.append("<h2>%s <span class='tag'>%d</span></h2>" % (title, len(rows)))
            parts.append("<table><tr>" + "".join("<th>%s</th>" % c for c in cols) + "</tr>")
            for r in rows:
                parts.append("<tr>" + "".join("<td>%s</td>" % (r.get(c, "")) for c in cols) + "</tr>")
            parts.append("</table>")
        body = "\n".join(parts)
    return LEADS_HTML.replace("__BODY__", body)


@app.route("/")
def index():
    return "AI Ghar WhatsApp Bot chal raha hai \u2705 — <a href='/leads'>leads dekhein</a>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT)
