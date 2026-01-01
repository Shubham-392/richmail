import os
from dotenv import load_dotenv
from argon2 import PasswordHasher

# Load environment variables from .env file
load_dotenv()

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
JWT_ACCESS_TOKEN_LIFETIME = 60 # in minutes
JWT_REFRESH_TOKEN_LIFETIME = 1440 # in minutes (24 hours)

hasher = PasswordHasher()