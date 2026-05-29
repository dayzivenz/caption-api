import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "d22c2fc5-718f-4415-8b41-11f6e40738b7"
env_id = "dde010a2-7b96-4c24-9831-335b4f3bda63"

# Delete old service first
svc_q = """query {
  project(id: "%s") {
    services { edges { node { id name } } }
  }
}""" % proj_id
r = requests.post(api, json={"query": svc_q}, headers=headers, timeout=10)
for svc in r.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
    sid = svc["node"]["id"]
    rm = """mutation { serviceDelete(environmentId: "%s", id: "%s") }""" % (env_id, sid)
    requests.post(api, json={"query": rm}, headers=headers, timeout=5)
    print(f"Deleted {svc['node']['name']}")

time.sleep(2)

# Create new service + connect GitHub + deploy
print("\n1. Create service")
q1 = """mutation { serviceCreate(input: {projectId: "%s", name: "caption-api"}) { id name } }""" % proj_id
r1 = requests.post(api, json={"query": q1}, headers=headers, timeout=10)
svc_id = r1.json().get("data",{}).get("serviceCreate",{}).get("id","")
print(f"   Service: {svc_id}")

print("\n2. Connect GitHub")
q2 = """mutation { serviceConnect(id: "%s", input: {repo: "dayzivenz/caption-api", branch: "main"}) { id name } }""" % svc_id
r2 = requests.post(api, json={"query": q2}, headers=headers, timeout=10)
print(f"   Result: {r2.json().get('data',{}).get('serviceConnect',{}).get('id','')}")

print("\n3. Deploy")
q3 = """mutation { serviceInstanceDeployV2(serviceId: "%s", environmentId: "%s") }""" % (svc_id, env_id)
r3 = requests.post(api, json={"query": q3}, headers=headers, timeout=15)
dep_id = r3.json().get("data",{}).get("serviceInstanceDeployV2","")
print(f"   Deployment: {dep_id}")

print("\n4. Domain")
q4 = """mutation { serviceDomainCreate(input: {serviceId: "%s", environmentId: "%s"}) { domain } }""" % (svc_id, env_id)
r4 = requests.post(api, json={"query": q4}, headers=headers, timeout=10)
domain = r4.json().get("data",{}).get("serviceDomainCreate",{}).get("domain","N/A")
print(f"   Domain: https://{domain}")

print("\n5. Watching deploy...")
for i in range(30):
    time.sleep(10)
    dq = """query {
        deployments(input: {serviceId: "%s", environmentId: "%s"}) {
            edges { node { id status url } }
        }
    }""" % (svc_id, env_id)
    r5 = requests.post(api, json={"query": dq}, headers=headers, timeout=10)
    for dep in r5.json().get("data",{}).get("deployments",{}).get("edges",[]):
        n = dep["node"]
        print(f"   [{i+1}/30] {n['status']}  url={n.get('url','N/A')}")
        
        if n["status"] == "FAILED":
            bq = """query { buildLogs(deploymentId: "%s") { message severity } }""" % n["id"]
            r6 = requests.post(api, json={"query": bq}, headers=headers, timeout=10)
            for log in r6.json().get("data",{}).get("buildLogs",[]):
                msg = log.get("message","").strip()
                if msg:
                    print(f"      [{log['severity']}] {msg[:300]}")
        
        if n["status"] == "SUCCESS":
            print(f"\n🔥🔥🔥 API LIVE: {n.get('url','N/A')} 🔥🔥🔥")
            print(f"   Swagger: {n.get('url','').rstrip('/')}/docs")
            exit(0)
