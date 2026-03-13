import requests, json

r = requests.post("http://localhost:8000/agent-builder", json={
    "input": "Support has been useless, been waiting 3 weeks and no one replies. Cancelling now.",
    "company": "Zendesk"
}, timeout=60)

d = r.json()
report = d["report"]

print(f"Model: {d['model']}  |  {d['latency_ms']}ms  |  {d['sources_searched']} sources from Elasticsearch\n")
print("SUMMARY:", report["executive_summary"])
print("\nURGENCY:", report["trigger_analysis"]["urgency"].upper())
print("CHURN RISK:", report["risk_assessment"]["churn_probability"])
print("SEVERITY:", report["risk_assessment"]["severity"])
print("\nPLAYBOOK:")
for s in report["resolution_playbook"]["steps"]:
    print(f"  {s['step']}. [{s['timing']}] {s['action']}")
print("\nEMAIL TO SEND:")
print(report["response_templates"]["immediate_acknowledgement"])
print("\nFULL REPORT:")
print(json.dumps(report, indent=2))
