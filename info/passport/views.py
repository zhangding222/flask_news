from datetime import datetime
import random
import re

from flask import current_app,jsonify
from flask import make_response
from flask import request
from flask import session

from info import constants, db
from info import redis_store
from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blu


@passport_blu.route('/image_code')
def get_image_code():
    # 1.获取图片id
    code_id = request.args.get('code_id')
    #生成验证码,三方库生成, [名称,验证码,图片]
    name, text, image = captcha.generate_captcha()
    try:
        # redis 字典格式:key 有效期 value
        redis_store.setex("ImageCode_"+code_id,constants.IMAGE_CODE_REDIS_EXPIRES,text)
        print(name)
        print(text)
    except Exception as e:
        current_app.logger.error(e)
        return make_response(jsonify(errno=RET.DATAERR, errmsg='保存图片失败'))

    # 返回相应内容
    resp = make_response(image)
    resp.headers['Content-Type'] = 'image/jpg'
    return resp


# 根据借口文档获取和使用参数
@passport_blu.route('/smscode',methods=['GET','POST'])
def send_sms():
    """
    1.接收参数判断是否为空
    2.校验手机号码格式
    3.通过id在redis查询验证码是否一致
    4.生成短信验证码进行发送
    5.redis存储短信验证码
    6.相应发送成功状态
    """
    # 获取参数和对应类型获取方式高版本才有json,其他是data
    param_dice = request.json
    mobile = param_dice.get('mobile')
    image_code = param_dice.get('image_code')
    image_code_id = param_dice.get('image_code_id')
    # 判断接收参数是否为空
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    # 判断手机号码格式
    if not re.match("^1[3-9][0-9]{9}$",mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机号不正确")
    #判断图片验证码
    try:
        real_image_code = redis_store.get("ImageCode_"+image_code_id)
        #取出则表示没有报错
        if real_image_code:
            # 进行解码赋值给变量
            real_image_code = real_image_code.decode()
            # 删除redis数据库中的编码
            redis_store.delete("ImageCode_"+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取图片验证码失败")

    if not real_image_code:
        # 判断验证码是否为空
        return jsonify(errno=RET.NODATA, errmsg="验证码已过期")
    if image_code.lower() != real_image_code.lower():
        # 判断验证码是否和服务器的一致
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    try:
        # 判断用户是否已经注册
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR , errmsg='该手机已被注册')

    # 生成随机短信验证码
    result = random.randint(0,999999)
    global sms_code 
    sms_code = "%06d" %result
    current_app.logger.debug('短信验证码内容为:%s' % sms_code)
    # 发送短信,参数为 电话,[内容,有效时间],模式
    result = CCP().send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES / 60],"1")
    if result != 0:
    # 发送失败
	#发短信接口太贵改成显示验证码
        #return jsonify(errno=RET.THIRDERR, errmsg='发送短信失败')
        return jsonify(errno=RET.THIRDERR, errmsg='短信接口太贵系列改为验证特征码:%s' % sms_code)

    #将验证码保存在redis中
    try:
        redis_store.set('SMS_'+mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        jsonify(errno=RET.DBERR ,errmsg='保存验证码失败')

    return jsonify(errno=RET.OK ,errmsg="发送成功")


@passport_blu.route('/register',methods=['POST'])
def register():
    """
    1.获取参数和判断是否正确
    2.从redis获取制指定手机号对应的短信验证码
    3.校验验证码
    4.初始化user模型,并设置数据添加到数据库
    5.保存当前用户状态
    6.返回注册的结果
    :return:
    """

    # 获取并判断是否为空
    json_data = request.json
    mobile = json_data.get("mobile")
    smscode = json_data.get("smscode")
    password = json_data.get("password")
    if smscode != sms_code:
	    return jsonify(erron=RET.DATAERR,errmsg='特征码错误')
	
	#使用验证码的话取消注释
    '''
    if not all([mobile,sms_code,password]):
        return jsonify(erron=RET.PARAMERR ,errmsg="参数不全")

    try:
        real_sms_code = redis_store.get('SMS_'+mobile)
        real_sms_code = real_sms_code.decode()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(erron=RET.DBERR ,errmsg='获取本地验证码失败')

    if not real_sms_code:
        return jsonify(erron=RET.NODATA ,errmsg='短信验证码失效')

    if sms_code != real_sms_code:
        return jsonify(erron=RET.DATAERR,errmsg='短信验证码错误')

    # 删除
    try:
        redis_store.delete("SMS_"+mobile)
    except Exception as e:
        current_app.logger.error(e)
    '''
    # 初始化user模型,设置数据并添加到数据库
    user = User()
    user.nick_name = mobile
    user.mobile = mobile
    # .password对password进行hash加密
    user.password = password
    user.money = 0

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmgs='数据保存错误')

    # from requests import session   函数对象不支持分配
    # from flask import session 成功没有报错.

    session['user_id'] = user.id
    session['nick_code'] = user.nick_name
    session['mobile'] = user.mobile

    return jsonify(errno=RET.OK , errmgs='OK')


@passport_blu.route('/login',methods=["POST"])
def login():
    """
        1.获取参数判断是否为空
        2.数据库查询制定用户
        3.校验密码
        4.保存用户登陆状态
        5.返回结果
    :return:
    """
    json_data = request.json
    mobile = json_data.get("mobile")
    password = json_data.get("password")

    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR ,errmsg="参数不全")
    # 数据库查询用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR ,errmsg='查询数据错误')

    if not user:
        return jsonify(errno=RET.USERERR ,errmsg="用户不存在")

    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR ,errmsg="密码错误")

    # 保存用户登陆状态
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # 最后一次登陆时间
    user.last_login = datetime.now()

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK ,errmsg="OK")

# 退出登陆
# 默认简写的ajax方法,方法名确定请求方式
@passport_blu.route('/logout')
# @passport_blu.route("/logout",methods=["POST"])
def logout():
    session.pop("user_id",None)
    session.pop("nick_name",None)
    session.pop("mobile",None)
    # 退出时清理管理员的信息
    session.pop('is_admin',None)
    return jsonify(errno=RET.OK ,errmsg="OK")
	
	


