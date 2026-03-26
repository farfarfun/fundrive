# OpenXLab 云存储驱动

OpenXLab是上海人工智能实验室推出的开放平台，提供数据集存储和AI模型托管服务。本驱动基于OpenXLab API实现，为FunDrive项目提供对OpenXLab数据集的访问接口。

## 功能特性

### 核心功能
- ✅ **用户认证**: 支持Cookie认证登录
- ✅ **数据集浏览**: 查看数据集文件和目录结构
- ✅ **文件下载**: 下载数据集中的文件
- ✅ **文件信息**: 获取文件和目录的详细信息
- ✅ **存在检查**: 检查数据集或文件是否存在

### 高级功能
- 🔍 **文件搜索**: 支持在数据集内搜索文件
- 📦 **批量下载**: 支持下载整个数据集
- 🔄 **断点续传**: 自动跳过已下载的文件

### 平台特性
- 📖 **只读访问**: OpenXLab是只读平台，不支持上传、创建、删除操作
- 🎯 **数据集专用**: 专门用于访问AI/ML数据集
- 🌐 **开放平台**: 支持访问公开数据集

## 安装依赖

OpenXLab驱动需要以下Python包：

```bash
pip install requests funget nltsecret funutil
```

或者安装完整的FunDrive项目：

```bash
pip install fundrive[openxlab]
```

## 配置说明

### 获取认证信息

1. **访问OpenXLab网站**
   - 打开 [OpenXLab官网](https://openxlab.org.cn)
   - 注册并登录账户

2. **获取Cookie信息**
   - 登录后，打开浏览器开发者工具 (F12)
   - 切换到Network标签页
   - 刷新页面或访问任意数据集
   - 在请求头中找到Cookie信息
   - 复制`opendatalab_session`和`ssouid`的值

### 配置方法

#### 方法1: 使用nltsecret（推荐）

```bash
# 设置OpenXLab认证信息
nltsecret set fundrive openxlab opendatalab_session "your_session_cookie_value"
nltsecret set fundrive openxlab ssouid "your_ssouid_cookie_value"
```

#### 方法2: 使用环境变量

```bash
export OPENXLAB_SESSION="your_session_cookie_value"
export OPENXLAB_SSOUID="your_ssouid_cookie_value"
```

#### 方法3: 代码中直接传递

```python
from fundrive.drives.openxlab import OpenXLabDrive

drive = OpenXLabDrive(
    opendatalab_session="your_session_cookie_value",
    ssouid="your_ssouid_cookie_value"
)
```

## 使用示例

### 基础使用

```python
from fundrive.drives.openxlab import OpenXLabDrive

# 创建驱动实例
drive = OpenXLabDrive()

# 登录
if drive.login():
    print("✅ 登录成功")

    # 数据集名称格式：owner/dataset_name
    dataset_name = "OpenDataLab/MNIST"

    # 检查数据集是否存在
    exists = drive.exist(dataset_name)
    print(f"数据集存在: {exists}")

    # 获取数据集文件列表
    files = drive.get_file_list(dataset_name)
    print(f"数据集有 {len(files)} 个文件")

    # 获取数据集目录列表
    dirs = drive.get_dir_list(dataset_name)
    print(f"数据集有 {len(dirs)} 个目录")

    # 下载文件（需要完整的文件ID：dataset_id/file_path）
    if files:
        first_file = files[0]
        dataset_id = first_file.ext.get("dataset_id")
        file_path = first_file.ext.get("path")
        file_id = f"{dataset_id}{file_path}"

        success = drive.download_file(file_id, "./downloads")
        if success:
            print("✅ 文件下载成功")
else:
    print("❌ 登录失败")
```

### 高级功能

```python
# 搜索数据集中的文件
results = drive.search("train", fid="OpenDataLab/MNIST")
print(f"搜索到 {len(results)} 个相关文件")

# 下载整个数据集
success = drive.download_dir("OpenDataLab/MNIST", "./datasets/mnist")
if success:
    print("✅ 数据集下载完成")

# 获取文件详细信息
file_info = drive.get_file_info("dataset_id/path/to/file.txt")
if file_info:
    print(f"文件名: {file_info.name}")
    print(f"文件大小: {file_info.size} 字节")
    print(f"数据集ID: {file_info.ext.get('dataset_id')}")
```

### 批量操作

```python
# 批量下载多个数据集
datasets = [
    "OpenDataLab/MNIST",
    "OpenDataLab/CIFAR10",
    "OpenMMLab/COCO"
]

for dataset in datasets:
    print(f"正在下载数据集: {dataset}")
    success = drive.download_dir(dataset, f"./datasets/{dataset.replace('/', '_')}")
    if success:
        print(f"✅ {dataset} 下载完成")
    else:
        print(f"❌ {dataset} 下载失败")
```

## 测试和演示

### 运行测试

```bash
# 进入OpenXLab驱动目录
cd src/fundrive/drives/openxlab

# 运行完整功能测试
python example.py --test

# 运行交互式演示
python example.py --interactive

# 查看帮助信息
python example.py --help
```

### 测试内容

完整测试包括以下功能验证：

1. **登录认证测试** - 验证Cookie认证流程
2. **数据集存在检查** - 测试数据集存在性验证
3. **文件列表获取** - 测试文件列表功能
4. **目录列表获取** - 测试目录列表功能
5. **文件信息获取** - 测试文件信息查询
6. **文件下载** - 测试文件下载功能
7. **搜索功能** - 验证文件搜索功能
8. **只读限制** - 验证平台只读特性

## 错误处理和故障排除

### 常见问题

#### 1. 认证失败
```
❌ OpenXLab登录失败: 认证信息无效
```

**解决方案:**
- 检查Cookie是否正确复制
- 确认Cookie是否已过期
- 重新登录OpenXLab网站获取新Cookie

#### 2. 数据集不存在
```
❌ 获取数据集信息失败: 404
```

**解决方案:**
- 检查数据集名称格式是否正确（owner/dataset_name）
- 确认数据集是否为公开数据集
- 验证数据集名称拼写是否正确

#### 3. 下载失败
```
❌ 文件下载失败: 网络连接超时
```

**解决方案:**
- 检查网络连接
- 重试下载操作
- 使用较小的文件进行测试

#### 4. 权限不足
```
❌ 获取文件列表失败: 403 Forbidden
```

**解决方案:**
- 检查Cookie是否有效
- 确认账户是否有访问权限
- 重新登录获取新的认证信息

### 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 创建驱动实例时会输出详细日志
drive = OpenXLabDrive()
```

#### 检查API响应
```python
# 手动测试API访问
import requests

cookies = {
    "opendatalab_session": "your_session_cookie",
    "ssouid": "your_ssouid_cookie"
}

response = requests.get(
    "https://openxlab.org.cn/datasets/api/v2/datasets",
    cookies=cookies
)

print(f"状态码: {response.status_code}")
print(f"响应内容: {response.text[:200]}")
```

#### 验证数据集访问
```python
# 测试特定数据集访问
dataset_name = "OpenDataLab/MNIST"
dataset_api_name = dataset_name.replace("/", ",")

response = requests.get(
    f"https://openxlab.org.cn/datasets/api/v2/datasets/{dataset_api_name}",
    cookies=cookies
)

if response.status_code == 200:
    print("✅ 数据集访问正常")
else:
    print(f"❌ 数据集访问失败: {response.status_code}")
```

## 性能优化

### 下载优化
- 对于大数据集，建议分批下载
- 使用断点续传避免重复下载
- 并行下载多个小文件

### 缓存策略
- 缓存数据集文件列表减少API调用
- 本地存储文件元数据
- 使用文件大小验证完整性

### 网络优化
- 设置合适的超时时间
- 实现重试机制
- 使用连接池提高效率

## 数据集格式说明

### 数据集命名规范
- 格式：`owner/dataset_name`
- 示例：`OpenDataLab/MNIST`、`OpenMMLab/COCO`
- 大小写敏感

### 文件ID格式
- 格式：`dataset_id/file_path`
- 示例：`12345/data/train.txt`
- 用于文件下载和信息查询

### 常见数据集
- **OpenDataLab/MNIST** - 手写数字识别数据集
- **OpenDataLab/CIFAR10** - 图像分类数据集
- **OpenMMLab/COCO** - 目标检测数据集
- **OpenDataLab/ImageNet** - 大规模图像数据集

## 安全注意事项

### Cookie安全
- 不要在代码中硬编码Cookie值
- 使用环境变量或加密配置文件
- 定期更新Cookie避免过期

### 网络安全
- 所有API请求都通过HTTPS加密
- 验证SSL证书有效性
- 避免在不安全网络环境下使用

### 数据保护
- 遵守数据集的使用协议
- 不要未经授权分发数据集
- 注意个人隐私和数据保护法规

## API限制和配额

### 请求限制
- OpenXLab对API请求有频率限制
- 建议在请求间添加适当延迟
- 实现指数退避重试机制

### 下载限制
- 大文件下载可能有速度限制
- 并发下载数量可能受限
- 单次下载超时时间限制

### 功能限制
- 仅支持公开数据集访问
- 不支持私有数据集（除非有权限）
- 只读访问，无法修改数据集

## 贡献指南

欢迎为OpenXLab驱动贡献代码和改进建议！

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/farfarfun/fundrive.git
cd fundrive

# 安装开发依赖
pip install -e .[dev]

# 运行测试
python -m pytest tests/test_openxlab.py
```

### 提交规范
- 遵循项目代码风格
- 添加适当的测试用例
- 更新相关文档
- 提交前运行完整测试

### 问题报告
如果发现bug或有功能建议，请在GitHub上创建issue，包含：
- 详细的问题描述
- 复现步骤
- 错误日志
- 环境信息

## 许可证

本项目基于MIT许可证开源，详见LICENSE文件。

## 更新日志

### v1.0.0 (2024-01-XX)
- 🎉 首次发布OpenXLab驱动
- ✅ 实现完整的数据集访问功能
- ✅ 支持文件下载和搜索功能
- ✅ 添加完整的测试套件
- 📚 提供详细的使用文档

---

**注意**: OpenXLab是上海人工智能实验室的商标。本项目与上海人工智能实验室无关，仅为第三方客户端实现。
