import os

class Config:
    # ------------------------------------------------------------------ #
    #  Flask
    # ------------------------------------------------------------------ #
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'

    # ------------------------------------------------------------------ #
    #  Database — XAMPP MySQL
    #  Format: mysql+pymysql://user:password@host:port/database_name
    # ------------------------------------------------------------------ #
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')          # XAMPP default = no password
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     '127.0.0.1')
    MYSQL_PORT     = os.environ.get('MYSQL_PORT',     '3307')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'pediacare_db')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------ #
    #  SMS — Semaphore (https://semaphore.co)
    #  Sign up for a free account, get your API key, set it below.
    # ------------------------------------------------------------------ #
    SEMAPHORE_API_KEY    = os.environ.get('SEMAPHORE_API_KEY', 'YOUR_SEMAPHORE_API_KEY')
    SEMAPHORE_SENDER     = os.environ.get('SEMAPHORE_SENDER',  'PediaCare')
    SEMAPHORE_API_URL    = 'https://api.semaphore.co/api/v4/messages'

    # ------------------------------------------------------------------ #
    #  Clinic info (used in SMS messages)
    # ------------------------------------------------------------------ #
    CLINIC_NAME    = 'PediaCare Clinic'
    CLINIC_ADDRESS = 'Your Clinic Address Here'
    CLINIC_PHONE   = 'Your Clinic Phone Here'