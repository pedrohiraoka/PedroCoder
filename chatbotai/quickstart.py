"""
Quickstart example for ChatBotAI.

This script demonstrates how to quickly set up and use the ChatBotAI
framework with minimal configuration.
"""

import logging
import sys

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from chatbotai.core.engine import ChatBot
from chatbotai.core.ai_engine import OllamaEngine


def main() -> None:
    """Run the quickstart demonstration."""
    print("=" * 60)
    print("ChatBotAI - Quickstart Example")
    print("=" * 60)
    print()

    # Initialize the AI engine (using Ollama with Llama model)
    print("Initializing AI engine...")
    ai_engine = OllamaEngine(
        model_name="llama3.2",  # Default Llama model
        base_url="http://localhost:11434",
    )

    # Check if Ollama is available
    if not ai_engine.is_available():
        print("\nWarning: Ollama server is not available!")
        print("Please ensure Ollama is running:")
        print("  1. Install Ollama from https://ollama.ai")
        print("  2. Pull a model: ollama pull llama3.2")
        print("  3. Start Ollama server")
        print("\nRunning in demo mode without AI responses...\n")

    # Create the chatbot instance
    chatbot = ChatBot(
        ai_engine=ai_engine,
        system_prompt=(
            "You are a helpful assistant. Be concise and friendly."
        ),
    )

    # Register some topic triggers for demonstration
    chatbot.register_topic_trigger(
        topic="greeting",
        pattern=r"\b(hi|hello|hey|greetings)\b",
        confidence=0.7,
    )

    chatbot.register_topic_trigger(
        topic="help",
        pattern=r"\b(help|assist|support)\b",
        confidence=0.7,
    )

    # Create a conversation
    user_id = "demo_user"
    conversation = chatbot.create_conversation(user_id=user_id)
    print(f"Created conversation: {conversation.conversation_id}")
    print()

    # Demo conversation loop
    print("Enter your messages below (type 'quit' to exit):")
    print("-" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("\nAssistant: Goodbye! Have a great day!")
                break

            # Get response from chatbot
            print("\nAssistant: ", end="", flush=True)

            if ai_engine.is_available():
                # Stream the response
                response = ""
                for chunk in chatbot.chat(
                    conversation_id=conversation.conversation_id,
                    message=user_input,
                    stream=True,
                ):
                    print(chunk, end="", flush=True)
                    response += chunk
                print()

                # Optionally learn from this interaction
                chatbot.learn_from_interaction(
                    user_message=user_input,
                    assistant_response=response,
                    feedback_score=1.0,
                )
            else:
                # Demo mode without AI
                response = (
                    f"[Demo Mode] I received your message: '{user_input}'\n"
                    "To enable AI responses, please start Ollama server."
                )
                print(response)

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            logging.exception("Chat error")

    # Show conversation summary
    print("\n" + "=" * 60)
    print("Conversation Summary")
    print("=" * 60)
    history = chatbot.get_conversation_history(conversation.conversation_id)
    print(f"Total messages: {len(history)}")
    print(f"Current topic: {conversation.topic}")
    print()


if __name__ == "__main__":
    main()
