import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'
    SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost:5432/healthcare_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False