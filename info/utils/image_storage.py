from qiniu import Auth, put_data

# 七牛access_key
access_key = "259yQ1fyibfVJOH280S_gscu8WZ8pR0_Yy6izn_a"

# 七牛secret_key
secret_key = "aVFo6VuRmRNM8YH7ZL_X9GwOc5RPG08KMdamTRvz"
bucket_name = "ihome-python"
def storage(data):
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
        print(ret, info)
    except Exception as e:
        raise e;

    print(info)
    print("*"*10)
    print(ret)
    if info.status_code == 200:
        # 表示上传成功, 返回文件名
        return ret.get("key")
    else:
        # 上传失败
        raise Exception("上传七牛失败")


if __name__ == '__main__':
    with open("./bb.jpg", "rb") as f:
        file_data = f.read()
        storage(file_data)