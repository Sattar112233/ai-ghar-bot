"""AI Ghar WhatsApp Bot — configuration.

Values ko environment variables se dein (Render/Railway par), ya yahan
direct paste kar dein. Kisi ko ye file mat bhejein — token secret hai.
"""
import os

# Meta developers.facebook.com → App → WhatsApp → API Setup se milega
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "PASTE_YOUR_TOKEN_HERE")

# WhatsApp → API Setup me "Phone number ID"
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "PASTE_YOUR_PHONE_NUMBER_ID")

# Apni marzi ka — webhook verify ke waqt Meta dashboard me yehi dalna hai
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "ai-ghar-123")

PORT = int(os.environ.get("PORT", "5000"))
