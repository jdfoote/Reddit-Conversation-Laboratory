#!/usr/bin/env python3
"""
Command-line utility for testing bot prompts and having test conversations.

This utility allows researchers to test different GAI models, bot prompts, and
first consented messages in an interactive conversation without needing to
set up the full Reddit chatbot infrastructure.

Usage:
    python test_prompt.py --config config.yaml --output test_conversation.txt
"""

import argparse
import yaml
import json
import logging
from datetime import datetime
import gai_interface

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def load_config(config_file):
    """Load configuration from YAML file."""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_file}")
        exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing config file: {e}")
        exit(1)


def select_from_list(items, prompt_text):
    """
    Present a numbered list to the user and get their selection.
    
    Args:
        items: List of items to choose from
        prompt_text: Text to display as the prompt
        
    Returns:
        Selected item
    """
    print(f"\n{prompt_text}")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")
    
    while True:
        try:
            choice = input(f"\nEnter your choice (1-{len(items)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(items):
                return items[choice_num - 1]
            else:
                print(f"Please enter a number between 1 and {len(items)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            exit(0)


def select_gai_model(config):
    """Let user select a GAI model from the config."""
    all_models = gai_interface.list_available_models(config)
    
    if not all_models:
        logging.error("No GAI models found in config file")
        exit(1)
    
    # Format models for display
    model_displays = [f"{platform}: {model}" for platform, model in all_models]
    selected_display = select_from_list(model_displays, "Select a GAI model:")
    
    # Find the corresponding platform and model
    selected_index = model_displays.index(selected_display)
    return all_models[selected_index]


def select_bot_prompt(config):
    """Let user select a bot prompt from the config."""
    if 'gai_prompt' not in config or not config['gai_prompt']:
        logging.error("No bot prompts found in config file")
        exit(1)
    
    prompts = list(config['gai_prompt'].keys())
    selected_key = select_from_list(prompts, "Select a bot prompt:")
    return selected_key, config['gai_prompt'][selected_key]


def select_first_consented_message(config):
    """Let user select a first consented message from the config."""
    if 'first_consented_message' not in config or not config['first_consented_message']:
        logging.error("No first consented messages found in config file")
        exit(1)
    
    messages = list(config['first_consented_message'].keys())
    selected_key = select_from_list(messages, "Select a first consented message:")
    return selected_key, config['first_consented_message'][selected_key]


def save_conversation(output_file, conversation_data):
    """
    Save the conversation to the output file.
    
    Args:
        output_file: Path to output file
        conversation_data: Dictionary with conversation metadata and messages
    """
    try:
        with open(output_file, 'a') as f:
            f.write("\n" + "="*80 + "\n")
            f.write(f"Conversation at {conversation_data['timestamp']}\n")
            f.write(f"GAI Platform: {conversation_data['gai_platform']}\n")
            f.write(f"GAI Model: {conversation_data['gai_model']}\n")
            f.write(f"Prompt Key: {conversation_data['prompt_key']}\n")
            f.write(f"First Consented Message Key: {conversation_data['first_message_key']}\n")
            f.write("="*80 + "\n\n")
            
            f.write("System Prompt:\n")
            f.write(conversation_data['system_prompt'] + "\n\n")
            
            f.write("Conversation:\n")
            f.write("-"*80 + "\n")
            for message in conversation_data['messages']:
                f.write(f"{message['role'].upper()}: {message['content']}\n")
                f.write("-"*80 + "\n")
            
            f.write("\n")
        logging.info(f"Conversation saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving conversation: {e}")


def have_conversation(gai_platform, gai_model, bot_prompt, first_message, 
                     prompt_key, first_message_key, output_file, config):
    """
    Conduct an interactive conversation with the bot.
    
    Args:
        gai_platform: Platform to use (e.g., 'openai', 'claude')
        gai_model: Model name
        bot_prompt: System prompt/instructions for the bot
        first_message: First message from bot
        prompt_key: Key of the selected prompt in config
        first_message_key: Key of the first message in config
        output_file: Path to save conversation
        config: Configuration dictionary
    """
    print("\n" + "="*80)
    print("Starting conversation. Type 'exit' or 'quit' to end the conversation.")
    print("="*80 + "\n")
    
    # Initialize conversation with first message from bot
    conversation_messages = []
    
    # Display first message
    print(f"BOT: {first_message}\n")
    conversation_messages.append({"role": "assistant", "content": first_message})
    
    # Get max tokens for the model (use config value or default)
    max_tokens = config.get('max_tokens', {}).get(gai_model, gai_interface.DEFAULT_MAX_TOKENS)
    max_interactions = config.get('max_interactions', 50)
    
    interaction_count = 0
    
    while interaction_count < max_interactions:
        # Get user input
        try:
            user_input = input("YOU: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nEnding conversation...")
            break
        
        if not user_input:
            print("Please enter a message.\n")
            continue
        
        if user_input.lower() in ['exit', 'quit']:
            print("\nEnding conversation...")
            break
        
        # Add user message to conversation
        conversation_messages.append({"role": "user", "content": user_input})
        interaction_count += 1
        
        # Get AI response
        print("\nThinking...\n")
        reply = gai_interface.get_ai_reply(
            messages=conversation_messages,
            bot_instructions=bot_prompt,
            gai_platform=gai_platform,
            gai_model=gai_model,
            max_tokens=max_tokens,
            max_interactions=max_interactions,
            goodbye_message=config.get('goodbye_message', 'Thank you for the conversation.'),
            conversation_length=interaction_count
        )
        
        # Display AI response
        print(f"BOT: {reply}\n")
        conversation_messages.append({"role": "assistant", "content": reply})
        
        # Check if this was the goodbye message
        if interaction_count >= max_interactions:
            print("\nMaximum interactions reached. Ending conversation.\n")
            break
    
    # Save the conversation
    conversation_data = {
        'timestamp': datetime.now().isoformat(),
        'gai_platform': gai_platform,
        'gai_model': gai_model,
        'prompt_key': prompt_key,
        'first_message_key': first_message_key,
        'system_prompt': bot_prompt,
        'messages': conversation_messages
    }
    
    save_conversation(output_file, conversation_data)
    
    print(f"\nConversation saved to {output_file}")


def main():
    """Main entry point for the test prompt utility."""
    parser = argparse.ArgumentParser(
        description='Interactive utility for testing bot prompts and conversations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration YAML file (default: config.yaml)'
    )
    parser.add_argument(
        '--output',
        default='test_conversations.txt',
        help='Path to output file for saving conversations (default: test_conversations.txt)'
    )
    parser.add_argument(
        '--log',
        '--loglevel',
        dest='loglevel',
        default='info',
        help='Logging level (default: info)'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(args.loglevel.upper())
    
    print("\n" + "="*80)
    print("Bot Prompt Testing Utility")
    print("="*80)
    
    # Load configuration
    config = load_config(args.config)
    
    # Step 1: Select GAI model
    gai_platform, gai_model = select_gai_model(config)
    print(f"\nSelected: {gai_platform} - {gai_model}")
    
    # Step 2: Select bot prompt
    prompt_key, bot_prompt = select_bot_prompt(config)
    print(f"\nSelected prompt: {prompt_key}")
    
    # Step 3: Select first consented message
    first_message_key, first_message = select_first_consented_message(config)
    print(f"\nSelected first message: {first_message_key}")
    
    # Format the prompt and first message (replace placeholders with generic values)
    # For testing purposes, we use placeholders
    bot_prompt = bot_prompt.format(
        user="[test_user]",
        subreddit_rules="[test subreddit rules]"
    ) if '{' in bot_prompt else bot_prompt
    
    first_message = first_message.format(
        subreddit="[test_subreddit]",
        comment="[test comment]"
    ) if '{' in first_message else first_message
    
    # Step 4: Have the conversation
    have_conversation(
        gai_platform=gai_platform,
        gai_model=gai_model,
        bot_prompt=bot_prompt,
        first_message=first_message,
        prompt_key=prompt_key,
        first_message_key=first_message_key,
        output_file=args.output,
        config=config
    )


if __name__ == '__main__':
    main()
