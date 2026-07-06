import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Resolve DB URI after dotenv is loaded
_mysql_host = os.getenv("MYSQL_HOST", "")
_mysql_user = os.getenv("MYSQL_USER", "")
_mysql_password = os.getenv("MYSQL_PASSWORD", "")
_mysql_port = os.getenv("MYSQL_PORT", "3306")
_mysql_db = os.getenv("MYSQL_DATABASE", "financial_advisory")

if _mysql_host and _mysql_user:
    _db_uri = f"mysql+pymysql://{_mysql_user}:{_mysql_password}@{_mysql_host}:{_mysql_port}/{_mysql_db}"
else:
    _db_uri = f"sqlite:///{os.path.join(BASE_DIR, 'financial_advisory.db')}"


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    SQLALCHEMY_DATABASE_URI = _db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False  # Set True in production (HTTPS)
    JWT_COOKIE_CSRF_PROTECT = False

    # AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

    # News
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
