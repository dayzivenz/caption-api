import requests, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "71c68875-d8b2-401e-b358-f0131b262e46"
env_id = "1e59fe74-5d4d-4ed5-a443-daf464a1446f"

# Get all info
q = """query {
  project(id: "%s") {
    services {
      edges {
        node {
          id
          name
          updatedAt
        }
      }
    }
    environments {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}""" % proj_id
r = requests.post(api, json={"query": q}, headers=headers, timeout=10)
print(json.dumps(r.json(), indent=2))

print("\n=== Deployment details ===")
for svc in r.json().get("data",{}).get("project",{}).get("services",{}).get("edges",[]):
    sid = svc["node"]["id"]
    dq = """query {
        deployments(input: {serviceId: "%s", environmentId: "%s"}) {
            edges {
                node {
                    id
                    status
                    url
                    createdAt
                }
            }
        }
    }""" % (sid, env_id)
    r2 = requests.post(api, json={"query": dq}, headers=headers, timeout=10)
    print(f"\nService: {svc['node']['name']} ({sid[:16]}...)")
    for dep in r2.json().get("data",{}).get("deployments",{}).get("edges",[]):
        did = dep["node"]["id"]
        print(f"  Dep: {did[:16]}... status={dep['node']['status']} created={dep['node']['createdAt']}")
        
        # Full build logs
        bq = """query { buildLogs(deploymentId: "%s") { message severity tags { buildId } } }""" % did
        r3 = requests.post(api, json={"query": bq}, headers=headers, timeout=10)
        logs = r3.json().get("data",{}).get("buildLogs",[])
        print(f"  Build logs ({len(logs)}):")
        for log in logs:
            print(f"    [{log['severity']}] {log.get('message','')[:400]}")
        
        # Deployment logs
        dlq = """query { deploymentLogs(deploymentId: "%s") { message severity } }""" % did
        r4 = requests.post(api, json={"query": dlq}, headers=headers, timeout=10)
        dlogs = r4.json().get("data",{}).get("deploymentLogs",[])
        print(f"  Deploy logs ({len(dlogs)}):")
        for log in dlogs[:10]:
            print(f"    [{log['severity']}] {log.get('message','')[:400]}")
