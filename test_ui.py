import json
import time
from playwright.sync_api import sync_playwright

script_json = """{
  "title": "సుందరకాండ - హనుమంతుని జాగృతి",
  "language": "telugu",
  "duration_sec": 180,
  "voice": {
    "type": "male",
    "tone": "devotional, deep, emotional",
    "speed": 0.9
  },
  "subtitle": {
    "enabled": true,
    "style": "తెలుగు bold, cinematic fade"
  },
  "scenes": [
    {
      "id": 1,
      "visual": "vast ocean sunrise, vanara army standing",
      "camera": "aerial wide slow zoom",
      "bgm": "soft flute + waves",
      "narration": "అనేక అరణ్యాలు దాటి... వానర సైన్యం సముద్రం ముందు ఆగిపోయింది..."
    },
    {
      "id": 2,
      "visual": "sad vanaras बैठे, worried",
      "camera": "slow pan close shots",
      "bgm": "low sad strings",
      "narration": "ఆశలు తగ్గుతున్నాయి... సీతమ్మ ఎక్కడ ఉందో తెలియదు..."
    },
    {
      "id": 3,
      "visual": "Jambavan speaking to Hanuman",
      "camera": "low angle",
      "dialogue": "హనుమంతుడా... నువ్వు సాధారణవాడివి కాదు..."
    },
    {
      "id": 4,
      "visual": "Hanuman childhood flying to sun",
      "camera": "flashback glow",
      "bgm": "divine choir",
      "narration": "మర్చిపోయిన శక్తి ఇప్పుడు మేల్కొంటోంది..."
    },
    {
      "id": 5,
      "visual": "Hanuman rising energy aura",
      "camera": "orbit shot",
      "bgm": "rising epic music",
      "dialogue": "నేను ఈ సముద్రాన్ని దాటుతాను!"
    },
    {
      "id": 6,
      "visual": "Hanuman giant form transformation",
      "camera": "low hero shot",
      "sfx": "rumble",
      "narration": "శక్తి తిరిగి వచ్చింది..."
    },
    {
      "id": 7,
      "visual": "Hanuman on mountain peak",
      "camera": "wide silhouette",
      "dialogue": "ఏ అడ్డంకి వచ్చినా ఆగను!"
    },
    {
      "id": 8,
      "visual": "jump preparation dust rising",
      "camera": "slow motion",
      "bgm": "heartbeat",
      "narration": "రామనామంతో..."
    },
    {
      "id": 9,
      "visual": "Hanuman flying across ocean",
      "camera": "tracking shot",
      "bgm": "epic + Jai Shri Ram chant",
      "narration": "భక్తి ఎగిరింది!"
    }
  ]
}"""

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Login if needed, or go straight to dashboard
            print("Navigating to Video Studio...")
            page.goto("http://localhost:2102/dashboard/video-studio")
            
            # Wait for the page to load
            page.wait_for_selector("text=Film Studio", timeout=10000)
            
            # Click Script Mode
            print("Switching to Script Mode...")
            page.click("button:has-text('Script Mode')")
            
            # Paste the JSON
            print("Pasting the JSON script...")
            page.locator("textarea").fill(script_json)
            
            # Take a screenshot to verify step
            page.screenshot(path="d:/ominou-studio/before_generate.png")
            
            # Click Generate
            print("Clicking Generate...")
            page.click("button:has-text('Generate')")
            
            # Wait for generation to progress
            print("Waiting for generation process...")
            time.sleep(5)
            page.screenshot(path="d:/ominou-studio/processing_generate.png")
            
            print("Done initiating. Screenshots saved.")
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="d:/ominou-studio/error_screenshot.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
