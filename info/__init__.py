from flask import Flask
from flask import g
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_session import Session
# 使用参数调用
from config import config

import logging
from logging.handlers import RotatingFileHandler
from flask_wtf.csrf import generate_csrf, CSRFProtect

# app.config.from_object(Config)
# # MySQL数据库对象
# db = SQLAlchemy(app)
# # Redis数据库配置/存储图片等资料
# redis_store = redis.StrictRedis(host=Config.REDIS_HOST,port=Config.REDIS_PORT)
# # CSRF攻击预防
# CSRFProtect(app)
# Session(app)


db = SQLAlchemy()
redis_store = None
def create_app(config_name):

    DEBUG = True
    # 配置日志
    setup_log(config_name)
    # 创建Flask对象
    app = Flask(__name__)
    # 使用下列方法替代上列信息
    app.config.from_object(config[config_name])
    db.init_app(app)

    global  redis_store
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST,port=config[config_name].REDIS_PORT)


    CSRFProtect(app)
    # 原本的Session存储在内存中,此时配置完后可以存放在redis中
    Session(app)

    # 首页
    from info.index import index_blue
    app.register_blueprint(index_blue)

    # 登录注册
    from info.passport import passport_blu
    app.register_blueprint(passport_blu)

    # 添加过滤器,使用是调用名称
    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class,"index_class")

    # 新闻页面
    from info.news import news_blue
    app.register_blueprint(news_blue)

    # 个人中心
    from info.user import profile_blu
    app.register_blueprint(profile_blu)

    # 管理员后台
    from info.admin import admin_blu
    app.register_blueprint(admin_blu)

    @app.after_request
    def after_request(response):
        csrf_token = generate_csrf()
        # 将csrf对象存储在cookie中
        response.set_cookie("csrf_token" , csrf_token)
        # print("Cookie:%s " %csrf_token)
        return response

    from info.utils.common import user_login_data
    @app.errorhandler(404)
    @user_login_data
    def page_not_found(error):
        user = g.user
        data = {
            "user_info": user.to_dict() if user else None,

        }
        return render_template('news/404.html', data=data)

    return app

def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)