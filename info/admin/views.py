
import time
from datetime import datetime, timedelta

from flask import current_app
from flask import g
from flask import redirect
from flask import render_template, jsonify
from flask import request
from flask import session
from flask import url_for

from info import constants, db
from info.models import User, News, Category,Tixian,Tuisong
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blu

@admin_blu.route('/add_category',methods=["GET","POST"])
def add_category():
    category_id = request.json.get("id")
    category_name = request.json.get("name")
    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 判断是否有分类id
    if category_id:
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not category:
            return jsonify(errno=RET.NODATA, errmsg="未查询到分类信息")

        category.name = category_name
    else:
        # 如果没有分类id，则是添加分类
        category = Category()
        category.name = category_name
        db.session.add(category)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    return jsonify(errno=RET.OK, errmsg="保存数据成功")





@admin_blu.route('/news_type')
def get_news_category():
    # 获取所有的分类数据
    categories = Category.query.all()
    #保存分类数据
    categories_dicts = []

    for category in categories:
        #获取字典
        cate_dict = category.to_dict()
        #内容拼接
        categories_dicts.append(cate_dict)

    categories_dicts.pop(0)
    data = {
        "categories":categories_dicts
    }
    #返回内容
    return render_template('admin/news_type.html',data =data)
    
@admin_blu.route('/delete_category')
def delete_category():
    key=request.args.get("key")
    user = Category.query.filter(Category.id == key).first()
    db.session.delete(user)
    db.session.commit()
    # 获取所有的分类数据
    categories = Category.query.all()
    #保存分类数据
    categories_dicts = []

    for category in categories:
        #获取字典
        cate_dict = category.to_dict()
        #内容拼接
        categories_dicts.append(cate_dict)

    categories_dicts.pop(0)
    data = {
        "categories":categories_dicts
    }
    #返回内容

    return render_template('admin/news_type.html',data =data)

#删除
@admin_blu.route('/delete/<int:news_id>')
def delete(news_id):
    new = News.query.get(news_id)
    # 2.删除
    db.session.delete(new)
    db.session.commit()

    # 3. 重定向展示界面
    #return redirect(url_for('admin.admin_index'))
    page = request.args.get('p',1)
    keywords = request.args.get('keywords',"")
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    try:
        filters = []
        # 是否有关键词
        if keywords:
            # 添加查询条件
            filters.append(News.title.contains(keywords))
    # 分页查询
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page,constants.ADMIN_NEWS_PAGE_MAX_COUNT,False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 字典形式存储
    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    data = {
        "total_page":total_page,
        "current_page":current_page,
        "news_list":news_dict_list
    }
    return render_template('admin/news_edit.html',data = data)
  


@admin_blu.route('/news_edit_detail',methods=['GET','POST'])
def news_edit_detail():
    """新闻编辑详情"""
    #获取参数
    if request.method == 'GET':
        news_id = request.args.get("news_id")

        if not news_id:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

        # 查询新闻
        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)

        if not news:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

        # 查询分类的数据
        categories = Category.query.all()
        categories_li = []
        for category in categories:
            c_dict = category.to_dict()
            # 判断是否有对应的数据
            c_dict["is_selected"] =False
            if category.id == news.category_id:
                c_dict["is_selected"] = True
            categories_li.append(c_dict)
        categories_li.pop(0)

        data = {
            "news":news.to_dict(),
            "categories":categories_li
        }

        return render_template('admin/news_edit_detail.html',data=data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    print("213213213213")
    print(index_image)
    category_id = request.form.get("category_id")

    if not all([title,digest,content,category_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='参数错误')

    if index_image:
        try:
            index_image = index_image.read()
        except Exception as e:
            return jsonify(errno=RET.PARAMERR, errmsg="图片参数有误")

    #上传图片给七牛云
    print("test")
    print(index_image)
    if index_image is None:
        print("该图片")
        news.title = title
        news.digest = digest
        news.content = content
        news.category_id = category_id
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR,errmsg='数据保存失败')

        return jsonify(errno=RET.OK,errmsg="编辑成功")
    else:
        print("不该图片")
        try:
            key = storage(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR,errmsg="上传图片错误")
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        news.title = title
        news.digest = digest
        news.content = content
        news.category_id = category_id
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR,errmsg='数据保存失败')

        return jsonify(errno=RET.OK,errmsg="编辑成功")
	
'''
    try:
        key = storage(index_image)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="上传图片错误")
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key

    # 设置相关数据
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id

    # 保存至数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='数据保存失败')

    return jsonify(errno=RET.OK,errmsg="编辑成功")
'''




@admin_blu.route('/news_edit')
def news_edit():
    """返回新闻列表"""
    page = request.args.get('p',1)
    keywords = request.args.get('keywords',"")
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    try:
        filters = []
        # 是否有关键词
        if keywords:
            # 添加查询条件
            filters.append(News.title.contains(keywords))
    # 分页查询
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page,constants.ADMIN_NEWS_PAGE_MAX_COUNT,False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 字典形式存储
    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    data = {
        "total_page":total_page,
        "current_page":current_page,
        "news_list":news_dict_list
    }
    return render_template('admin/news_edit.html',data = data)


@admin_blu.route('/news_review_detail',methods=["GET","POST"])
def news_review_detail():
    """ 新闻审核 """
    # 如果是get请求，则显示基础页面，图过是POST提交则走下面逻辑
    if request.method == "GET":
        news_id = request.args.get('news_id')
        news = News.query.get(news_id)
        data = {
            "news": news.to_dict()
        }
        return render_template('admin/news_review_detail.html',data=data)

    # 1.审核操作
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    # 2.判断参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数为空')
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 3.查询新闻
    news = None
    try:
        # 查询当前新闻详情
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        data = {
            "errmsg": "未查询到此新闻"
        }
    if not news:
        return render_template('admin/news_review_detail.html',data)
    # 4.不同状态不同的值
    if action == 'accept':
        news.status = 0
        page =  request.args.get("p",1)
        print("aaaaaaaaaaaaaaaaaa")
        user = User.query.filter(User.id == news.user.id).first()
        paginate =  user.followers.paginate(page,4,False)
        items =  paginate.items
        print(items)
        for item in items:
            tuisong =Tuisong()
            tuisong.user_id = item.id
            tuisong.tuisong =  "%s发布了新闻：%s.点击查看" % (user.nick_name,news.title)

            tuisong.news_id = news.id
            db.session.add(tuisong)
            db.session.commit()
        #fans =  BaseModel.query.filter(BaseModel.follower_id == user.id).first()
        #print(fans)
    else:
        #拒绝通过
        reason = request.json.get('reason')
        if not reason:
            return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
        news.reason = reason
        news.status = -1
    # 将结果保存至数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='数据保存失败')
    return jsonify(errno=RET.OK,errmsg='操作成功')


@admin_blu.route('/news_review')
def news_review():
    # 返回待审和新闻列表
    page = request.args.get('p',1)
    # 获取 搜索参数
    keywords = request.args.get('keywords',"")
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    try:
        # 增加搜索条件，如果有则增加，没有则跳过
        filters = [News.status != 0]
        if keywords:
            filters.append(News.title.contains(keywords))

        # 显示审核通过或者未审核，且按照创建时间显示前10条数据，并分页
        paginate = News.query.filter(*filters)\
            .order_by(News.create_time.desc())\
            .paginate(page,constants.ADMIN_NEWS_PAGE_MAX_COUNT,False)
        # 内容
        news_list = paginate.items
        # 当前页码
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        # 该字典有前端需求数据结构
        news_dict_list.append(news.to_review_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_list": news_dict_list
    }
    return render_template('admin/news_review.html',data = data)




@admin_blu.route('/user_list')
def user_list():
    #获取用户列表

    #页码
    page = request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    #设置变量默认值
    users = []
    current_page = 1
    total_page = 1

    #查询数据，并且分页以及倒序最后登录时间
    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        # paginate = User.query.filter(User.is_admin==False).order_by(User.last_login.desc()).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    user_list = []
    for user in users:
        # 过滤获取需要的参数
        user_list.append(user.to_admin_dict())

    data = {
        "total_page":total_page,
        "current_page":current_page,
        "users": user_list
    }

    return render_template('admin/user_list.html',data = data)


@admin_blu.route('/user_count')
# 用户统计
def user_count():
    # 总人数
    total_count = 0

    try:
        total_count = User.query.filter(User.is_admin==False).count()
    except Exception as e:
        current_app.logger.error(e)
    # 月新增数
    mon_count = 0
    try:
        # 获取当前时间
        now = time.localtime()
        # 按照格式进行时间转换为String
        mon_begin = '%d-%02d-01' %(now.tm_year, now.tm_mon)
        # 获取本月的起始时间
        mon_begin_date = datetime.strptime(mon_begin,'%Y-%m-%d')
        # 查询本月创建的用户人数
        mon_count = User.query.filter(User.is_admin == False,User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

#     查询日新增数
    day_count = 0
    try:
        day_begin = '%d-%02d-%02d' %(now.tm_year,now.tm_mon,now.tm_mday)
        # 将时间转换为字符串格式
        day_begin_data = datetime.strptime(day_begin,'%Y-%m-%d')
        # 查询当天的新增用户人数
        day_count = User.query.filter(User.is_admin == False,User.create_time>day_begin_data).count()
    except Exception as e:
        current_app.logger.error(e)

#     查询图表信息
#     获取当天时间
    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'),'%Y-%m-%d')
#     建立变量存储时间
    active_date = []
    active_count = []

#     循环查询之前没有天的人数，进行显示
    for i in range(0,31):
        # 获取当天时间00.00.00--23.59.59
        # 因为是以当前天向前推算，所以是今天的时间0开始，明天的0接受，所以是i-1
        begin_date = now_date - timedelta(days=i)
        end_date = now_date - timedelta(days=i-1)
        # 时间格式转换,并添加进数据库
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        count=0
        try:
            # User表查询用户创建时间的数量，去除admin
            count = User.query.filter(User.is_admin == False,User.last_login>=begin_date,User.last_login<=end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        #     每次查询当天存储在列表中
        active_count.append(count)

    #倒序进行传递和显示
    active_date.reverse()
    active_count.reverse()

    # 按照前端显示进行赋值
    data={
        "total_count":total_count,
        "mon_count":mon_count,
        "day_count":day_count,
        "active_date":active_date,
        "active_count":active_count
    }

    return render_template('admin/user_count.html',data = data)





@admin_blu.route('/login',methods=['GET','POST'])
def admin_login():
    if request.method == "GET":
        # user = g.user
        # 获取当前登录用户信息和是设置默认值
        user_id = session.get('user_id',None)
        is_admin = session.get('is_admin',False)

        # 判断是否是管理员
        if user_id and is_admin:
            return redirect(url_for('admin.admin_index'))
        return render_template('admin/login.html')

    # 表单提交POST，获取参数

    username = request.form.get('username')
    password = request.form.get('password')

    if not all([username,password]):
        return render_template('/admin/login.html',errmsg='参数不足')

    #数据库查看管理员进行匹配
    try:
        user = User.query.filter(User.mobile == username).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html',errmsg='数据查询失败')

    if not user:
        return render_template('admin/login.html',errmsg='用户不存在')

    if not user.check_password(password):
        return  render_template('admin/login.html',errmsg='密码错误')

    if not user.is_admin:
        return  render_template('admin/login.html',errmsg='用户权限不足')

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # session["is_admin"] = True
    # 逻辑优化，管理员进入前台保持管理员信息
    if user.is_admin:
        session['is_admin'] = True


    return redirect(url_for('admin.admin_index'))

@admin_blu.route('/')
@user_login_data
def admin_index():
    # 登录首页
    #读取登录用户的信息
    user = g.user
    # 管理员可以再登录状态下切换至管理后台界面
    if not user:
        return redirect(url_for('admin.admin_login'))

    # 构造渲染数据
    data = {
        'user':user.to_dict()
    }

    return render_template('admin/index.html',data=data)
@admin_blu.route('/tixian_list', methods=['GET', 'POST'])
@user_login_data
def tixian_list():
    user = g.user	
    p = request.args.get("p",1)
    current_page = 1
    total_page = 1
    per_page = 10
    paginate = Tixian.query.filter().paginate(p,per_page, False)
    tixian_li= paginate.items
    tixian_dict_li=[]
    for tixian_item in tixian_li:
         tixian_dict_li.append(tixian_item.to_review_dict())
    data = {
        "tixian_list": tixian_dict_li,
         "total_page" : total_page,
        "current_page" : current_page
		}
    return render_template("admin/user_tixian_list.html",data = data)

@admin_blu.route('/tixian_tongguo', methods=['GET', 'POST'])
@user_login_data
def tixian_tongguo():
    user = g.user
    key=request.args.get("key")
    tongguo = Tixian.query.filter(Tixian.id ==key).first()
    tongguo.status = 0
    db.session.commit()
    return redirect('http://127.0.0.1:5000/admin/tixian_list')
	
@admin_blu.route('/tixian_jujue', methods=['GET', 'POST'])
@user_login_data
def tixian_jujue():
    user = g.user
    key=request.args.get("key")
    key1=request.args.get("key1")
    print(key1)
    key2=request.args.get("key2")
    c = int(key2)
    print(key2)
    tuihuan = Tixian.query.filter(Tixian.id ==key1).first()
    print("wwwwwwwwwwwwwwwwwwwwwwwww")
    print(tuihuan.user_id)
    tuihuan1 = User.query.filter(User.id ==tuihuan.user_id).first()
    tuihuan1.money=tuihuan1.money+c
    jujue = Tixian.query.filter(Tixian.id ==key).first()
    jujue.status = -1
    db.session.commit()
    return redirect('http://127.0.0.1:5000/admin/tixian_list')