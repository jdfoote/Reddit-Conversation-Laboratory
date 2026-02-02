import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Reddit API credentials
client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
username = os.getenv('REDDIT_USERNAME')
password = os.getenv('REDDIT_PASSWORD')
u_agent = os.getenv('REDDIT_USER_AGENT')

# OpenAI API key
openai_key = os.getenv('OPENAI_API_KEY')

# Anthropic API key
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

# Perspective API key
perspective_api_key = os.getenv('PERSPECTIVE_API_KEY')
