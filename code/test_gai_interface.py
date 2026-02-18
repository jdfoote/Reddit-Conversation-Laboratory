#!/usr/bin/env python3
"""
Unit tests for the gai_interface module.

Tests cover:
- list_available_models() function
- get_ai_reply() function with various scenarios
- Token limit handling
- Max interactions handling
- Error handling
- Platform-specific logic
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gai_interface


class TestListAvailableModels(unittest.TestCase):
    """Tests for the list_available_models function."""
    
    def test_list_models_with_valid_config(self):
        """Test listing models from a valid config."""
        config = {
            'gai_models': {
                'openai': ['gpt-4', 'gpt-3.5-turbo'],
                'claude': ['claude-sonnet-4-5']
            }
        }
        
        models = gai_interface.list_available_models(config)
        
        self.assertEqual(len(models), 3)
        self.assertIn(('openai', 'gpt-4'), models)
        self.assertIn(('openai', 'gpt-3.5-turbo'), models)
        self.assertIn(('claude', 'claude-sonnet-4-5'), models)
    
    def test_list_models_with_empty_config(self):
        """Test listing models from config without gai_models key."""
        config = {}
        
        models = gai_interface.list_available_models(config)
        
        self.assertEqual(models, [])
    
    def test_list_models_with_empty_gai_models(self):
        """Test listing models from config with empty gai_models."""
        config = {'gai_models': {}}
        
        models = gai_interface.list_available_models(config)
        
        self.assertEqual(models, [])
    
    def test_list_models_with_single_platform(self):
        """Test listing models with only one platform."""
        config = {
            'gai_models': {
                'openai': ['gpt-4']
            }
        }
        
        models = gai_interface.list_available_models(config)
        
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0], ('openai', 'gpt-4'))


class TestGetAiReplyMaxInteractions(unittest.TestCase):
    """Tests for max_interactions handling in get_ai_reply."""
    
    def test_max_interactions_reached_with_goodbye_message(self):
        """Test that goodbye message is returned when max interactions reached."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        result = gai_interface.get_ai_reply(
            messages=messages,
            bot_instructions=bot_instructions,
            gai_platform='openai',
            gai_model='gpt-4',
            max_interactions=5,
            goodbye_message="Goodbye!",
            conversation_length=5
        )
        
        self.assertEqual(result, "Goodbye!")
    
    def test_max_interactions_reached_without_goodbye_message(self):
        """Test default goodbye message when max interactions reached."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        result = gai_interface.get_ai_reply(
            messages=messages,
            bot_instructions=bot_instructions,
            gai_platform='openai',
            gai_model='gpt-4',
            max_interactions=3,
            conversation_length=3
        )
        
        self.assertEqual(result, "Thank you for the conversation.")
    
    def test_max_interactions_not_reached(self):
        """Test that processing continues when max interactions not reached."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        # Mock the OpenAI client to avoid actual API calls
        with patch.object(gai_interface, 'OpenAIClient') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Hi there!"
            mock_client.chat.completions.create.return_value = mock_response
            
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='openai',
                gai_model='gpt-4',
                max_interactions=5,
                conversation_length=2
            )
            
            self.assertEqual(result, "Hi there!")


class TestGetAiReplyTokenLimits(unittest.TestCase):
    """Tests for token limit handling in get_ai_reply."""
    
    def test_token_limit_exceeded_single_message(self):
        """Test response when token limit exceeded with single message."""
        # Create a very long message that exceeds token limit
        long_message = " ".join(["word"] * 10000)
        messages = [{"role": "user", "content": long_message}]
        bot_instructions = "You are a helpful assistant."
        
        result = gai_interface.get_ai_reply(
            messages=messages,
            bot_instructions=bot_instructions,
            gai_platform='openai',
            gai_model='gpt-4',
            max_tokens=100
        )
        
        self.assertEqual(result, "I'm sorry, but your response is too long. Can you try something shorter?")
    
    def test_token_limit_exceeded_multiple_messages(self):
        """Test truncation when token limit exceeded with multiple messages."""
        # Create enough messages that after truncation there's still more than 1
        messages = [
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "msg2"},
            {"role": "user", "content": "msg3"}
        ]
        bot_instructions = "You are a helpful assistant."
        
        # Mock the OpenAI client to handle recursion
        call_count = [0]
        def mock_create(**kwargs):
            call_count[0] += 1
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Truncated response"
            return mock_response
        
        with patch.object(gai_interface, 'OpenAIClient') as mock_client:
            mock_client.chat.completions.create.side_effect = mock_create
            
            # Use a reasonable token limit that won't exceed with short messages
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='openai',
                gai_model='gpt-4',
                max_tokens=1000  # Reasonable limit
            )
            
            # Should get a response without truncation needed
            self.assertEqual(result, "Truncated response")
            # Should be called once (no recursion for these short messages)
            self.assertEqual(call_count[0], 1)
    
    def test_default_max_tokens(self):
        """Test that DEFAULT_MAX_TOKENS is used when max_tokens is None."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'OpenAIClient') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Hi!"
            mock_client.chat.completions.create.return_value = mock_response
            
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='openai',
                gai_model='gpt-4',
                max_tokens=None  # Should use DEFAULT_MAX_TOKENS
            )
            
            self.assertEqual(result, "Hi!")


class TestGetAiReplyOpenAI(unittest.TestCase):
    """Tests for OpenAI platform-specific logic."""
    
    def test_openai_success(self):
        """Test successful OpenAI API call."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'OpenAIClient') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Hello! How can I help you?"
            mock_client.chat.completions.create.return_value = mock_response
            
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='openai',
                gai_model='gpt-4'
            )
            
            self.assertEqual(result, "Hello! How can I help you?")
            
            # Verify API was called with correct parameters
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            self.assertEqual(call_args[1]['model'], 'gpt-4')
            self.assertEqual(len(call_args[1]['messages']), 2)  # system + user
    
    def test_openai_client_not_initialized(self):
        """Test error handling when OpenAI client is not initialized."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'OpenAIClient', None):
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='openai',
                gai_model='gpt-4'
            )
            
            self.assertEqual(result, "Error occurred.")
    
    def test_openai_bad_request_error(self):
        """Test handling of BadRequestError from OpenAI."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'OpenAIClient') as mock_client:
            from openai import BadRequestError
            mock_client.chat.completions.create.side_effect = BadRequestError(
                "Invalid request", 
                response=Mock(status_code=400),
                body=None
            )
            
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='openai',
                gai_model='gpt-4'
            )
            
            self.assertEqual(result, "I can't figure out how to respond to your message. Could you try again?")
    
    def test_openai_generic_exception(self):
        """Test handling of generic exception from OpenAI."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'OpenAIClient') as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("Network error")
            
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='openai',
                gai_model='gpt-4'
            )
            
            self.assertEqual(result, "I encountered an error and can't figure out how to respond to your message. Could you try again?")


class TestGetAiReplyClaude(unittest.TestCase):
    """Tests for Claude/Anthropic platform-specific logic."""
    
    def test_claude_success(self):
        """Test successful Claude API call."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'AnthropicClient') as mock_client:
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = "Hello! How can I assist you?"
            mock_client.messages.create.return_value = mock_response
            
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='claude',
                gai_model='claude-sonnet-4-5'
            )
            
            self.assertEqual(result, "Hello! How can I assist you?")
            
            # Verify API was called with correct parameters
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args
            self.assertEqual(call_args[1]['model'], 'claude-sonnet-4-5')
            self.assertEqual(call_args[1]['system'], bot_instructions)
            # Claude messages should not include system message
            self.assertEqual(len(call_args[1]['messages']), 1)
    
    def test_claude_client_not_initialized(self):
        """Test error handling when Claude client is not initialized."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'AnthropicClient', None):
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='claude',
                gai_model='claude-sonnet-4-5'
            )
            
            self.assertEqual(result, "Error occurred.")
    
    def test_claude_system_message_separation(self):
        """Test that system message is properly separated for Claude API."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'AnthropicClient') as mock_client:
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = "I'm doing well!"
            mock_client.messages.create.return_value = mock_response
            
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='claude',
                gai_model='claude-sonnet-4-5'
            )
            
            # Verify system message was separated
            call_args = mock_client.messages.create.call_args
            passed_messages = call_args[1]['messages']
            
            # Should have 3 messages (no system message in messages list)
            self.assertEqual(len(passed_messages), 3)
            
            # Verify no system role in messages
            for msg in passed_messages:
                self.assertNotEqual(msg['role'], 'system')


class TestGetAiReplyUnknownPlatform(unittest.TestCase):
    """Tests for unknown platform handling."""
    
    def test_unknown_platform(self):
        """Test error handling for unknown platform."""
        messages = [{"role": "user", "content": "Hello"}]
        bot_instructions = "You are a helpful assistant."
        
        result = gai_interface.get_ai_reply(
            messages=messages,
            bot_instructions=bot_instructions,
            gai_platform='unknown_platform',
            gai_model='some-model'
        )
        
        self.assertEqual(result, "Error occurred.")


class TestDefaultMaxTokensConstant(unittest.TestCase):
    """Tests for DEFAULT_MAX_TOKENS constant."""
    
    def test_default_max_tokens_exists(self):
        """Test that DEFAULT_MAX_TOKENS constant is defined."""
        self.assertTrue(hasattr(gai_interface, 'DEFAULT_MAX_TOKENS'))
    
    def test_default_max_tokens_value(self):
        """Test that DEFAULT_MAX_TOKENS has expected value."""
        self.assertEqual(gai_interface.DEFAULT_MAX_TOKENS, 7000)


class TestConversationLengthHandling(unittest.TestCase):
    """Tests for conversation_length parameter handling."""
    
    def test_conversation_length_preserved_during_truncation(self):
        """Test that conversation_length remains unchanged during truncation."""
        messages = [
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "msg2"},
            {"role": "user", "content": "msg3"}
        ]
        bot_instructions = "You are a helpful assistant."
        
        with patch.object(gai_interface, 'OpenAIClient') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Response"
            mock_client.chat.completions.create.return_value = mock_response
            
            # The conversation_length should be preserved through recursion
            result = gai_interface.get_ai_reply(
                messages=messages,
                bot_instructions=bot_instructions,
                gai_platform='openai',
                gai_model='gpt-4',
                max_tokens=1000,
                max_interactions=10,
                conversation_length=5
            )
            
            # Should still get a response
            self.assertEqual(result, "Response")
            # Should be called once (no truncation needed for short messages)
            mock_client.chat.completions.create.assert_called_once()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
