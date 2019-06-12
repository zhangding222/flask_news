from .CCPRestSDK import REST

# 说明：主账号，登陆云通讯网站后，可在"控制台-应用"中看到开发者主账号ACCOUNT SID
accountSid = '8aaf07086a961c7a016aa17484730ab8'

# 说明：主账号Token，登陆云通讯网站后，可在控制台-应用中看到开发者主账号AUTH TOKEN
accountToken = '0f966e86df5e4317b2bcd27d26983f47'

# 请使用管理控制台首页的APPID或自己创建应用的APPID
appId = '8aaf07086a961c7a016aa17484cd0abf'

# 说明：请求地址，生产环境配置成app.cloopen.com
serverIP = 'app.cloopen.com'

# 说明：请求端口 ，生产环境为8883
serverPort = '8883'

# 说明：REST API版本号保持不变
softVersion = '2013-12-26'

# accountSid = '8a216da866c847f90166cce2422a0263'
# accountToken = '81ad791901f54983823d3ae0fa3baefc'
# appId = '8a216da866c847f90166cce2429c026a'
# serverIP = 'app.cloopen.com'
# serverPort = '8883'
# softVersion = '2013-12-26'

# 短信辅助类
class CCP(object):
    # 创建单例对象
    def __new__(cls, *args, **kwargs):
        # 判断是否存在类属性_instance，_instance是类CCP的唯一对象，即单例
        # 第三方连接方式和参数传递,进行登陆
        if not hasattr(CCP, "instance"):
            cls.instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            cls.instance.rest = REST(serverIP, serverPort, softVersion)
            cls.instance.rest.setAccount(accountSid, accountToken)
            cls.instance.rest.setAppId(appId)
        return cls.instance

    def send_template_sms(self, to, datas, temp_id):
        """发送模板短信"""
        # @param to 手机号码
        # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
        # @param temp_id 模板Id默认为1
        result = self.rest.sendTemplateSMS(to, datas, temp_id)
        # 如果云通讯发送短信成功，返回的字典数据result中statuCode字段的值为"000000"
        if result.get("statusCode") == "000000":
            # 返回0 表示发送短信成功
            return 0
        else:
            # 返回-1 表示发送失败
            return -1
