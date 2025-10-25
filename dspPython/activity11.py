{
  "nodes": [
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
      "id": "3557f75b-1033-4613-a4d2-ba36a2e66df7",
      "name": "Google Gemini Chat Model",
      "credentials": {
        "googlePalmApi": {
          "id": "E98A3lBsFqJr3CzQ",
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
      "id": "3d4513bc-0876-46a7-b4a3-06d80ff0bcde",
      "name": "Simple Memory"
    },
    {
      "parameters": {
        "mode": "retrieve-as-tool",
        "toolDescription": "Retrieve information for knowledgebase based for the question.",
        "memoryKey": {
          "__rl": true,
          "mode": "list",
          "value": "vector_store_key"
        }
      },
      "type": "@n8n/n8n-nodes-langchain.vectorStoreInMemory",
      "typeVersion": 1.3,
      "position": [
        368,
        224
      ],
      "id": "af70648b-e8a0-47fd-81f1-884f564db310",
      "name": "Simple Vector Store"
    },
    {
      "parameters": {},
      "type": "@n8n/n8n-nodes-langchain.embeddingsGoogleGemini",
      "typeVersion": 1,
      "position": [
        464,
        432
      ],
      "id": "6d9bc264-28c9-4692-95c3-57fd1022ca1e",
      "name": "Embeddings Google Gemini",
      "credentials": {
        "googlePalmApi": {
          "id": "E98A3lBsFqJr3CzQ",
          "name": "Google Gemini(PaLM) Api account"
        }
      }
    },
    {
      "parameters": {
        "authentication": "basicAuth",
        "formTitle": "Form",
        "formFields": {
          "values": [
            {
              "fieldLabel": "pdf",
              "fieldType": "file",
              "acceptFileTypes": "pdf"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.formTrigger",
      "typeVersion": 2.3,
      "position": [
        608,
        48
      ],
      "id": "2882d23c-7190-40bc-a6d6-a6980c523c6b",
      "name": "On form submission",
      "webhookId": "a732eec3-ebe0-4dc5-b4d2-c1701f39d9c2",
      "credentials": {
        "httpBasicAuth": {
          "id": "qkFwf5mBNZOGrOM2",
          "name": "Unnamed credential 2"
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
        816,
        48
      ],
      "id": "e90afabe-cdc8-4c4f-bb0c-cb98e916db33",
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
        960,
        256
      ],
      "id": "2126ddd0-1a2a-47c3-9889-caa213759b53",
      "name": "Default Data Loader"
    },
    {
      "parameters": {
        "options": {}
      },
      "type": "@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter",
      "typeVersion": 1,
      "position": [
        1056,
        464
      ],
      "id": "88cf985c-6cd3-4fa8-b420-af309754ffe1",
      "name": "Recursive Character Text Splitter"
    }
  ],
  "connections": {
    "Google Gemini Chat Model": {
      "ai_languageModel": [
        []
      ]
    },
    "Simple Memory": {
      "ai_memory": [
        []
      ]
    },
    "Simple Vector Store": {
      "ai_tool": [
        []
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
    }
  },
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "8825dc18ea84ae07a1afe4bcb3893595dcb65fc31f9f7dd44e7177595cc518bb"
  }
}