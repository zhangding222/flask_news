import redis
import logging

class Config:
    # DEBUG = True
    # MySQL配置信息
    SQLALCHEMY_DATABASE_URI = "mysql://root:123456@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = "True"
    # Rdis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'
    #配置Session
    # session的密钥配置
    SECRET_KEY = 'test'
    # session保存再redis中
    SESSION_TYPE = 'redis'
    # id签名加密
    SESSION_USE_SIGNER = True
    # Session的Redis对象
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    # 有效期(秒)
    PERMANENT_SESSION_LIFETIME = 86400
    LOG_LEVEL = logging.DEBUG
    WTF_CSRF_ENABLED = False


# 针对与开发环境和正式环境的分别
class DevelopementConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    LOG_LEVEL = logging.ERROR


config={
    "development":DevelopementConfig,
    "production":ProductionConfig
}