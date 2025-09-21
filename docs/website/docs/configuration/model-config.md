---
sidebar_position: 3
title: Model Configuration
---

# Model Configuration 

**The models are configured in `config/model_config.json`.**

Specifies the LLMs and embedding models used by the simulator:

```jsonc
{
  "chat": [
    {
      "provider": "openai",                     // LLM provider: OpenAI
      "config_name": "openai-gpt4o",            // Configuration identifier
      "model_name": "gpt-4o",                   // Model name
      "api_key": "sk-xxx",                      // API key
      "generate_args": {
        "temperature": 0                        // Temperature setting (0 = deterministic)
      }
    },
    {
      "provider": "vllm",                       // LLM provider: vLLM for local deployment
      "config_name": "vllm-qwen",               // Configuration identifier
      "model_name": "Qwen2.5-14B-Instruct",     // Model name or path
      "client_args": {
        "base_url": "http://localhost:9889/v1/" // Local API endpoint
      },
      "generate_args": {
        "temperature": 0                        // Temperature setting
      }
    }
  ],
  "embedding": [
    {
      "provider": "vllm",
      "config_name": "embedding-bert",   // Configuration identifier
      "model_name": "bge-base-en-v1.5",         // Embedding model name or path
      "client_args": {
        "base_url": "http://localhost:9890/v1/" // Local API endpoint
      }
    }
  ]
}
```

## Supported Providers

YuLan-OneSim supports the following LLM and embedding providers:

| Provider   | Description                 | Chat Models                    | Embedding Models           |
| ---------- | --------------------------- | ------------------------------ | -------------------------- |
| `openai`   | OpenAI API (GPT models)     | GPT-4, GPT-3.5-turbo           | text-embedding-ada-002     |
| `aliyun`   | Alibaba Cloud DashScope API | Qwen series (turbo/plus/max)   | text-embedding-v1          |
| `deepseek` | DeepSeek API                | DeepSeek-chat, DeepSeek-coder  | DeepSeek-embedding         |
| `tencent`  | Tencent Cloud API           | Hunyuan series (lite/standard) | Hunyuan-embedding          |
| `ark`      | ByteDance Ark API           | Doubao series (lite/pro)       | Doubao-embedding           |
| `vllm`     | Local deployment with vLLM  | Llama, Vicuna, ChatGLM         | Various open-source models |

## Field Definitions

| Field                     | Type     | Description                                                         |
| ------------------------- | -------- | ------------------------------------------------------------------- |
| `chat[].provider`         | `string` | Which backend to use ("openai", "vllm", "aliyun", "deepseek", "tencent", "ark")                   |
| `chat[].config_name`      | `string` | Unique key referenced by agents or prompts to select this model     |
| `chat[].model_name`       | `string` | Model identifier or local path to load balance across providers                                     |
| `chat[].api_key`          | `string` | API key for cloud-based providers (e.g., OpenAI, Aliyun, DeepSeek, Tencent, Ark)                    |
| `chat[].client_args`      | `object` | Client arguments (e.g., max_retries, base_url(only for vLLM)) used to customize API request behavior.       |
| `chat[].generate_args`    | `object` | Inference parameters (e.g., temperature) used to control generation behavior.|
| `embedding[].provider`  | `string` | Embedding backend identifier (e.g., `"openai"`)           |
| `embedding[].config_name` | `string` | Unique key referenced by the memory manager to select this embedding |
| `embedding[].model_name`  | `string` | Embedding model identifier or local path                            |
| `embedding[].client_args` | `object` | Client arguments (e.g., max_retries, base_url(only for vLLM)) used to customize API request behavior. |

## Configuration Examples

### OpenAI-Only Configuration

With openAI, you can set your model configs like this to use the API

```jsonc
{
  "chat": [
    {
      "provider": "openai",               
      "config_name": "openai-gpt4o", // you may choose any unique strings as identifier, and there's memory config in config.json refering it  
      "model_name": "gpt-4o",    // chat model name, you can check the list on official documentation.         
      "api_key": "sk-xxx",  // put your API key here.              
      "generate_args": {
        "temperature": 0.7    // arguments of generating, you may check it on documentation of API provider.            
      }
    }
  ],
  "embedding": [
    {
      "provider": "openai",
      "config_name": "openai-embedding", 
      "model_name": "text-embedding-3-small",   // embedding model name, you can check the list on official documentation
    }
  ]
}
```

### Aliyun DashScope Configuration

```jsonc
{
  "chat": [
    {
      "provider": "aliyun",
      "config_name": "aliyun-qwen",
      "model_name": "qwen-plus",
      "api_key": "your-dashscope-api-key",
      "generate_args": {
        "temperature": 0.7
      }
    }
  ],
  "embedding": [
    {
      "provider": "aliyun",
      "config_name": "aliyun-embedding",
      "model_name": "text-embedding-v1",
      "api_key": "your-dashscope-api-key"
    }
  ]
}
```

### DeepSeek Configuration

```jsonc
{
  "chat": [
    {
      "provider": "deepseek",
      "config_name": "deepseek-chat",
      "model_name": "deepseek-chat",
      "api_key": "your-deepseek-api-key",
      "generate_args": {
        "temperature": 0.7
      }
    }
  ]
}
```

### Multi-Provider Configuration

```jsonc
{
  "chat": [
    {
      "provider": "openai",
      "config_name": "openai-gpt4o",
      "model_name": "gpt-4o",
      "api_key": "sk-xxx"
    },
    {
      "provider": "aliyun",
      "config_name": "aliyun-qwen",
      "model_name": "qwen-plus",
      "api_key": "your-dashscope-api-key"
    },
    {
      "provider": "vllm",
      "config_name": "local-llama",
      "model_name": "Llama-3-8B-Instruct",
      "client_args": {
        "base_url": "http://localhost:8000/v1/"
      }
    }
  ],
  "embedding": [
    {
      "provider": "openai",
      "config_name": "openai-embedding",
      "model_name": "text-embedding-3-small",
      "api_key": "sk-xxx"
    }
  ]
}
```
