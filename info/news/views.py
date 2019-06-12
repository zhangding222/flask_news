from flask import abort, jsonify
from flask import current_app
from flask import g
from flask import request
import tkinter
import tkinter.messagebox
from flask import redirect,url_for
from info import constants, db
from info.models import News, Comment, CommentLike, User
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blue
from flask import render_template
import tkinter
import tkinter.messagebox

@news_blue.route("/followed_user",methods = ["POST","GET"])
@user_login_data
def followed_user():
    user = g.user
    # 表示我要关注的这个新闻作者的id
    user_id = request.json.get("user_id")
    # 'follow', 'unfollow'
    action = request.json.get("action")
    # 获取到当前的新闻作者
    news_user = User.query.get(user_id)

    if action == "follow":
        # 关注
        if news_user not in user.followed:
            # 表示当前新闻的作者,不在我关注的人列表当中,如果不在,就把作者添加到我的关注人列表当中
            user.followed.append(news_user)
        else:
            return jsonify(errno = RET.PARAMERR,errmsg = "我已经关注你了")
    else:
        # 取消关注
        if news_user in user.followed:
            user.followed.remove(news_user)
        else:
            return jsonify(errno=RET.PARAMERR, errmsg="没有在我的关注人列表里面,没有办法取消")

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "ok")


@news_blue.route('/comment_like',methods=['POST'])
@user_login_data
def set_comment_like():
    # 评论点赞
    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

        # 获取参数
    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 判断参数
    if not all([comment_id, news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("add", "remove"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询评论数据
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论数据不存在")
    if action == "add":
        comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
        if not comment_like:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = g.user.id
            db.session.add(comment_like)
            # 增加点赞条数
            comment.like_count += 1
    else:
        # 删除点赞数据
        comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
        if comment_like:
            db.session.delete(comment_like)
            # 减小点赞条数
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blue.route('/news_comment',methods=['POST'])
@user_login_data
def add_news_comment():
# 添加评论
    user = g.user
    if not user:
        return jsonify(error=RET.SESSIONERR, errmsg='用户未登录')

    data_dict = request.json
    news_id = data_dict.get("news_id")
    comment_str = data_dict.get("comment")
    parent_id = data_dict.get("parent_id")

    if not all([news_id, comment_str]):
        return jsonify(errno=RET.PARAMERR , errmsg='参数不足')

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg='该新闻不存在')

    #初始化模型
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_str
    if parent_id:
        comment.parent_id = parent_id

#     保存至数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存评论数据失败')

    return jsonify(errno=RET.OK, errmsg='评论成功', data=comment.to_dict())

@news_blue.route('/new_dashang',methods=['GET','POST'])
@user_login_data
def news_dashang():
    user = g.user
    if not user:
        #tkinter.messagebox.showwarning('警告','没登陆')
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    a = request.form.get('dashang')
    b = request.form.get('newsid')
    try:
        c = int(a)
    except Exception as e:
	    return jsonify(errno=RET.OK, errmsg='不是数字')
    if c<= user.money:
        user.money = user.money - c
        db.session.commit()
        news1 = News.query.filter(News.id ==b).first()
        user1 = User.query.filter(User.id == news1.user_id).first()
        user1.money = user1.money + c
        db.session.commit()
        comment = Comment()
        comment.user_id = 999
        comment.news_id = b
        comment.content = "%s打赏了%s金币，真是任性啊！！！"  % (user.nick_name,c)
        db.session.add(comment)
        db.session.commit()
		
		
        return redirect('http://127.0.0.1:5000/news/%s'  % b) 
        
    else:
        return jsonify(errno=RET.OK, errmsg='金币不足') 

@news_blue.route('/news_collect',methods=['POST'])
@user_login_data
def news_collect():
    # 新闻收藏
    user = g.user
    json_data = request.json
    print(json_data)
    news_id = json_data.get('news_id')
    #name = news.query.filter(news.id ==52).first()	
    #user = user.query.filter(user.id == 1).first()
    action = json_data.get('action')

    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')

    if not news_id:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    # 收藏和取消收藏
    if action not in ('collect','cancel_collect'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.looger.error(e)
        return jsonify(erron=RET.DBERR,errmsg='查询数据错误')

    if not news:
        return jsonify(erron=RET.NODATA,errmsg='新闻数据不存在')

    # 此时查询的结果是一个关联的集合，所以集合操作是append和remove
    if action == 'collect':
        user.collection_news.append(news)
        news1 = News.query.filter(News.id ==news_id).first()
        user1 = User.query.filter(User.id == news1.user_id).first()
        user1.money = user1.money+5

    else:
        user.collection_news.remove(news)
        news1 = News.query.filter(News.id ==news_id).first()
        user1 = User.query.filter(User.id == news1.user_id).first()
        user1.money = user1.money-5
		

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存失败')

    return jsonify(errno=RET.OK,errmsg='操作成功')



@news_blue.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    user = g.user

    try:
        # 查看当前数据库中的前10条新闻
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    click_news_list = []
    for new_model in news_list:
        click_news_list.append(new_model.to_dict())
        if len(click_news_list) == 5:
			
            
            break

    try:
        # 获取新闻详情资料
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)
    if not news:
        abort(404)
    #     点击次数
    news.clicks +=1

    # # 判断是否收藏新闻
    # is_collected = False
    # if g.user:
    #     if news in g.user.collection_news:
    #         is_collected = True

    # 获取当前评论
    comments=[]
    try:
        # 查询当前新闻的所有评论按照最后修改时间排序
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    # 点赞的评论数据
    comment_like_ids = []
    # 点赞的ID
    comment_likes = []

    if user:
        comment_likes = CommentLike.query.filter(CommentLike.user_id == user.id).all()
        comment_likes_ids = [comment_like.comment_id for comment_like in comment_likes]

    comment_list = []
    for comment in comments:
        comment_dict = comment.to_dict()
        if comment.id in comment_like_ids:
            comment_dict['is_like'] = True
        comment_list.append(comment_dict)

    # for item in comments:
    #     comment_dict = item.to_dict()
    #     comment_list.append(comment_dict)


    is_collected = False
    if g.user:
        if news in g.user.collection_news:
            is_collected = True

    # 当前标记
    is_followed = False

    # 当前新闻必须有作者,才能关注, 用户必须登陆,才能关注作者

    if user:
        # 判断当前新闻的作者是否在我关注的人的列表里面(张三,李四)
        if news.user in user.followed:
            is_followed = True

    data = {
        "news":news.to_dict(),
        "user_info":user.to_dict() if user else None,
        "click_news_list":click_news_list,
        "news":news.to_dict(),
        "is_collected":is_collected,
        "comments":comment_list,
        "is_followed": is_followed,
    }
    return render_template('news/detail.html',data = data)
	
	

