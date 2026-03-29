import datetime as dt
import os

import requests
from google import genai
from twilio.rest import Client

# ==========================================
# 1. CONFIGURATION & CREDENTIALS
# ==========================================
LOCATION = "Lincoln NE"
OWM_Endpoint = "https://api.openweathermap.org/data/2.5/forecast"

OWM_KEY = os.getenv("OWM_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
Account_SID = os.getenv("ACCOUNT_SID")
Auth_Token = os.getenv("AUTH_TOKEN")


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def log(message):
    """Helper function to print formatted log messages."""
    current_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {message}")


# ==========================================
# 3. MAIN SCRIPT EXECUTION
# ==========================================
now = dt.datetime.now()
log("🚀 Starting daily weather script...")

# --- Step A: Fetch Weather Data ---
log(f"☁️ Fetching weather data for {LOCATION}...")
parameters = {
    "lat": 40.8137,
    "lon": -96.7026,
    "appid": OWM_KEY,
    "cnt": 4,
}

api_response = requests.get(OWM_Endpoint, params=parameters)
api_response.raise_for_status()
api_response = api_response.json()
log("✅ Weather data fetched successfully.")

simplified_weather = []
for interval in api_response["list"]:
    condition = interval["weather"][0]["main"]
    weather_id = interval["weather"][0]["id"]
    simplified_weather.append({"condition": condition, "id": weather_id})

# --- Step B: Generate Prompt ---
log("🤖 Sending prompt to Gemini 2.5 Flash...")
prompt = f"""
You are a witty, friendly weather assistant sending a morning update to a close friend.

CONTEXT:
- Location: {LOCATION}
- Current Date/Day: {now.strftime("%B %d, %Y (%A)")}
- 12-Hour Forecast (list of weather condition IDs): {simplified_weather}

WEATHER CODE GUIDE:
- 2xx → Thunderstorm (stormy, thunder, lightning ⛈️)
- 3xx → Drizzle (light rain 🌦️)
- 5xx → Rain (rainy 🌧️; 502+ = heavy rain)
- 6xx → Snow (snowy ❄️)
- 7xx → Atmosphere (fog, mist, haze 🌫️)
- 800 → Clear sky (sunny ☀️)
- 801–802 → Partly cloudy 🌤️
- 803–804 → Cloudy/overcast ☁️

TASK:
Write a single-paragraph summary of the weather.

RULES:
1. Natural Integration: Blend date + location naturally
2. Emoji Distribution: Use 2–3 emojis placed next to relevant words (NOT all at end)
3. Weather Logic (IMPORTANT):
   - If ANY 2xx → call it a thunderstorm day ⛈️
   - If 502+ or many 5xx → "heavy rain" 🌧️ (warn clearly)
   - If light 3xx/500 → "chance of rain"
   - If 6xx → mention snow ❄️
   - If 7xx → mention fog/mist 🌫️
   - If mostly 800 → sunny ☀️
   - If 801–804 → cloudy/partly cloudy ☁️
- Add a useful suggestion:
  - rain → umbrella
  - cold → jacket
  - hot → stay hydrated
4. Tone: Friendly, slightly funny, conversational
5. Length: 200–250 characters MAX (lock screen friendly)
6. STRICT: Output ONLY the message text (no quotes, no explanations)
"""

# --- Step C: Call Gemini API ---
client = genai.Client(api_key=GEMINI_API_KEY)
response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)

final_message = response.text.strip()
log(f"✅ Gemini summary generated ({len(final_message)} chars).")
log(f"📝 MESSAGE PREVIEW:\n{final_message}\n" + "-" * 40)

# --- Step D: Send Message via Twilio ---
twilio_client = Client(Account_SID, Auth_Token)
log("💬 Attempting to send Twilio WhatsApp message...")

try:
    message = twilio_client.messages.create(
        from_="whatsapp:+14155238886",
        body=final_message,
        to="whatsapp:+16266778986",
    )
    log(f"✅ Twilio message sent! SID: {message.sid}")
except Exception as e:
    log(f"❌ Twilio message failed: {e}")

log("🎉 Script finished execution.")
