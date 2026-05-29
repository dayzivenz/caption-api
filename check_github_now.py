import requests, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"

# Check repos now
q = """query {
  githubRepos {
    name
    fullName
  }
}"""
r = requests.post(api, json={"query": q}, headers=headers, timeout=10)
d = r.json()
print("=== GitHub repos available ===")
print(json.dumps(d, indent=2))

if d.get("data",{}).get("githubRepos"):
    print("\n🔥 GitHub connected! Repos found!")
else:
    print("\n😢 Still no repos")
    
# Check integrations
q2 = """query {
  integrationAuths {
    edges {
      node {
        provider
      }
    }
  }
}"""
r2 = requests.post(api, json={"query": q2}, headers=headers, timeout=10)
print("\n=== Integrations ===")
print(json.dumps(r2.json(), indent=2))
