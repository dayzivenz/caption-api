import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "71c68875-d8b2-401e-b358-f0131b262e46"
env_id = "1e59fe74-5d4d-4ed5-a443-daf464a1446f"

# Delete nginx service
svc_id = "5af7abae-8c6b-4e52-83ea-aa0c8b0c171b"
print("=== Delete nginx service ===")
rm = """mutation { serviceDelete(environmentId: "%s", id: "%s") }""" % (env_id, svc_id)
r = requests.post(api, json={"query": rm}, headers=headers, timeout=5)
print(f"Deleted: {r.json()}")

time.sleep(2)

# Try another approach - use githubRepoUpdate to change existing service source
print("\n=== Create service with GitHub source via serviceConnect ===")
q1 = """mutation { serviceCreate(input: {projectId: "%s", name: "caption-api"}) { id name } }""" % proj_id
r1 = requests.post(api, json={"query": q1}, headers=headers, timeout=10)
svc_id = r1.json().get("data",{}).get("serviceCreate",{}).get("id","")
print(f"Service: {svc_id}")

# Connect to GitHub
q2 = """mutation { serviceConnect(id: "%s", input: {repo: "dayzivenz/caption-api", branch: "main"}) { id name } }""" % svc_id
r2 = requests.post(api, json={"query": q2}, headers=headers, timeout=10)
print(f"Connected: {json.dumps(r2.json(), indent=2)}")

# Now try environmentStageChanges to trigger deploy
print("\n=== Stage changes ===")
q3 = """mutation { environmentStageChanges(environmentId: "%s", input: {}) { id } }""" % env_id
r3 = requests.post(api, json={"query": q3}, headers=headers, timeout=10)
print(f"Stage: {json.dumps(r3.json(), indent=2)}")

# Check if there are any environment patches
time.sleep(3)
q4 = """query {
    environmentPatches(environmentId: "%s") {
        edges {
            node {
                id
                status
                createdAt
            }
        }
    }
}""" % env_id
r4 = requests.post(api, json={"query": q4}, headers=headers, timeout=10)
print(f"Patches: {json.dumps(r4.json(), indent=2)[:500]}")

# Try environmentPatchCommit
q5 = """mutation { 
    environmentPatchCommit(environmentId: "%s", commitMessage: "deploy caption-api") {
        id
        status
    }
}""" % env_id
r5 = requests.post(api, json={"query": q5}, headers=headers, timeout=10)
print(f"Commit: {json.dumps(r5.json(), indent=2)[:500]}")

# What's the actual service source?
time.sleep(3)
q6 = """query {
    project(id: "%s") {
        services {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
}""" % proj_id
r6 = requests.post(api, json={"query": q6}, headers=headers, timeout=10)
for svc in r6.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
    sid = svc["node"]["id"]
    print(f"\nService: {svc['node']['name']} ({sid[:16]}...)")
    
    # Check deployments
    dq = """query {
        deployments(input: {serviceId: "%s", environmentId: "%s"}) {
            edges { node { id status url createdAt } }
        }
    }""" % (sid, env_id)
    r7 = requests.post(api, json={"query": dq}, headers=headers, timeout=10)
    for dep in r7.json().get("data",{}).get("deployments",{}).get("edges",[]):
        n = dep["node"]
        print(f"  Dep: {n['status']} url={n.get('url','N/A')} created={n['createdAt']}")
        
        if n["status"] == "FAILED":
            bq = """query { buildLogs(deploymentId: "%s") { message severity } }""" % n["id"]
            r8 = requests.post(api, json={"query": bq}, headers=headers, timeout=10)
            for log in r8.json().get("data",{}).get("buildLogs",[]):
                msg = log.get("message","").strip()
                if msg:
                    print(f"    [{log['severity']}] {msg[:300]}")
