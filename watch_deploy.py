import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "d22c2fc5-718f-4415-8b41-11f6e40738b7"
env_id = "dde010a2-7b96-4c24-9831-335b4f3bda63"
new_svc_id = "71708f0a-03b7-4292-918c-22046ac86f66"
dep_id = "ee11979e-7f50-4a7c-b89a-d2670de81d5a"

print("=== Watching deployment ===")
for i in range(15):
    # Check status
    dep_query = """query {
        deployments(input: { serviceId: "%s", environmentId: "%s" }) {
            edges {
                node {
                    id
                    status
                    url
                    createdAt
                }
            }
        }
    }""" % (new_svc_id, env_id)
    
    r = requests.post(api, json={"query": dep_query}, headers=headers, timeout=10)
    d = r.json()
    
    status = "unknown"
    url = None
    if d.get("data", {}).get("deployments", {}).get("edges"):
        for edge in d["data"]["deployments"]["edges"]:
            status = edge["node"]["status"]
            url = edge["node"].get("url")
            print(f"[{i+1}/15] Status: {status}  URL: {url or 'N/A'}")
    
    if status in ["SUCCESS", "FAILED", "CRASHED"]:
        break
    
    time.sleep(10)
