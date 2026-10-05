# 蓝奏云驱动（LanZouDrive）

`fundrive.drives.lanzou` 基于 [`fundrive-lanzou`](https://github.com/farfarfun/fundrive-lanzou)
（源自 [zaxtyson/LanZouCloud-API](https://github.com/zaxtyson/LanZouCloud-API)）封装，
把蓝奏云接入 FunDrive 的统一 `BaseDrive` 接口。

主要能力：

1. 上传、下载带 [tqdm](https://github.com/tqdm/tqdm) 进度条；
2. 既支持按目录ID操作，也支持直接按「分享链接 + 提取密码」读取；
3. `ylogin` / `phpdisk_info` 两个 Cookie 字段可交给
   [funsecret](https://github.com/farfarfun/funsecret) 本地保存，避免每次明文传入；
4. `LanZouSnapshot` 提供目录快照式的单向同步（本地目录打包上传 + 保留有限历史版本）。

## 安装

```bash
uv add "fundrive[lanzou]"
```

## 可运行示例

[`example.py`](example.py)：

```bash
python -m fundrive.drives.lanzou.example          # 只读：登录 + 列目录
python -m fundrive.drives.lanzou.example --fid 2192474
```

## 登录

```python
from fundrive.drives.lanzou import LanZouDrive

drive = LanZouDrive()

# 开启大文件分卷上传（默认关闭）
drive.ignore_limit()

# 第一次传入 Cookie 中的 ylogin / phpdisk_info
drive.login(ylogin="****", phpdisk_info="****")
```

把凭据预先写入 funsecret 后，`drive.login()` 不用再传参：

```bash
funsecret set fundrive drives funlanzou ylogin "****"
funsecret set fundrive drives funlanzou phpdisk_info "****"
```

也可以直接给出完整 Cookie 字典：

```python
drive.login(cookie={"ylogin": "****", "phpdisk_info": "****"})
```

## 浏览

```python
# 按目录ID列出子目录和文件
dirs = drive.get_dir_list(fid=2192474)
files = drive.get_file_list(fid=2192474)

# 按分享链接列出文件（pwd 为提取密码，无密码分享可不传）
files = drive.get_file_list(
    fid=None, url="https://wwe.lanzoui.com/ig56tpia6rg", pwd="1234"
)

for item in files:
    print(item["name"], item["size"], item["url"])
```

## 下载

```python
# 按文件ID下载
drive.download_file(fid="123456", save_dir="./download/lanzou")

# 按分享链接下载（无需登录账号）
drive.download_file(
    fid=None,
    url="https://wwe.lanzoui.com/ig56tpia6rg",
    pwd="1234",
    save_dir="./download/lanzou",
)
```

## 上传

```python
drive.upload_file(filepath="./file.csv", fid=2192474)
```

## 其他操作

```python
drive.mkdir(fid=-1, name="新目录")                      # fid=-1 表示根目录
drive.move(source_fid="123456", target_fid="2192474")
drive.delete(fid="123456")
```

## 目录快照同步

```python
from fundrive.drives.lanzou import LanZouSnapshot

snapshot = LanZouSnapshot(fid=2192474, version_num=20)
snapshot.update("./data")                                # 打包上传一个新版本

restore = LanZouSnapshot(url="https://wwe.lanzoui.com/b01hh2zve", pwd="1234")
restore.download("./restore")                            # 取最新快照并解包
```

## 注意事项

- 蓝奏云对单文件大小有限制，超限文件需要先调用 `ignore_limit()` 走分卷上传。
- `exist()` 恒返回 `True`：蓝奏云没有「按ID查询是否存在」的接口，实际存在性由后续
  具体操作的返回值体现。
- 蓝奏云不支持同名文件覆盖，`upload_file()` 的 `overwrite` 参数仅为满足 `BaseDrive`
  契约而保留。
- `DriveFile` 继承自 `dict`，字段用下标访问（`item["name"]`）。

## 致谢

[zaxtyson/LanZouCloud-API](https://github.com/zaxtyson/LanZouCloud-API)
（[API 文档](https://github.com/zaxtyson/LanZouCloud-API/wiki)）
