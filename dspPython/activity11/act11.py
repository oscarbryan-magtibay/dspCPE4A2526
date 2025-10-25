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
      "id": "2f1810d7-5234-476a-93ed-93a7634ba1be",
      "name": "When chat message received",
      "webhookId": "40c8efe0-40fb-424f-9449-fde16525413a"
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
      "id": "c3c74e6a-8672-4e1d-8c63-16a841668692",
      "name": "AI Agent"
    },
    {
      "parameters": {
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
      "typeVersion": 1,
      "position": [
        80,
        208
      ],
      "id": "b4ae3f2f-7ffe-48d3-b88e-62ee4d7e9d0f",
      "name": "Google Gemini Chat Model",
      "credentials": {
        "googlePalmApi": {
          "id": "4X2P40ARLkF9uK0y",
          "name": "Google Gemini(PaLM) Api account"
        }
      }
    },
    {
      "parameters": {},
      "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
      "typeVersion": 1.3,
      "position": [
        224,
        208
      ],
      "id": "2936f302-48a5-4bed-bc95-78f15ecf8942",
      "name": "Simple Memory"
    },
    {
      "parameters": {
        "mode": "retrieve-as-tool",
        "toolDescription": "Retrieve information for knowledgebase based for the question",
        "memoryKey": {
          "__rl": true,
          "mode": "list",
          "value": "vector_store_key"
        },
        "includeDocumentMetadata": false
      },
      "type": "@n8n/n8n-nodes-langchain.vectorStoreInMemory",
      "typeVersion": 1.3,
      "position": [
        352,
        192
      ],
      "id": "9f5e4c15-4ba7-4c85-adc5-d5719f225694",
      "name": "Simple Vector Store"
    },
    {
      "parameters": {},
      "type": "@n8n/n8n-nodes-langchain.embeddingsGoogleGemini",
      "typeVersion": 1,
      "position": [
        528,
        352
      ],
      "id": "7f8fb8f9-f3d0-450c-907d-2cd89add4841",
      "name": "Embeddings Google Gemini",
      "credentials": {
        "googlePalmApi": {
          "id": "4X2P40ARLkF9uK0y",
          "name": "Google Gemini(PaLM) Api account"
        }
      }
    },
    {
      "parameters": {
        "formTitle": "Contact Us",
        "formDescription": "Made by Joseph Bacroya\nEmail : 2220700@ub.edu.ph",
        "options": {}
      },
      "type": "n8n-nodes-base.formTrigger",
      "typeVersion": 2.3,
      "position": [
        544,
        48
      ],
      "id": "924f18b7-9cc0-4aa5-aeb5-a17be58f4251",
      "name": "On form submission",
      "webhookId": "1ace3eb0-27b4-4562-bf6b-80ba783119c5"
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
        768,
        0
      ],
      "id": "d89fd3eb-8040-419d-98e2-d339f59e8c92",
      "name": "Simple Vector Store1"
    },
    {
      "parameters": {
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.documentDefaultDataLoader",
      "typeVersion": 1.1,
      "position": [
        832,
        160
      ],
      "id": "bcdce22e-a66d-4c46-abbf-e7585295751a",
      "name": "Default Data Loader"
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
    }
  },
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "0013b39d10d8f8a4a5180ac0f62bbd0b2f8a6d61ac159c4ba5bfdd0d4e5afb59"
  }
}