import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"

# Get latest deployment
for i in range(12):
    time.sleep(10)
    dq = """query {
        deployments(input: {serviceId: "6219a424-e0f4-4afc-ae29-ab0e67b807b7", environmentId: "1e59fe74-5d4d-4ed5-a443-daf464a1446f"}) {
            edges { node { id status url } }
        }
    }"""
    r = requests.post(api, json={"query": dq}, headers=headers, timeout=5)
    d = r.json()
    for dep in d.get("data",{}).get("deployments",{}).get("edges",[]):
        n = dep["node"]
        print(f"[{i+1}/12] {n['status']} url={n.get('url','N/A')}")
        if n["status"] == "SUCCESS" and n.get("url"):
            print(f"\n🔥🔥🔥 APILIVE: {n['url']}")
            print(f"🔥🔥🔥 DOCS:   {n['url'].rstrip('/')}/docs")
            exit(0)
