# ChatBotAI

A minimalist and highly extensible AI chatbot framework for Python, designed for local LLM inference with Ollama.

## Features

- **Local AI Inference**: 100% local processing using Ollama with Llama family models
- **Minimal Boilerplate**: Get started with just a few lines of code
- **Extensible Architecture**: Clean separation of concerns with modular components
- **Conversation Management**: Topic-based routing with contextual transitions
- **Memory Systems**: Both volatile (in-memory) and persistent (file-based) storage
- **Function Handlers**: Register custom Python functions for the AI to call
- **API Integrations**: Built-in support for REST API calls with validation
- **Incremental Learning**: Store and learn from conversation interactions
- **Streaming Support**: Real-time response streaming
- **PEP 8 Compliant**: Follows Python best practices throughout

## Installation

### Prerequisites

- Python 3.10 or higher
- Ollama installed and running (see [OLLAMA_SETUP.md](OLLAMA_SETUP.md))

### Quick Install

```bash
# Clone or download the project
cd chatbotai

# Install dependencies
pip install -r requirements.txt

# Pull the default Llama model
ollama pull llama3.2
```

## Quick Start

```python
from chatbotai.core.engine import ChatBot
from chatbotai.core.ai_engine import OllamaEngine

# Initialize the AI engine
ai_engine = OllamaEngine(model_name="llama3.2")

# Create the chatbot
chatbot = ChatBot(ai_engine=ai_engine)

# Create a conversation
conversation = chatbot.create_conversation(user_id="user_123")

# Chat!
response = chatbot.chat(
    conversation_id=conversation.conversation_id,
    message="Hello, how are you?"
)
print(response)
```

### Running the Example

```bash
python quickstart.py
```

## Project Structure

```
chatbotai/
├── __init__.py           # Package initialization
├── quickstart.py         # Quick start example
├── config.yaml           # YAML configuration file
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
├── OLLAMA_SETUP.md       # Ollama setup guide
├── core/
│   ├── __init__.py
│   ├── models.py         # Data models (Message, ConversationContext)
│   ├── ai_engine.py      # AI engine implementations (Ollama)
│   ├── conversation_manager.py  # Conversation flow management
│   └── engine.py         # Main ChatBot orchestrator
├── memory/
│   ├── __init__.py
│   └── backends.py       # Volatile and Persistent memory
├── handlers/
│   ├── __init__.py
│   └── function_handler.py  # Function registration and API integration
├── integrations/
│   └── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py       # Configuration management
├── utils/
│   ├── __init__.py
│   └── helpers.py        # Utility functions
└── tests/
    └── test_core.py      # Unit tests
```

## Configuration

### Using YAML (config.yaml)

```yaml
ollama:
  model_name: llama3.2
  base_url: http://localhost:11434
  temperature: 0.7

memory:
  volatile_enabled: true
  persistent_enabled: false

logging:
  level: INFO
```

### Using Environment Variables

```bash
export CHATBOT_OLLAMA_MODEL=llama3.2
export CHATBOT_OLLAMA_BASE_URL=http://localhost:11434
export CHATBOT_MEMORY_PERSISTENT=false
```

### Programmatic Configuration

```python
from chatbotai.config.settings import ConfigLoader

config = (
    ConfigLoader()
    .load_from_yaml("config.yaml")
    .load_from_env()
    .get_chatbot_config()
)
```

## Advanced Usage

### Topic-Based Routing

```python
# Register topic triggers
chatbot.register_topic_trigger(
    topic="greeting",
    pattern=r"\b(hi|hello|hey)\b",
    confidence=0.8,
)

chatbot.register_topic_trigger(
    topic="technical",
    pattern=r"\b(code|program|debug|error)\b",
    confidence=0.7,
)
```

### Custom Function Handlers

```python
from chatbotai.handlers.function_handler import FunctionHandler

handler = FunctionHandler()

@handler.register(name="get_weather", description="Get weather for a city")
def get_weather(city: str) -> str:
    # Your implementation
    return f"Weather in {city}: Sunny, 25°C"

# Execute the function
result = handler.execute("get_weather", {"city": "São Paulo"})
```

### Streaming Responses

```python
for chunk in chatbot.chat(
    conversation_id=conv_id,
    message="Tell me a story",
    stream=True
):
    print(chunk, end="", flush=True)
```

### Memory Management

```python
from chatbotai.memory.backends import MemoryManager

# Create memory manager with both backends
memory = MemoryManager(
    volatile=True,
    persistent=True,
    storage_path="./my_memory"
)

# Save and load data
memory.save("user_prefs", {"theme": "dark", "lang": "en"})
prefs = memory.load("user_prefs")
```

### Incremental Learning

```python
# Store interaction for learning
chatbot.learn_from_interaction(
    user_message="How do I sort a list?",
    assistant_response="You can use the sorted() function...",
    feedback_score=0.95
)
```

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=chatbotai --cov-report=html
```

## API Reference

### ChatBot Class

| Method | Description |
|--------|-------------|
| `create_conversation(user_id)` | Create a new conversation |
| `chat(conversation_id, message, stream=False)` | Send a message and get response |
| `register_topic_trigger(topic, pattern, handler)` | Register topic detection |
| `get_conversation_history(conversation_id)` | Get full message history |
| `clear_conversation(conversation_id)` | Clear conversation history |
| `delete_conversation(conversation_id)` | Delete a conversation |
| `learn_from_interaction(user_msg, response, score)` | Store for learning |
| `is_ready()` | Check if chatbot is ready |

### OllamaEngine Class

| Method | Description |
|--------|-------------|
| `generate_response(messages, **kwargs)` | Generate a response |
| `generate_stream(messages, **kwargs)` | Stream a response |
| `is_available()` | Check if Ollama is available |
| `list_models()` | List available models |

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama server
ollama serve
```

### Model Not Found

```bash
# Pull the required model
ollama pull llama3.2
```

### Import Errors

```bash
# Ensure you're in the project directory
cd chatbotai

# Install dependencies
pip install -r requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

This project follows PEP 8 guidelines:
- 4 spaces for indentation
- Maximum 79 characters per line
- snake_case for functions and variables
- CamelCase for classes
- ALL_CAPS for constants

Run linting:
```bash
flake8 chatbotai/
black chatbotai/ --check
```

## License

MIT License - See LICENSE file for details.

## Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [Llama Models](https://ollama.ai/library)
- [Python PEP 8](https://peps.python.org/pep-0008/)

## Support

For issues and questions:
1. Check [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for setup help
2. Review existing issues on GitHub
3. Create a new issue with detailed information
