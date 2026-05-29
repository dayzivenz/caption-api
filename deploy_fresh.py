import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "d22c2fc5-718f-4415-8b41-11f6e40738b7"
env_id = "dde010a2-7b96-4c24-9831-335b4f3bda63"

# Delete old project and recreate
print("=== Delete old project ===")
del_p = """mutation { projectDelete(id: "%s") }""" % proj_id
r = requests.post(api, json={"query": del_p}, headers=headers, timeout=10)
print(json.dumps(r.json(), indent=2))

time.sleep(2)

# Create new project
ws_id = "b1cffeb2-8869-4c08-8838-a7c7fb3d93ee"
print("\n=== Create fresh project ===")
cr_p = """mutation { projectCreate(input: {name: "caption-api", workspaceId: "%s"}) { id environments { edges { node { id name } } } } }""" % ws_id
r2 = requests.post(api, json={"query": cr_p}, headers=headers, timeout=10)
d2 = r2.json()
print(json.dumps(d2, indent=2))

new_proj_id = d2.get("data",{}).get("projectCreate",{}).get("id","")
new_env_id = None
for env in d2.get("data",{}).get("projectCreate",{}).get("environments",{}).get("edges",[]):
    if env["node"]["name"] == "production":
        new_env_id = env["node"]["id"]
        break

if not new_env_id:
    cr_env = """mutation { environmentCreate(input: {projectId: "%s", name: "production"}) { id } }""" % new_proj_id
    r_env = requests.post(api, json={"query": cr_env}, headers=headers, timeout=10)
    new_env_id = r_env.json().get("data",{}).get("environmentCreate",{}).get("id","")

print(f"\nNew project: {new_proj_id}")
print(f"New env: {new_env_id}")

# Deploy via githubRepoDeploy
print("\n=== Deploy via githubRepoDeploy ===")
dep = """mutation {
    githubRepoDeploy(input: {
        projectId: "%s",
        environmentId: "%s",
        repo: "dayzivenz/caption-api",
        branch: "main"
    })
}""" % (new_proj_id, new_env_id)

r3 = requests.post(api, json={"query": dep}, headers=headers, timeout=20)
d3 = r3.json()
print(json.dumps(d3, indent=2))

# Get domain
time.sleep(5)
svc_q = """query { project(id: "%s") { services { edges { node { id name } } } } }""" % new_proj_id
r4 = requests.post(api, json={"query": svc_q}, headers=headers, timeout=10)
for svc in r4.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
    sid = svc["node"]["id"]
    dom = """mutation { serviceDomainCreate(input: {serviceId: "%s", environmentId: "%s"}) { domain } }""" % (sid, new_env_id)
    r5 = requests.post(api, json={"query": dom}, headers=headers, timeout=10)
    dom_val = r5.json().get("data",{}).get("serviceDomainCreate",{}).get("domain","N/A")
    print(f"\nDomain: https://{dom_val}")

# Wait
print("\n=== Watching ===")
for i in range(20):
    time.sleep(10)
    r6 = requests.post(api, json={"query": svc_q}, headers=headers, timeout=10)
    for svc in r6.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
        sid = svc["node"]["id"]
        dq = """query {
            deployments(input: {serviceId: "%s", environmentId: "%s"}) {
                edges { node { id status url } }
            }
        }""" % (sid, new_env_id)
        r7 = requests.post(api, json={"query": dq}, headers=headers, timeout=10)
        for dep in r7.json().get("data",{}).get("deployments",{}).get("edges",[]):
            n = dep["node"]
            print(f"  [{i+1}/20] {n['status']} url={n.get('url','N/A')}")
            
            if n["status"] == "FAILED":
                bq = """query { buildLogs(deploymentId: "%s") { message severity } }""" % n["id"]
                r8 = requests.post(api, json={"query": bq}, headers=headers, timeout=10)
                for log in r8.json().get("data",{}).get("buildLogs",[]):
                    msg = log.get("message","").strip()
                    if msg and "scheduling" not in msg:
                        print(f"    LOG: {msg[:300]}")
            
            if n["status"] == "SUCCESS":
                print(f"\n🔥🔥🔥 API: {n.get('url','')} 🔥🔥🔥")
                exit(0)
