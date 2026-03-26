
# 说明
百度云盘的python-api，[官方API](https://openapi.baidu.com/wiki/index.php?title=docs/pcs/rest/file_data_apis_list)  


# 目录

|方法|描述|
|:--:|:--|
|[安装](#安装)|安装方式|
|[list](#list-查看)|查看该目录下有哪些文件|
|[meta](#meta-查看)|可以查看某个文件的具体信息|
|[upload](#upload-上传单个文件)|上传单个文件|
|[download](#download-下载单个文件)|下载单个文件|
|[upload_dir](#upload_dir-上传文件夹)|上传文件夹|
|[download_dir](#download_dir-下载文件夹)|下载文件夹|


# 使用
## 第一次使用
获取百度cookies中的BDUSS值，注意保密
```python
from fundrive.baidu.drive import BaiDuDrive
client = BaiDuDrive(bduss="XXXXXXXXXXXXXXXXXXXXXXXX",save=True)
```
第一次使用后，会将BDUSS存入'~/.secret/.bduss'(save=True时)

如果允许保存到本地，则下次调用不用传入dbuss,即
```python
from fundrive.baidu.drive import BaiDuDrive
client = BaiDuDrive()
```

## list 查看
```python
from fundrive.baidu.drive import BaiDuDrive

client = BaiDuDrive()
for path in client.list("/drive/example/api"):
    print(path['server_filename'])
```

## meta 查看
```python
from fundrive.baidu.drive import BaiDuDrive

client = BaiDuDrive()
print(client.meta("/drive/example/api/test.txt"))
```

## upload 上传单个文件
```python
from fundrive.baidu.drive import BaiDuDrive

client = BaiDuDrive()
client.upload('test.txt', '/drive/example/api/test.txt', overwrite=False)
```

## download 下载单个文件
```python
from fundrive.baidu.drive import BaiDuDrive

client = BaiDuDrive()
client.download( '/drive/example/api/test.txt','test2.txt', overwrite=False)
```

## upload_dir 上传文件夹
```python
from fundrive.baidu.drive import BaiDuDrive

client = BaiDuDrive()
client.upload_dir('logs', '/drive/example/api/')
```

## download_dir 下载文件夹
```python
from fundrive.baidu.drive import BaiDuDrive

client = BaiDuDrive()
client.download_dir('/drive/example/api/', 'logs')
```


# 参考
[baidupcsapi](https://github.com/ly0/baidupcsapi)
[baidu-pcs-python-sdk](https://github.com/mozillazg/baidu-pcs-python-sdk)


