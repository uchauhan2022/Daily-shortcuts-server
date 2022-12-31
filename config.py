"""Flask configuration."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))


class Config:
    """Set Flask config variables."""

    FLASK_ENV = "development"
    TESTING = True
    DEBUG = True
    SECRET_KEY = environ.get("SECRET_KEY")

    """
    Energia Electricity Credentials
    """
    USERNAME_ENERGIA = environ.get("USERNAME_ENERGIA")
    PASSWORD_ENERGIA = environ.get("PASSWORD_ENERGIA")
    MPRN_HASH = environ.get("MPRN_HASH")

    """
    Pushover keys
    """
    PUSHOVER_KEY = environ.get("PUSHOVER_KEY")
    PUSHOVER_TOKEN = environ.get("PUSHOVER_TOKEN")
