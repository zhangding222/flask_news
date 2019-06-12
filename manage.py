from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
from info import create_app,db
# 便于在入口函数通过命令进行数据库迁移操作
from info import models
from info.models import User

app = create_app("development")

# 脚本设置
manager = Manager(app)
Migrate(app,db)
manager.add_command('db',MigrateCommand)


@manager.option('-n','-name',dest='name')
@manager.option('-u','-password',dest='password')
def createsuperuser(name,password):
#     创建管理员
    if not all([name,password]):
        print('参数不足')
        return
    user = User()
    user.mobile = name
    user.nick_name = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
        print("创建成功")
    except Exception as e:
        print(e)
        db.session.rollback()



if __name__ == '__main__':
    manager.run()
    # app.run(host="0.0.0.0")
	

