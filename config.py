"""Configuration module. Should give correct values for 'SECRET_KEY' and 'TOKEN'."""
import os
import secrets

API = "https://api.vk.com/method"
V = 5.131

SECRET_KEY = secrets.token_urlsafe(16)
TOKEN = os.environ.get("VK_API_TOKEN")
