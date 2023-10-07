import datetime
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import os
from dotenv import load_dotenv
from dylr.core import app
load_dotenv()

# 正常情况日志级别使用 INFO，需要定位时可以修改为 DEBUG，此时 SDK 会打印和服务端的通信信息
# logging.basicConfig(level=logging.INFO, stream=sys.stdout)


# 1. 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在 CosConfig 中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
secret_id = os.environ['COS_SECRET_ID']     # 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
secret_key = os.environ['COS_SECRET_KEY']   # 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
bucket = os.environ['COS_BUCKET']
region = 'ap-hongkong'      # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
                           # COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
token = None               # 如果使用永久密钥不需要填入 token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见 https://cloud.tencent.com/document/product/436/14048
scheme = 'https'           # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

# print(f"COS_BUCKET={bucket}")

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
client = CosS3Client(config)

def save_object(room_id:str, filename:str, key:str, title:str, call_back_done):
    prograss_fun = make_upload_done(room_id, key, filename, title, call_back_done)
    response = client.upload_file(
        Bucket=bucket,
        LocalFilePath=filename,
        Key=key,
        PartSize=1,
        MAXThread=10,
        StorageClass="STANDARD_IA",
        EnableMD5=False,
        progress_callback = prograss_fun
    )

    print(f"{datetime.datetime.utcnow()}:{response['ETag']}")

def make_upload_done(room_id, key, filename, title, upload_done):
    roomid = room_id
    upload_complete = upload_done
    title = title
    filepath = filename
    url = f"https://default-1253420115.cos.ap-hongkong.myqcloud.com/{key}"
    key = key
    def call_back(consumed_bytes, total_bytes):
        if consumed_bytes==total_bytes:
            print(f"{datetime.datetime.utcnow()}:upload complete")
            upload_complete(roomid, title, url, filepath)
    return call_back