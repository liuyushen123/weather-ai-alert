import datetime as dt
import os

import requests
from google import genai
from twilio.rest import Client

LOCATION = "Lincoln NE"

now = dt.datetime.now()

OWM_Endpoint = "https://api.openweathermap.org/data/2.5/forecast"
Account_SID = os.getenv("ACCOUNT_SID")
Auth_Token = os.getenv("AUTH_TOKEN")
parameters = {
    "lat": 40.8137,
    "lon": -96.7026,
    "appid": os.getenv("OWM_KEY"),
    "cnt": 4,
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
api_response = requests.get(OWM_Endpoint, params=parameters)
api_response.raise_for_status()
api_response = api_response.json()

client = genai.Client(api_key=GEMINI_API_KEY)
simplified_weather = []
for interval in api_response["list"]:
    condition = interval["weather"][0]["main"]
    weather_id = interval["weather"][0]["id"]

    simplified_weather.append({"condition": condition, "id": weather_id})

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


response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)

gemini_message = response.text.strip()


def send_bark():
    parameter = {
        "title": "Today's Weather",
        "body": gemini_message,
        "icon": "https://vfiles.gtimg.cn/vupload/20211104/1636015504785.png",
        "group": "WeatherReport",
        "isArchive": 1,
    }

    url = "https://api.day.app/cQGdBMU9Pc6CJhbgDWA5yG/"
    requests.get(url, params=parameter)


def send_whats_app():
    twilio_client = Client(Account_SID, Auth_Token)
    message = twilio_client.messages.create(
        from_="whatsapp:+14155238886",
        body=gemini_message,
        to="whatsapp:+16266778986",
    )


send_whats_app()
