# Unit Tests for gai_interface Module

This directory contains unit tests for the `gai_interface.py` module.

## Running Tests

To run the tests, use Python's built-in unittest module:

```bash
cd code
python3 test_gai_interface.py
```

For verbose output:

```bash
python3 test_gai_interface.py -v
```

## Test Coverage

The test suite covers the following areas:

### list_available_models()
- Valid config with multiple platforms and models
- Empty config
- Empty gai_models dictionary
- Single platform configuration

### get_ai_reply() - Max Interactions
- Max interactions reached with custom goodbye message
- Max interactions reached with default goodbye message
- Max interactions not reached (processing continues)

### get_ai_reply() - Token Limits
- Token limit exceeded with single message
- Token limit exceeded with multiple messages (truncation)
- Default max_tokens value usage

### get_ai_reply() - OpenAI Platform
- Successful API call
- Client not initialized error handling
- BadRequestError handling
- Generic exception handling

### get_ai_reply() - Claude/Anthropic Platform
- Successful API call
- Client not initialized error handling
- System message separation (Claude-specific)

### get_ai_reply() - Error Cases
- Unknown platform handling

### Constants
- DEFAULT_MAX_TOKENS constant existence and value

### Edge Cases
- Conversation length preservation during truncation

## Test Framework

Tests use Python's built-in `unittest` module with `unittest.mock` for mocking external dependencies (OpenAI and Anthropic API clients).

## Mock Strategy

- All API calls are mocked to avoid requiring actual API keys
- Client initialization is mocked when testing error conditions
- API responses are mocked with appropriate structure for each platform

## Dependencies

No additional dependencies are required beyond what's already in the project:
- Python 3.x standard library (unittest, unittest.mock)
- openai (for types/exceptions)
- anthropic (for types)
- gai_interface module being tested

## Adding New Tests

When adding new functionality to `gai_interface.py`, please add corresponding tests:

1. Create a new test class inheriting from `unittest.TestCase`
2. Name test methods starting with `test_`
3. Use descriptive docstrings
4. Mock external dependencies appropriately
5. Test both success and error paths

Example:

```python
class TestNewFeature(unittest.TestCase):
    """Tests for the new feature."""
    
    def test_feature_success(self):
        """Test successful execution of the feature."""
        # Test implementation
        pass
    
    def test_feature_error_handling(self):
        """Test error handling in the feature."""
        # Test implementation
        pass
```
