import os
import subprocess
import json
import time

N8N_CONTAINER_NAME = "n8n_gemini"
N8N_PORT = "5678"
N8N_VOLUME = os.path.expanduser("~/.n8n")
WORKFLOW_FILE = "gemini_rag_workflow.json"

workflow_json = {
    "nodes": [
        {
            "parameters": {
                "options": {}
            },
            "type": "@n8n/n8n-nodes-langchain.chatTrigger",
            "typeVersion": 1.3,
            "position": [0, 0],
            "id": "a788762d-20f2-4ef7-908f-8823c7e1d82d",
            "name": "When chat message received",
            "webhookId": "5c76f156-9eb3-42a6-8427-ad8b5db55110"
        },
        {
            "parameters": {"options": {}},
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 2.2,
            "position": [208, 0],
            "id": "c0e5bb6e-2e2e-4663-8ece-68e962e3ccf5",
            "name": "AI Agent"
        },
        {
            "parameters": {"options": {}},
            "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
            "typeVersion": 1,
            "position": [176, 192],
            "id": "04e442a4-ce57-4d6c-8516-468a328cce85",
            "name": "Google Gemini Chat Model",
            "credentials": {
                "googlePalmApi": {
                    "id": "QLv77iYLI9zg5qN2",
                    "name": "Google Gemini(PaLM) Api account 3"
                }
            }
        },
    ]
}

# Save to file
with open(WORKFLOW_FILE, "w") as f:
    json.dump(workflow_json, f, indent=2)

print(f"✅ Workflow saved as {WORKFLOW_FILE}")

print("🚀 Starting n8n container...")
try:
    subprocess.run([
        "docker", "run", "-d",
        "--name", N8N_CONTAINER_NAME,
        "-p", f"{N8N_PORT}:5678",
        "-v", f"{N8N_VOLUME}:/home/node/.n8n",
        "n8nio/n8n"
    ], check=True)
except subprocess.CalledProcessError as e:
    print("⚠️ Could not start n8n container (maybe it’s already running).")
    print(str(e))

print("⏳ Waiting for n8n to start...")
time.sleep(10)

print("📤 Uploading workflow to n8n...")
import requests

workflow_data = open(WORKFLOW_FILE, "rb")
response = requests.post(
    f"http://localhost:{N8N_PORT}/rest/workflows",
    files={"file": workflow_data}
)

if response.status_code in (200, 201):
    print("✅ Workflow imported successfully!")
else:
    print(f"❌ Failed to import workflow: {response.status_code}")
    print(response.text)

print("\n🎯 n8n is now running on: http://localhost:5678")
print("You can open it in your browser and start chatting with Gemini!")
