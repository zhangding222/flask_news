from flask import g
from flask import request, jsonify

from info import constants
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import index_blue
from flask import render_template
from flask import current_app
from flask import session
global keywords
@index_blue.route("/")
@user_login_data
def index():
    user = g.user
    news_list = None
    global keywords
    keywords = request.values.get('keywords')   	
    try:
        # 查看当前数据库中的前10条新闻
        news_list = News.query.order_by(News.clicks.desc()).filter(News.status == 0)
		
    except Exception as e:
        current_app.logger.error(e)

    click_news_list = []
    # 将查询的结果分别存入列表中
    for news in news_list if news_list else []:
        click_news_list.append(news.to_basic_dict())
        if len(click_news_list) == 5:
            print ("111")
			
            
            break

    categories = Category.query.all()
    categories_dicts = []

    # for category in enumerate(categories):
    #     将当前对象进行拼接,将每条信息按照索引分开
    #     to_dict将数据转换成字典格式
    for category in categories:
        categories_dicts.append(category.to_dict())


    # 将查询的结果和用户的状态一起发送至前端
    data = {
        "user_info": user.to_dict() if user else None,
        # 热门新闻列表
        "click_news_list":click_news_list,
        # 新闻分类列表
        "categories":categories_dicts
    }
    # 传输用户状态
    return render_template('news/index.html',data=data)

    

# 首页列表新闻
@index_blue.route('/news_list')
def get_news_list():
    # 获取参数页数\条数\id值
    args_dict = request.args
    cid = args_dict.get("cid", "1")
    page = args_dict.get("page","1")
    per_page = args_dict.get("per_page",constants.HOME_PAGE_MAX_NEWS)

    #校验参数
    # 转换类型
    try:
        page = int(page)
        per_page = int(per_page)
        cid = int(cid)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR ,errmsg="页码参数错误")

    #查询当前页数查询结果
    global keywords
    if keywords:
        filter = [News.status == 0,News.title.contains(keywords)]
    else:
	    filter = [News.status == 0]
    #此时cid时int类型，匹配无须""
    if cid != 1:
	    
        filter.append(News.category_id == cid)
    try:
        # paginate 获取页数\现实条数\以及是否引起404报错
        # paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
        paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(page, per_page, False)
        # 查询的结果
        items = paginate.items
        #
        toal_page = paginate.pages
        #
        current_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR , errmsg = "数据查询失败")

    items_list = []
    for item in items:
        items_list.append(item.to_dict())

    data = {
        "current_page": current_page,
        "total_page": toal_page,
        "news_dict_li": items_list
    }
    return jsonify(errno=RET.OK ,errmsg="OK",data = data)


@index_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')