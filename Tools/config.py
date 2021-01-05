import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    

