import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://localhost:2102/dashboard/video-studio")
            page.wait_for_selector("text=Film Studio", timeout=10000)
            
            page.click("button:has-text('Script Mode')")
            page.locator("textarea").fill("""{
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
    }
  ]
}""")
            
            page.click("button:has-text('Generate')")
            print("Generate clicked. Waiting for completion...")
            
            # loop and check for success or failure message
            for i in range(30):
                content = page.content()
                if "Video ready!" in content:
                    print("SUCCESS: Video generated successfully.")
                    page.screenshot(path="d:/ominou-studio/success.png")
                    break
                elif "Generation failed" in content or "Error:" in content:
                    print("FAILED: Video generation returned an error.")
                    page.screenshot(path="d:/ominou-studio/failed.png")
                    break
                time.sleep(2)
            else:
                print("TIMEOUT: Generation took too long or got stuck.")
                page.screenshot(path="d:/ominou-studio/timeout.png")
        except Exception as e:
            print(f"Playwright Error: {e}")
            page.screenshot(path="d:/ominou-studio/fatal_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
