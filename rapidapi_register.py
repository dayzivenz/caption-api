import requests, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Try to register on RapidAPI via their API
EMAIL = "dayzivenz@gmail.com"
PASSWORD = "dayzibitch88XX"

print("=== Registering on RapidAPI ===")

# RapidAPI uses Auth0 for auth
session = requests.Session()

# Step 1: Get signup page
r = session.get("https://rapidapi.com/auth/signup", timeout=15, 
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120"})
print(f"Signup page: {r.status_code}")

# Step 2: Try their API
r2 = session.post("https://auth.rapidapi.com/signup", json={
    "email": EMAIL,
    "password": PASSWORD,
    "name": "dayzivenz",
    "acceptTerms": True,
    "acceptPrivacy": True
}, timeout=15,
    headers={"Content-Type": "application/json", "Origin": "https://rapidapi.com"})
print(f"Signup API: {r2.status_code}")
print(r2.text[:300])

# Step 3: Try login if already registered
r3 = session.post("https://auth.rapidapi.com/login", json={
    "email": EMAIL,
    "password": PASSWORD
}, timeout=15, headers={"Content-Type": "application/json"})
print(f"\nLogin: {r3.status_code}")
print(r3.text[:500])
