"""Quick test script for all Ominou Studio services via gateway."""
import httpx

BASE = "http://localhost:8080/api/v1"
passed = 0
failed = 0

def test(name, method, url, json=None, expected=200):
    global passed, failed
    try:
        if method == "get":
            r = httpx.get(url, timeout=10)
        else:
            r = httpx.post(url, json=json, timeout=10)
        if r.status_code == expected:
            passed += 1
            print(f"  + {name}")
        else:
            failed += 1
            print(f"  X {name} -> {r.status_code}: {r.text[:120]}")
    except Exception as e:
        failed += 1
        print(f"  X {name} -> {e}")

# Auth uses prefix /api/auth so gateway path = /api/v1/auth/auth/...
print("=== Auth Service ===")
import time
test("Register", "post", f"{BASE}/auth/auth/register", {"email": f"test{int(time.time())}@test.com", "password": "Pass1234!", "full_name": "Tester"}, 201)
test("Login", "post", f"{BASE}/auth/auth/login", {"email": "test@ominou.com", "password": "Test1234!"})

print("\n=== Voice Service ===")
test("Get voices", "get", f"{BASE}/voice/voices")
test("Get languages", "get", f"{BASE}/voice/languages")

print("\n=== Design Service ===")
test("Get styles", "get", f"{BASE}/design/styles")
test("Get templates", "get", f"{BASE}/design/templates")

print("\n=== Code Service ===")
test("Get languages", "get", f"{BASE}/code/languages")
test("Get templates", "get", f"{BASE}/code/templates")

# Video uses /api prefix (same as all services)
print("\n=== Video Service ===")
test("Get styles", "get", f"{BASE}/video/styles")
test("Get resolutions", "get", f"{BASE}/video/resolutions")

print("\n=== Writer Service ===")
test("Get content types", "get", f"{BASE}/writer/content-types")
test("Get tones", "get", f"{BASE}/writer/tones")

print("\n=== Music Service ===")
test("Get genres", "get", f"{BASE}/music/genres")
test("Get moods", "get", f"{BASE}/music/moods")

print("\n=== Workflow Service ===")
test("Get templates", "get", f"{BASE}/workflow/templates")
test("List workflows (auth required)", "get", f"{BASE}/workflow/list", expected=403)

print("\n=== Billing Service ===")
test("Get plans", "get", f"{BASE}/billing/plans")

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
