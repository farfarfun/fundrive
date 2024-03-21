## 1.支持列表

| 序号 | 网盘             | 支持内容       |
| :--: | :--------------- | :------------- |
|  1   | [蓝奏云](#3.1)   | 上传/下载/删除 |
|  2   | [OSS](#3.2)      | 上传/下载/删除 |
|  3   | [github](#3.3)   | 上传/下载/删除 |
|  4   | [gitee](#3.4)    | 上传/下载/删除 |
|  5   | [百度网盘](#3.5) | TODO           |
|  6   | [阿里云盘](#3.6) | TODO           |

## 2.安装

```bash
pip install fundrive
```

或者直接从 gitHub 安装

```bash
pip install git+https://github.com/farfarfun/fundrive.git
```

或者直接从 gitee 安装

```bash
pip install git+https://gitee.com/farfarfun/fundrive.git
```

<h2 id="3">3 使用说明</h2>

- 所有的 drive 都是继承基类，实现登录、上传、下载、删除
- 每个 drive 的函数返回没有做统计，使用需注意
- 部分 drive 需要安装额外的库，不装也行，直接使用时会尝试 import，import 失败会自动安装

这是基类

```python
class DriveSystem:
    def __init__(self, *args, **kwargs):
        pass

    def login(self, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def mkdir(self, path, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def delete(self, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def get_file_list(self, *args, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError()

    def get_dir_list(self, *args, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError()

    def get_file_info(self, *args, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError()

    def get_dir_info(self, *args, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError()

    def download_file(self, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def download_dir(self, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def upload_file(self, file_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        raise NotImplementedError()

    def upload_dir(self, dir_path="./cache", overwrite=False, *args, **kwargs) -> bool:
        raise NotImplementedError()
```

<h3 id="3.1">3.1 蓝奏云</h3>
# 蓝奏云
额外安装lanzou底层api

```bash
pip install git+https://github.com/Leon406/lanzou-gui.git --no-deps
```

登录需要额外两个参数

<h3 id="3.1">3.2 OSS</h3>
额外安装oss的库OSS2

```bash
pip install oss2
```

登录需要参数

<h3 id="3.1">3.3 github</h3>

<h3 id="3.1">3.4 gitee</h3>

<h3 id="3.1">3.5 百度网盘</h3>

<h3 id="3.1">3.6 阿里云盘</h3>

#参考
百度云盘的 python-api，[官方 API](https://openapi.baidu.com/wiki/index.php?title=docs/pcs/rest/file_data_apis_list)  
蓝奏云的 python-api [参考](https://github.com/zaxtyson/LanZouCloud-API)
