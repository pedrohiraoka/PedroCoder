# OLLAMA Setup Guide

This document provides instructions for setting up Ollama to use with ChatBotAI.

## Overview

ChatBotAI uses Ollama as its default AI engine for local, private LLM inference.
Ollama supports the Llama family of models and many other open-source models.

## Installation

### macOS / Linux

1. **Install Ollama:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Verify installation:**
   ```bash
   ollama --version
   ```

### Windows

1. Download the installer from: https://ollama.ai/download
2. Run the installer and follow the prompts
3. Verify installation in PowerShell:
   ```powershell
   ollama --version
   ```

## Model Setup

### Pulling Llama Models

ChatBotAI defaults to `llama3.2`, but you can use any model available in Ollama.

```bash
# Pull the default Llama 3.2 model (recommended)
ollama pull llama3.2

# Alternative Llama models
ollama pull llama3.1
ollama pull llama3
ollama pull llama2

# Other popular models
ollama pull mistral
ollama pull codellama
ollama pull phi3
```

### Listing Available Models

```bash
ollama list
```

### Removing Models

```bash
ollama rm <model_name>
```

## Running Ollama Server

### Default (Local) Mode

Ollama runs as a background service automatically after installation.

**Check if running:**
```bash
curl http://localhost:11434/api/tags
```

### Custom Configuration

To run Ollama on a different port or host:

```bash
# Set environment variables before starting
export OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

### Docker Deployment

```bash
docker run -d -p 11434:11434 --name ollama ollama/ollama
```

## Configuring ChatBotAI

### Using Default Settings

By default, ChatBotAI connects to:
- URL: `http://localhost:11434`
- Model: `llama3.2`

### Custom Configuration

Edit `config.yaml`:

```yaml
ollama:
  model_name: llama3.1
  base_url: http://localhost:11434
  timeout: 60
  temperature: 0.7
  top_p: 0.9
```

Or use environment variables:

```bash
export CHATBOT_OLLAMA_MODEL=llama3.1
export CHATBOT_OLLAMA_BASE_URL=http://localhost:11434
```

## Testing Your Setup

### Quick Test with Ollama CLI

```bash
ollama run llama3.2 "Hello, how are you?"
```

### Test with ChatBotAI

```bash
cd chatbotai
python quickstart.py
```

## Troubleshooting

### Connection Refused

If you get connection errors:

1. Ensure Ollama is running:
   ```bash
   ps aux | grep ollama
   ```

2. Start Ollama manually:
   ```bash
   ollama serve
   ```

3. Check firewall settings for port 11434

### Model Not Found

```bash
# Pull the required model
ollama pull llama3.2

# Verify it's available
ollama list
```

### Memory Issues

For large models, ensure sufficient RAM:

- Llama 3.2 3B: ~2GB RAM
- Llama 3.2 7B: ~4GB RAM
- Llama 3.1 8B: ~5GB RAM
- Llama 3.1 70B: ~40GB RAM

### Slow Responses

1. Use a smaller model (e.g., `llama3.2` instead of `llama3.1:70b`)
2. Reduce context window size in config
3. Ensure GPU acceleration is enabled if available

## Advanced Configuration

### GPU Acceleration

Ollama automatically uses GPU if available. To force CPU-only:

```bash
export OLLAMA_NUM_GPU=0
ollama serve
```

### Custom Model Parameters

Create a Modelfile for custom parameters:

```dockerfile
FROM llama3.2
PARAMETER temperature 0.8
PARAMETER top_p 0.9
SYSTEM "You are a helpful coding assistant."
```

Build and run:

```bash
ollama create my-custom-model -f Modelfile
ollama run my-custom-model
```

## API Reference

### Chat Endpoint

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}'
```

### Generate Endpoint

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello!",
  "stream": false
}'
```

### List Models

```bash
curl http://localhost:11434/api/tags
```

## Resources

- Official Documentation: https://ollama.ai/docs
- GitHub Repository: https://github.com/ollama/ollama
- Model Library: https://ollama.ai/library
- Community Discord: https://discord.gg/ollama
