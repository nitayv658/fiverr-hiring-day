import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'postgresql://user:password@localhost:5432/fiverr_test'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
