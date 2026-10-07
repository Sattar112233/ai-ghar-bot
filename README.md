# AI Ghar — WhatsApp Bot

Customer messages ka khud jawab dene wala bot (Buy/Rent/List/Wanted), leads `/leads` page par.

## Files
- `bot.py` — poora bot (Flask): webhook verify + receive, conversation flow, leads page
- `config.py` — tokens (env vars se ya direct paste)
- `requirements.txt` — `flask`, `requests`
- `listings.json` — Buy/Rent sample listings (apni asal listings se badal dein)
- `leads.json` — khud ban jayegi jab pehli lead aayegi

## Local test
```bash
pip install -r requirements.txt
python3 bot.py
# http://localhost:5000/leads
```

## Live karne ke steps (user ke zimme)
1. **Meta App:** developers.facebook.com → naya App → WhatsApp product add karein →
   `WHATSAPP_TOKEN` aur `PHONE_NUMBER_ID` nikaal kar `config.py` me (ya env vars me) paste karein.
   `VERIFY_TOKEN` default `ai-ghar-123` hai.
2. **Deploy (FREE):** Render.com / Railway.app → New Web Service → ye folder upload karein.
   Start command: `python3 bot.py` | Build: `pip install -r requirements.txt`
3. **Webhook:** Meta dashboard → WhatsApp → Configuration →
   Callback URL: `https://AAPKA-LINK/webhook`, Verify token: `ai-ghar-123`, Subscribe: `messages`

## Zaroori note
- WhatsApp Cloud API wala number **regular WhatsApp par nahi chal sakta** — agar
  +92 300 2254063 pehle se WhatsApp par hai to ya to use Cloud API par migrate
  karna hoga ya bot ke liye alag number lena hoga.
- Pehle 1000 conversations/month FREE hain.
