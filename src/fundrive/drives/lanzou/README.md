# 使用说明

[fundrive.lanzou](https://github.com/notechats/fundrive/tree/master/fundrive/lanzou) 是对 [zaxtyson/LanZouCloud-API](https://github.com/zaxtyson/LanZouCloud-API) 一些简单的封装，主要做了以下功能

1. 支持上传和下载的进度条，参考[tqdm/tqdm](https://github.com/tqdm/tqdm)；

2. 将本地的文件单向同步到云端；

3. 对`ylogin`和`phpdisk_info`进行简单的本地化保存，第二次无需传入，避免明文数据泄露，参考[notechats/funsecret](https://github.com/notechats/funsecret)；


---

# 使用实例

[python实例](https://github.com/notechats/fundrive/blob/master/example/lanzou_example.py)

## 登录
```python
from fundrive.lanzou import LanZouDrive

downer = LanZouDrive()
downer.ignore_limits()
# 第一次必须输入`ylogin`和`phpdisk_info`，会存入本地缓存；后续可不再输入
downer.login_by_cookie(ylogin="****", phpdisk_info="****")
```


## 下载
```python
downer.down_dir_by_url('https://wws.lanzous.com/b01hh2zve', dir_pwd='./lanzou')
```


登录将`ylogin`和`phpdisk_info`存入本地后，也可以使用快捷下载
```python 
from fundrive.lanzou import download
download('https://wwe.lanzoui.com/ig56tpia6rg', dir_pwd='./download/lanzou')
```


## 上传
```python
downer.upload_file('.file_csv.csv', folder_id=2192474)
```


## 同步
```python
downer.sync_files('.download/', folder_id=2192474)
```


---


# 感谢 

1. [zaxtyson/LanZouCloud-API](https://github.com/zaxtyson/LanZouCloud-API)： 对应的[API文档](https://github.com/zaxtyson/LanZouCloud-API/wiki)

