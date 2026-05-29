import requests, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN = "74fd43a8-a9e9-48d8-b788-3505cea784bf"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
api = "https://api.railway.app/graphql/v2"
proj_id = "71c68875-d8b2-401e-b358-f0131b262e46"
env_id = "1e59fe74-5d4d-4ed5-a443-daf464a1446f"
ws_id = "b1cffeb2-8869-4c08-8838-a7c7fb3d93ee"

# Try templateDeployV2 approach - look up what it needs
print("=== Introspect TemplateDeployV2Input ===")
q = """query {
  __type(name: "TemplateDeployV2Input") {
    inputFields {
      name
      type { name kind }
    }
  }
}"""
r = requests.post(api, json={"query": q}, headers=headers, timeout=10)
print(json.dumps(r.json(), indent=2))

print("\n=== Introspect SerializedTemplateConfig ===")
q2 = """query {
  __type(name: "SerializedTemplateConfig") {
    inputFields {
      name
      type { name kind }
    }
  }
}"""
r2 = requests.post(api, json={"query": q2}, headers=headers, timeout=10)
print(json.dumps(r2.json(), indent=2)[:2000])
