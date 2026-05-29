import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "d22c2fc5-718f-4415-8b41-11f6e40738b7"
env_id = "dde010a2-7b96-4c24-9831-335b4f3bda63"

# Check what exists
print("=== Current state ===")
svc_q = """query {
  project(id: "%s") {
    services { edges { node { id name } } }
  }
}""" % proj_id
r = requests.post(api, json={"query": svc_q}, headers=headers, timeout=10)
print(json.dumps(r.json(), indent=2))

# Check if there's a service
for svc in r.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
    sid = svc["node"]["id"]
    dep_q = """query {
        deployments(input: {serviceId: "%s", environmentId: "%s"}) {
            edges { node { id status url createdAt } }
        }
    }""" % (sid, env_id)
    r2 = requests.post(api, json={"query": dep_q}, headers=headers, timeout=10)
    print(f"\nDeployments for {svc['node']['name']}:")
    print(json.dumps(r2.json(), indent=2))
    
    for dep in r2.json().get("data",{}).get("deployments",{}).get("edges",[]):
        did = dep["node"]["id"]
        if dep["node"]["status"] == "FAILED":
            bq = """query { buildLogs(deploymentId: "%s") { message severity } }""" % did
            r3 = requests.post(api, json={"query": bq}, headers=headers, timeout=10)
            logs = r3.json().get("data",{}).get("buildLogs",[])
            for log in logs:
                msg = log.get("message","").strip()
                if msg and msg != "scheduling build on Metal builder":
                    print(f"  LOG: [{log['severity']}] {msg[:500]}")
