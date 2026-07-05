import urllib.request
import json

req = urllib.request.Request(
    "http://localhost:8000/api/chat",
    data=json.dumps({"question": "What is Pangochain?"}).encode(),
    headers={"Content-Type": "application/json"},
)
res = urllib.request.urlopen(req)
data = json.loads(res.read())
print(f"Answer: {data['answer'][:500]}")
print(f"\nSources: {len(data['sources'])}")
print(f"Time: {data['response_time_ms']}ms")
