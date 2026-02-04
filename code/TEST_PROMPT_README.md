# Command-Line Utility for Bot Prompt Testing

The `test_prompt.py` utility allows researchers to test different GAI models, bot prompts, and first consented messages in an interactive conversation without needing to set up the full Reddit chatbot infrastructure.

## Setup

1. Make sure you have the required API keys in your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

2. Ensure you have a valid `config.yaml` file with:
   - `gai_models`: Dictionary of available AI platforms and models
   - `gai_prompt`: Dictionary of bot prompts
   - `first_consented_message`: Dictionary of first messages
   - `max_tokens`: Token limits for models (optional)
   - `max_interactions`: Maximum number of conversation turns (optional)
   - `goodbye_message`: Message when conversation ends (optional)

## Usage

Basic usage with default config and output file:
```bash
python test_prompt.py
```

Specify a custom config file and output file:
```bash
python test_prompt.py --config my_config.yaml --output my_conversations.txt
```

Enable debug logging:
```bash
python test_prompt.py --log debug
```

## Interactive Flow

When you run the utility, it will:

1. **Select a GAI model** - Choose from a numbered list of available models (e.g., OpenAI GPT-4, Claude)
2. **Select a bot prompt** - Choose from a numbered list of system prompts that define the bot's behavior
3. **Select a first consented message** - Choose from a numbered list of opening messages
4. **Have a conversation** - Chat interactively with the bot:
   - Type your messages and press Enter
   - The bot will respond based on your selected configuration
   - Type `exit` or `quit` to end the conversation
   - Press Ctrl+C to abort at any time

5. **Save the conversation** - The complete conversation (including metadata) is appended to the output file

## Output Format

Each conversation is saved in the output file with:
- Timestamp
- GAI platform and model used
- Prompt key and first message key selected
- Complete system prompt
- Full conversation history with speaker labels (USER/BOT)

Example output:
```
================================================================================
Conversation at 2024-01-15T10:30:00.123456
GAI Platform: openai
GAI Model: gpt-4
Prompt Key: prompt_1
First Consented Message Key: first_consented_1
================================================================================

System Prompt:
Context: You are a chatbot designed by a team of researchers...

Conversation:
--------------------------------------------------------------------------------
ASSISTANT: Thank you for agreeing to chat with me...
--------------------------------------------------------------------------------
USER: Hello, I'd like to discuss...
--------------------------------------------------------------------------------
ASSISTANT: Great! Let me address that...
--------------------------------------------------------------------------------
```

## Module Structure

The utility is built on two key modules:

### `gai_interface.py`
A reusable module for interacting with various AI platforms (OpenAI, Claude). It provides:
- `get_ai_reply()`: Get responses from AI models
- `list_available_models()`: List available models from config
- Handles API client initialization and error handling

This module is used by both `test_prompt.py` and `chatbot.py`.

### `test_prompt.py`
The command-line interface that:
- Loads configuration
- Presents interactive menus
- Manages conversation flow
- Saves conversations to file

## Notes

- The utility does not require Reddit API credentials (unlike the full chatbot)
- Conversations are self-contained and don't affect the main chatbot's state
- Multiple test conversations can be run and saved to the same output file
- Placeholder values are used for template variables (e.g., `{subreddit}`, `{comment}`)
