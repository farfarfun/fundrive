# 天池 云存储驱动

天池是阿里云推出的数据科学竞赛平台，提供数据集存储和AI竞赛服务。本驱动基于天池API实现，为FunDrive项目提供对天池竞赛数据集的访问接口。

## 功能特性

### 核心功能
- ✅ **用户认证**: 支持Cookie和CSRF Token认证
- ✅ **数据集浏览**: 查看竞赛数据集文件和目录结构
- ✅ **文件下载**: 下载数据集中的文件
- ✅ **文件信息**: 获取文件和目录的详细信息
- ✅ **存在检查**: 检查数据集或文件是否存在

### 高级功能
- 🔍 **文件搜索**: 支持在数据集内搜索文件
- 📦 **批量下载**: 支持下载整个数据集
- 🎯 **竞赛专用**: 专门用于访问竞赛数据集

### 平台特性
- 📖 **只读访问**: 天池是只读平台，不支持上传、创建、删除操作
- 🏆 **竞赛导向**: 专门用于AI/ML竞赛数据集
- 🔒 **权限控制**: 需要参与竞赛才能访问相关数据集

## 安装依赖

天池驱动需要以下Python包：

```bash
pip install requests orjson funget funsecret funutil
```

或者安装完整的FunDrive项目：

```bash
pip install fundrive[tianchi]
```

## 配置说明

### 获取认证信息

1. **注册天池账户**
   - 访问 [天池官网](https://tianchi.aliyun.com)
   - 注册并登录账户

2. **参与竞赛**
   - 选择感兴趣的竞赛并报名参与
   - 获得数据集访问权限

3. **获取Cookie和Token信息**
   - 登录后，打开浏览器开发者工具 (F12)
   - 切换到Network标签页
   - 访问任意数据集页面
   - 在请求头中找到Cookie和Headers信息
   - 复制`tc`、`_csrf` Cookie值和`csrf-token` Header值

### 配置方法

#### 方法1: 使用funsecret（推荐）

```bash
# 设置天池认证信息
funsecret set fundrive tianchi cookies tc "your_tc_cookie_value"
funsecret set fundrive tianchi cookies _csrf "your_csrf_cookie_value"
funsecret set fundrive tianchi headers csrf-token "your_csrf_token_value"
```

#### 方法2: 使用环境变量

```bash
export TIANCHI_TC_COOKIE="your_tc_cookie_value"
export TIANCHI_CSRF_COOKIE="your_csrf_cookie_value"
export TIANCHI_CSRF_TOKEN="your_csrf_token_value"
```

#### 方法3: 代码中直接传递

```python
from fundrive.drives.tianchi import TianChiDrive

drive = TianChiDrive(
    tc_cookie="your_tc_cookie_value",
    csrf_cookie="your_csrf_cookie_value",
    csrf_token="your_csrf_token_value"
)
```

## 使用示例

### 基础使用

```python
from fundrive.drives.tianchi import TianChiDrive

# 创建驱动实例
drive = TianChiDrive()

# 登录
if drive.login():
    print("✅ 登录成功")
    
    # 数据集ID（数字格式）
    dataset_id = "75730"
    
    # 检查数据集是否存在
    exists = drive.exist(dataset_id)
    print(f"数据集存在: {exists}")
    
    # 获取数据集文件列表
    files = drive.get_file_list(dataset_id)
    print(f"数据集有 {len(files)} 个文件")
    
    # 获取数据集目录列表
    dirs = drive.get_dir_list(dataset_id)
    print(f"数据集有 {len(dirs)} 个目录")
    
    # 下载文件（需要文件ID）
    if files:
        first_file = files[0]
        file_id = first_file.ext.get("file_id")
        
        success = drive.download_file(file_id, "./downloads")
        if success:
            print("✅ 文件下载成功")
else:
    print("❌ 登录失败")
```

### 高级功能

```python
# 搜索数据集中的文件
results = drive.search("train", fid="75730")
print(f"搜索到 {len(results)} 个相关文件")

# 下载整个数据集
success = drive.download_dir("75730", "./datasets/tianchi_75730")
if success:
    print("✅ 数据集下载完成")

# 获取文件详细信息
file_info = drive.get_file_info("12345")  # 文件ID
if file_info:
    print(f"文件名: {file_info.name}")
    print(f"文件大小: {file_info.size} 字节")
    print(f"下载URL: {file_info.ext.get('download_url')}")
```

### 批量操作

```python
# 批量下载多个数据集
datasets = ["75730", "12345", "67890"]

for dataset_id in datasets:
    print(f"正在下载数据集: {dataset_id}")
    success = drive.download_dir(dataset_id, f"./datasets/tianchi_{dataset_id}")
    if success:
        print(f"✅ 数据集 {dataset_id} 下载完成")
    else:
        print(f"❌ 数据集 {dataset_id} 下载失败")
```

## 测试和演示

### 运行测试

```bash
# 进入天池驱动目录
cd src/fundrive/drives/tianchi

# 运行完整功能测试
python example.py --test

# 运行交互式演示
python example.py --interactive

# 查看帮助信息
python example.py --help
```

### 测试内容

完整测试包括以下功能验证：

1. **登录认证测试** - 验证Cookie和CSRF Token认证流程
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
❌ 天池登录失败: 认证信息无效
```

**解决方案:**
- 检查Cookie和CSRF Token是否正确复制
- 确认认证信息是否已过期
- 重新登录天池网站获取新的认证信息

#### 2. 数据集访问被拒绝
```
❌ 获取数据集信息失败: 403 Forbidden
```

**解决方案:**
- 确认是否已参与相关竞赛
- 检查竞赛是否仍在进行中
- 验证账户是否有访问权限

#### 3. 数据集不存在
```
❌ 获取数据集信息失败: 404
```

**解决方案:**
- 检查数据集ID是否正确
- 确认数据集是否已下线
- 验证数据集ID格式（应为数字）

#### 4. 下载失败
```
❌ 文件下载失败: 网络连接超时
```

**解决方案:**
- 检查网络连接
- 重试下载操作
- 使用较小的文件进行测试

### 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 创建驱动实例时会输出详细日志
drive = TianChiDrive()
```

#### 检查API响应
```python
# 手动测试API访问
import requests
import orjson

cookies = {
    "tc": "your_tc_cookie",
    "_csrf": "your_csrf_cookie"
}

headers = {
    "content-type": "application/json",
    "csrf-token": "your_csrf_token"
}

# 测试数据集访问
data = orjson.dumps({"dataId": 75730}).decode("utf-8")
response = requests.post(
    "https://tianchi.aliyun.com/api/notebook/dataDetail",
    cookies=cookies,
    headers=headers,
    data=data
)

print(f"状态码: {response.status_code}")
print(f"响应内容: {response.text[:200]}")
```

#### 验证文件下载URL
```python
# 测试文件下载URL获取
file_id = "12345"
response = requests.get(
    f"https://tianchi.aliyun.com/api/dataset/getFileDownloadUrl?fileId={file_id}",
    cookies=cookies
)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        print(f"✅ 下载URL: {result.get('data')}")
    else:
        print(f"❌ 获取下载URL失败: {result}")
else:
    print(f"❌ API请求失败: {response.status_code}")
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

## 竞赛数据集说明

### 数据集类型
- **图像分类** - 如CIFAR、ImageNet等
- **自然语言处理** - 如文本分类、情感分析等
- **推荐系统** - 如用户行为数据等
- **时间序列** - 如股价预测、销量预测等

### 数据集格式
- **训练集** - 用于模型训练
- **测试集** - 用于模型评估
- **验证集** - 用于模型调优
- **样本提交** - 提交格式示例

### 常见竞赛
- **阿里云天池新人实战赛** - 适合初学者
- **工业AI大赛** - 实际业务场景
- **学术竞赛** - 前沿算法研究
- **企业定制赛** - 特定行业应用

## 安全注意事项

### 认证信息安全
- 不要在代码中硬编码Cookie和Token
- 使用环境变量或加密配置文件
- 定期更新认证信息避免过期

### 网络安全
- 所有API请求都通过HTTPS加密
- 验证SSL证书有效性
- 避免在不安全网络环境下使用

### 数据保护
- 遵守竞赛数据使用协议
- 不要未经授权分发竞赛数据
- 注意个人隐私和数据保护法规

## API限制和配额

### 请求限制
- 天池对API请求有频率限制
- 建议在请求间添加适当延迟
- 实现指数退避重试机制

### 下载限制
- 大文件下载可能有速度限制
- 并发下载数量可能受限
- 单次下载超时时间限制

### 功能限制
- 仅支持已参与竞赛的数据集访问
- 不支持历史竞赛数据（除非特殊权限）
- 只读访问，无法修改数据集

## 贡献指南

欢迎为天池驱动贡献代码和改进建议！

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/farfarfun/fundrive.git
cd fundrive

# 安装开发依赖
pip install -e .[dev]

# 运行测试
python -m pytest tests/test_tianchi.py
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
- 🎉 首次发布天池驱动
- ✅ 实现完整的数据集访问功能
- ✅ 支持文件下载和搜索功能
- ✅ 添加完整的测试套件
- 📚 提供详细的使用文档

---

**注意**: 天池是阿里云的商标。本项目与阿里云无关，仅为第三方客户端实现。
