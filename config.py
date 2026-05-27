import os

class Config:
    # ------------------------------------------------------------------ #
    #  Flask
    # ------------------------------------------------------------------ #
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'

    # ------------------------------------------------------------------ #
    #  Database — XAMPP MySQL
    # ------------------------------------------------------------------ #
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     '127.0.0.1')
    MYSQL_PORT     = os.environ.get('MYSQL_PORT',     '3307')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'pediacare_db')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------ #
    #  Email — pick ONE provider below, fill in your credentials
    #
    #  OPTION A: Gmail
    #    MAIL_USERNAME = 'yourname@gmail.com'
    #    MAIL_PASSWORD = 'xxxx xxxx xxxx xxxx'  ← 16-char App Password
    #    (Get at: myaccount.google.com → Security → App passwords)
    #
    #  OPTION B: Outlook / Hotmail (recommended if Gmail SMTP is blocked)
    #    MAIL_USERNAME = 'yourname@outlook.com'
    #    MAIL_PASSWORD = 'your_outlook_password'
    #    (Enable SMTP at: outlook.com → Settings → Mail → Sync email)
    #
    #  OPTION C: Yahoo Mail
    #    MAIL_USERNAME = 'yourname@yahoo.com'
    #    MAIL_PASSWORD = 'xxxx xxxx xxxx xxxx'  ← Yahoo App Password
    #    (Get at: account.yahoo.com → Security → App passwords)
    # ------------------------------------------------------------------ #
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'tugasjerwin7@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'lufa sqdo xgao ithb')
    MAIL_FROM     = os.environ.get('MAIL_USERNAME', 'tugasjerwin7@gmail.com')

    # ------------------------------------------------------------------ #
    #  Clinic info
    # ------------------------------------------------------------------ #
    CLINIC_NAME    = 'Napalinga\'s Children Clinic'
    CLINIC_ADDRESS = 'Meycauayan Bulacan'
    CLINIC_PHONE   = '09123456789'