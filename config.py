import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
