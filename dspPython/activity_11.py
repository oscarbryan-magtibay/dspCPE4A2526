{
  "nodes": [
    {
      "parameters": {
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.chatTrigger",
      "typeVersion": 1.3,
      "position": [
        0,
        0
      ],
      "id": "a788762d-20f2-4ef7-908f-8823c7e1d82d",
      "name": "When chat message received",
      "webhookId": "5c76f156-9eb3-42a6-8427-ad8b5db55110"
    },
    {
      "parameters": {
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.agent",
      "typeVersion": 2.2,
      "position": [
        208,
        0
      ],
      "id": "c0e5bb6e-2e2e-4663-8ece-68e962e3ccf5",
      "name": "AI Agent"
    },
    {
      "parameters": {
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
      "typeVersion": 1,
      "position": [
        176,
        192
      ],
      "id": "04e442a4-ce57-4d6c-8516-468a328cce85",
      "name": "Google Gemini Chat Model",
      "credentials": {
        "googlePalmApi": {
          "id": "QLv77iYLI9zg5qN2",
          "name": "Google Gemini(PaLM) Api account 3"
        }
      }
    },
    {
      "parameters": {},
      "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
      "typeVersion": 1.3,
      "position": [
        304,
        224
      ],
      "id": "a96cb76d-50ff-4dec-9c6e-a567a1eb1015",
      "name": "Simple Memory"
    },
    {
      "parameters": {
        "mode": "retrieve-as-tool",
        "toolDescription": "Retrieve documents for AI agent",
        "memoryKey": {
          "__rl": true,
          "value": "vector_store_key",
          "mode": "list",
          "cachedResultName": "vector_store_key"
        },
        "includeDocumentMetadata": "={{ true }}"
      },
      "type": "@n8n/n8n-nodes-langchain.vectorStoreInMemory",
      "typeVersion": 1.3,
      "position": [
        512,
        224
      ],
      "id": "d45a11b4-02b7-44e3-94d6-f76520222b7e",
      "name": "Simple Vector Store"
    },
    {
      "parameters": {},
      "type": "@n8n/n8n-nodes-langchain.embeddingsGoogleGemini",
      "typeVersion": 1,
      "position": [
        352,
        416
      ],
      "id": "500b1528-4e91-4012-b65e-5ab8ba795ea3",
      "name": "Embeddings Google Gemini",
      "credentials": {
        "googlePalmApi": {
          "id": "QLv77iYLI9zg5qN2",
          "name": "Google Gemini(PaLM) Api account 3"
        }
      }
    },
    {
      "parameters": {
        "mode": "insert",
        "memoryKey": {
          "__rl": true,
          "mode": "list",
          "value": "vector_store_key"
        }
      },
      "type": "@n8n/n8n-nodes-langchain.vectorStoreInMemory",
      "typeVersion": 1.3,
      "position": [
        848,
        0
      ],
      "id": "11414b63-f89a-49c3-9ca3-6d10d6eacc24",
      "name": "Simple Vector Store1"
    },
    {
      "parameters": {
        "dataType": "binary",
        "loader": "pdfLoader",
        "textSplittingMode": "custom",
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.documentDefaultDataLoader",
      "typeVersion": 1.1,
      "position": [
        848,
        320
      ],
      "id": "3de33af4-205c-478b-aa58-b0d27d565d4a",
      "name": "Default Data Loader"
    },
    {
      "parameters": {
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter",
      "typeVersion": 1,
      "position": [
        928,
        512
      ],
      "id": "84d76703-15f1-46c5-8e9d-4795ee6e401a",
      "name": "Recursive Character Text Splitter"
    },
    {
      "parameters": {
        "authentication": "basicAuth",
        "formTitle": "contact us",
        "formDescription": "we'll get you back soon",
        "options": {}
      },
      "type": "n8n-nodes-base.formTrigger",
      "typeVersion": 2.3,
      "position": [
        560,
        0
      ],
      "id": "457bdf8a-f52b-4716-8519-c9b5e39fc5ec",
      "name": "On form submission",
      "webhookId": "e5afe37f-d1fe-4336-84ce-d33243dd834e",
      "credentials": {
        "httpBasicAuth": {
          "id": "YsYXEtt429dZKR72",
          "name": "Unnamed credential"
        }
      }
    }
  ],
  "connections": {
    "When chat message received": {
      "main": [
        [
          {
            "node": "AI Agent",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Google Gemini Chat Model": {
      "ai_languageModel": [
        [
          {
            "node": "AI Agent",
            "type": "ai_languageModel",
            "index": 0
          }
        ]
      ]
    },
    "Simple Memory": {
      "ai_memory": [
        [
          {
            "node": "AI Agent",
            "type": "ai_memory",
            "index": 0
          }
        ]
      ]
    },
    "Simple Vector Store": {
      "ai_tool": [
        [
          {
            "node": "AI Agent",
            "type": "ai_tool",
            "index": 0
          }
        ]
      ]
    },
    "Embeddings Google Gemini": {
      "ai_embedding": [
        [
          {
            "node": "Simple Vector Store",
            "type": "ai_embedding",
            "index": 0
          },
          {
            "node": "Simple Vector Store1",
            "type": "ai_embedding",
            "index": 0
          }
        ]
      ]
    },
    "Default Data Loader": {
      "ai_document": [
        [
          {
            "node": "Simple Vector Store1",
            "type": "ai_document",
            "index": 0
          }
        ]
      ]
    },
    "Recursive Character Text Splitter": {
      "ai_textSplitter": [
        [
          {
            "node": "Default Data Loader",
            "type": "ai_textSplitter",
            "index": 0
          }
        ]
      ]
    },
    "On form submission": {
      "main": [
        [
          {
            "node": "Simple Vector Store1",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "fa41ee59c8111dd4b9755fe06f2a480cf7a5c2eb92b83877e013e94925db14f0"
  }
}