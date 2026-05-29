import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "71c68875-d8b2-401e-b358-f0131b262e46"
env_id = "1e59fe74-5d4d-4ed5-a443-daf464a1446f"

# Delete old
print("=== Delete old service ===")
q = """query { project(id: "%s") { services { edges { node { id name } } } } }""" % proj_id
r = requests.post(api, json={"query": q}, headers=headers, timeout=20)
for svc in r.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
    sid = svc["node"]["id"]
    rm = """mutation { serviceDelete(environmentId: "%s", id: "%s") }""" % (env_id, sid)
    r2 = requests.post(api, json={"query": rm}, headers=headers, timeout=20)
    print(f"Deleted: {r2.json()}")

time.sleep(3)

# Deploy v2
print("\n=== Deploy v2 ===")
dep = """mutation {
    githubRepoDeploy(input: {
        projectId: "%s",
        environmentId: "%s",
        repo: "dayzivenz/caption-api",
        branch: "main"
    })
}""" % (proj_id, env_id)
r3 = requests.post(api, json={"query": dep}, headers=headers, timeout=30)
d3 = r3.json()
print(json.dumps(d3, indent=2))
dep_id = d3.get("data",{}).get("githubRepoDeploy","")

# Domain
time.sleep(10)
svc_q = """query { project(id: "%s") { services { edges { node { id name } } } } }""" % proj_id
r4 = requests.post(api, json={"query": svc_q}, headers=headers, timeout=20)
for svc in r4.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
    sid = svc["node"]["id"]
    dom = """mutation { serviceDomainCreate(input: {serviceId: "%s", environmentId: "%s"}) { domain } }""" % (sid, env_id)
    r5 = requests.post(api, json={"query": dom}, headers=headers, timeout=20)
    print(f"Domain: https://{r5.json().get('data',{}).get('serviceDomainCreate',{}).get('domain','N/A')}")

# Watch
print("\n=== Watch ===")
for i in range(20):
    time.sleep(15)
    r6 = requests.post(api, json={"query": svc_q}, headers=headers, timeout=20)
    for svc in r6.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
        sid = svc["node"]["id"]
        dq = """query {
            deployments(input: {serviceId: "%s", environmentId: "%s"}) {
                edges { node { id status url } }
            }
        }""" % (sid, env_id)
        r7 = requests.post(api, json={"query": dq}, headers=headers, timeout=20)
        for dep2 in r7.json().get("data",{}).get("deployments",{}).get("edges",[]):
            n = dep2["node"]
            print(f"  [{i+1}/20] {n['status']} url={n.get('url','N/A')}")
            if n["status"] == "SUCCESS":
                print(f"\n🔥 V2 DEPLOYED: {n.get('url','N/A')}")
                exit(0)
