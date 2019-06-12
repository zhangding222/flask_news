from flask import Blueprint
from flask import redirect
from flask import request
from flask import session
from flask import url_for

admin_blu = Blueprint('admin',__name__,url_prefix='/admin')

from . import views

# 应用钩子对于直接访问admin/login页面的用户信息匹配
@admin_blu.before_request
def before_request():
    if not request.url.endswith(url_for("admin.admin_login")):
        user_id = session.get("user_id",None)
        is_admin = session.get("is_admin",False)

        if not user_id or not is_admin:
            # 判断当前是否登录以及是否为管理员
            return redirect('/')