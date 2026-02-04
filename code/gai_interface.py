"""
GAI (Generative AI) Interface Module

This module provides a reusable interface for interacting with various AI platforms
(OpenAI, Claude) for generating conversational responses. It can be used by both
the main chatbot and the command-line testing utility.
"""

import logging
from openai import OpenAI, BadRequestError
from anthropic import Anthropic
import auth

# Initialize AI clients conditionally based on available API keys
OpenAIClient = None
AnthropicClient = None

if auth.openai_key:
    try:
        OpenAIClient = OpenAI(api_key=auth.openai_key)
        logging.info('OpenAI client initialized successfully')
    except Exception as e:
        logging.warning(f'Failed to initialize OpenAI client: {e}')

if auth.anthropic_key:
    try:
        AnthropicClient = Anthropic(api_key=auth.anthropic_key)
        logging.info('Anthropic client initialized successfully')
    except Exception as e:
        logging.warning(f'Failed to initialize Anthropic client: {e}')


def get_ai_reply(messages, bot_instructions, gai_platform, gai_model, max_tokens=7000, 
                 max_interactions=None, goodbye_message=None, conversation_length=None):
    """
    Get an AI reply from the specified platform and model.
    
    Args:
        messages: List of message dicts with 'role' ('user' or 'assistant') and 'content' (text)
        bot_instructions: System prompt/instructions for the bot
        gai_platform: 'openai' or 'claude'
        gai_model: Model name (e.g., 'gpt-4', 'claude-sonnet-4-5')
        max_tokens: Maximum token limit for the conversation context
        max_interactions: Maximum number of interactions (optional)
        goodbye_message: Message to return when max_interactions is reached (optional)
        conversation_length: Current conversation length for checking max_interactions (optional)
        
    Returns:
        String reply from the AI model, or an error message
    """
    # Check for maximum interactions if provided
    if max_interactions and conversation_length and conversation_length > max_interactions:
        return goodbye_message if goodbye_message else "Thank you for the conversation."
    
    # Calculate message length
    message_len = len(bot_instructions.split())
    for message in messages:
        message_len += len(message['content'].split())
    
    # Check if we've exceeded max tokens
    if message_len > max_tokens:
        if len(messages) == 1:
            return "I'm sorry, but your response is too long. Can you try something shorter?"
        
        # Recursively call with truncated messages
        truncated_messages = messages[1:]
        updated_instructions = bot_instructions + " You are in the middle of a conversation with the user."
        return get_ai_reply(truncated_messages, updated_instructions, gai_platform, gai_model, 
                          max_tokens, max_interactions, goodbye_message, 
                          conversation_length - 1 if conversation_length else None)
    
    # Build final message list with system prompt
    final_messages = [{"role": "system", "content": bot_instructions}] + messages
    
    try:
        if gai_platform == 'openai':
            if OpenAIClient is None:
                logging.error("OpenAI client not initialized. Check OPENAI_API_KEY in .env")
                return "Error occurred."
            response = OpenAIClient.chat.completions.create(
                model=gai_model,
                messages=final_messages)
            reply = response.choices[0].message.content
        
        elif gai_platform == 'claude':
            if AnthropicClient is None:
                logging.error("Anthropic client not initialized. Check ANTHROPIC_API_KEY in .env")
                return "Error occurred."
            # Claude API requires separating system prompt from messages
            claude_messages = [msg for msg in final_messages if msg['role'] != 'system']
            response = AnthropicClient.messages.create(
                model=gai_model,
                max_tokens=1024,
                system=bot_instructions,
                messages=claude_messages)
            reply = response.content[0].text
        
        else:
            logging.error(f"Unknown GAI platform: {gai_platform}")
            return "Error occurred."
    
    except BadRequestError as e:
        logging.warning(f"Got a BadRequestError for {final_messages}. Error is {e}")
        return "I can't figure out how to respond to your message. Could you try again?"
    except Exception as e:
        logging.error(f"Error calling {gai_platform} API: {e}")
        return "I encountered an error and can't figure out how to respond to your message. Could you try again?"
            
    return reply


def list_available_models(config):
    """
    Get a list of all available GAI models from the config.
    
    Args:
        config: Configuration dictionary with 'gai_models' key
        
    Returns:
        List of tuples (platform, model_name)
    """
    all_models = []
    if 'gai_models' in config:
        for platform, models in config['gai_models'].items():
            for model in models:
                all_models.append((platform, model))
    return all_models
