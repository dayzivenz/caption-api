import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "71c68875-d8b2-401e-b358-f0131b262e46"
env_id = "1e59fe74-5d4d-4ed5-a443-daf464a1446f"
ws_id = "b1cffeb2-8869-4c08-8838-a7c7fb3d93ee"

# Delete old service
svc_q = """query {
  project(id: "%s") { services { edges { node { id name } } } }
}""" % proj_id
r = requests.post(api, json={"query": svc_q}, headers=headers, timeout=10)
for svc in r.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
    sid = svc["node"]["id"]
    rm = """mutation { serviceDelete(environmentId: "%s", id: "%s") }""" % (env_id, sid)
    requests.post(api, json={"query": rm}, headers=headers, timeout=5)
    print(f"Deleted {svc['node']['name']}")

time.sleep(2)

# Check if we can find a template for caption-api
print("\n=== Search templates ===")
tq = """query {
  templateSearch(query: "caption-api") {
    ... on Template {
      id
      name
    }
  }
}"""
r2 = requests.post(api, json={"query": tq}, headers=headers, timeout=10)
print(json.dumps(r2.json(), indent=2)[:500])

# Try templateClone
print("\n=== Try deploy via Docker ===")
# Create service with Docker image nginx first to test
q = """mutation {
  serviceCreate(input: {
    projectId: "%s",
    name: "caption-api",
    source: { image: "nginx" }
  }) {
    id
    name
  }
}""" % proj_id

r3 = requests.post(api, json={"query": q}, headers=headers, timeout=10)
d3 = r3.json()
print(json.dumps(d3, indent=2))

svc_id = d3.get("data",{}).get("serviceCreate",{}).get("id","")
if svc_id:
    # Deploy
    dq = """mutation { serviceInstanceDeployV2(serviceId: "%s", environmentId: "%s") }""" % (svc_id, env_id)
    r4 = requests.post(api, json={"query": dq}, headers=headers, timeout=15)
    print(f"Deploy: {json.dumps(r4.json(), indent=2)}")
    
    # Domain
    dom = """mutation { serviceDomainCreate(input: {serviceId: "%s", environmentId: "%s"}) { domain } }""" % (svc_id, env_id)
    r5 = requests.post(api, json={"query": dom}, headers=headers, timeout=10)
    print(f"Domain: {json.dumps(r5.json(), indent=2)}")
    
    # Watch
    print("\n=== Watch ===")
    for i in range(15):
        time.sleep(10)
        dq2 = """query {
            deployments(input: {serviceId: "%s", environmentId: "%s"}) {
                edges { node { id status url } }
            }
        }""" % (svc_id, env_id)
        r6 = requests.post(api, json={"query": dq2}, headers=headers, timeout=10)
        for dep in r6.json().get("data",{}).get("deployments",{}).get("edges",[]):
            n = dep["node"]
            print(f"  [{i+1}/15] {n['status']} url={n.get('url','N/A')}")
            
            if n["status"] == "SUCCESS":
                print(f"\n🔥 SUCCESS: {n.get('url','')}")
                exit(0)
