import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'postgresql://user:password@localhost:5432/fiverr_test'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
