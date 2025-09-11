# 📚 FunDrive 开发指南

欢迎来到 FunDrive 开发指南！本文档将帮助你快速上手网盘驱动开发，从零开始创建符合项目规范的高质量驱动。

## 🎯 快速导航

- [🚀 快速开始](#-快速开始) - 5分钟创建你的第一个驱动
- [📋 项目架构](#-项目架构) - 了解项目结构和设计理念
- [🏗️ 驱动开发](#️-驱动开发) - 详细的开发规范和最佳实践
- [🧪 测试指南](#-测试指南) - 使用通用测试框架
- [📖 文档规范](#-文档规范) - 编写高质量的文档
- [❓ 常见问题](#-常见问题) - 开发过程中的常见问题解答
- [🔧 故障排除](#-故障排除) - 问题诊断和解决方案

---

## 🚀 快速开始

### 5分钟创建你的第一个驱动

#### 步骤 1: 创建目录结构

```bash
# 创建驱动目录
mkdir -p src/fundrive/drives/your_drive
cd src/fundrive/drives/your_drive

# 创建必需文件
touch __init__.py drive.py example.py README.md
```

#### 步骤 2: 实现基础驱动类

```python
# drive.py
from fundrive.core import BaseDrive, DriveFile
from funutil import getLogger

logger = getLogger("fundrive.your_drive")

class YourDrive(BaseDrive):
    """你的网盘驱动实现"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化你的驱动配置
    
    def login(self, *args, **kwargs):
        """登录认证"""
        logger.info("开始登录...")
        # 实现登录逻辑
        return True
    
    # 实现其他必需方法...
```

#### 步骤 3: 使用通用测试框架

```python
# example.py
from fundrive.core import create_drive_tester
from .drive import YourDrive

def create_test_drive():
    """创建测试驱动实例"""
    return YourDrive()

def comprehensive_test():
    """运行综合功能测试"""
    drive = create_test_drive()
    if not drive:
        return False
    
    tester = create_drive_tester(drive, "/test_dir")
    return tester.comprehensive_test()

def quick_demo():
    """运行快速演示"""
    drive = create_test_drive()
    if not drive:
        return False
    
    tester = create_drive_tester(drive, "/demo_dir")
    return tester.quick_demo()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="你的网盘驱动示例")
    parser.add_argument("--test", action="store_true", help="运行综合功能测试")
    parser.add_argument("--demo", action="store_true", help="运行快速演示")
    
    args = parser.parse_args()
    
    if args.test:
        comprehensive_test()
    else:
        quick_demo()
```

#### 步骤 4: 测试你的驱动

```bash
# 运行快速演示
python example.py --demo

# 运行完整测试
python example.py --test
```

🎉 恭喜！你已经创建了一个基础的网盘驱动！

---

## 📋 项目架构

### 目录结构规范

每个网盘驱动必须遵循以下目录结构：

```
src/fundrive/drives/{drive_name}/
├── __init__.py          # 模块初始化和导出
├── drive.py             # 驱动主实现（必需）
├── example.py           # 测试和示例（必需）
└── README.md            # 驱动文档（必需）
```

### 核心组件说明

| 组件 | 作用 | 重要性 |
|:-----|:-----|:------:|
| **BaseDrive** | 抽象基类，定义统一接口 | 🔴 核心 |
| **DriveFile** | 文件信息封装类 | 🔴 核心 |
| **BaseDriveTest** | 通用测试框架 | 🟡 重要 |
| **funsecret** | 配置管理工具 | 🟡 重要 |
| **funutil** | 日志和工具库 | 🟢 辅助 |

### 必需文件说明

1. **`drive.py`** - 驱动主文件
   - 包含驱动的核心实现类
   - 必须继承 `BaseDrive` 基类
   - 必须实现所有抽象方法

2. **`example.py`** - 使用示例文件
   - 包含驱动的使用示例和综合测试代码
   - 必须提供 `comprehensive_test()` 函数，按优先级测试所有核心接口
   - 支持 `--test` 参数运行完整测试，`--demo` 参数运行快速演示
   - 提供清晰的使用说明和测试结果统计

3. **`README.md`** - 驱动说明文档
   - 简单介绍对应的网盘网站
   - 说明驱动的主要功能和特点
   - 提供配置和使用指南

## 🏗️ 驱动开发

### 核心接口实现

#### 必须实现的方法 (10个核心方法)

| 方法 | 说明 | 返回值 | 重要性 |
|:-----|:-----|:-------|:------:|
| `login()` | 登录认证 | `bool/object` | 🔴 必需 |
| `exist(path)` | 检查文件/目录是否存在 | `bool` | 🔴 必需 |
| `upload_file()` | 上传文件 | `bool/str` | 🔴 必需 |
| `download_file()` | 下载文件 | `bool` | 🔴 必需 |
| `mkdir()` | 创建目录 | `str` | 🔴 必需 |
| `delete()` | 删除文件/目录 | `bool` | 🔴 必需 |
| `get_file_list()` | 获取文件列表 | `List[DriveFile]` | 🔴 必需 |
| `get_dir_list()` | 获取目录列表 | `List[DriveFile]` | 🔴 必需 |
| `get_file_info()` | 获取文件信息 | `DriveFile` | 🔴 必需 |
| `get_dir_info()` | 获取目录信息 | `DriveFile` | 🔴 必需 |

#### 推荐实现的高级方法

| 方法 | 说明 | 推荐度 | 备注 |
|:-----|:-----|:------:|:-----|
| `search()` | 文件搜索 | ⭐⭐⭐ | 用户体验重要 |
| `share()` | 创建分享链接 | ⭐⭐⭐ | 协作功能 |
| `get_quota()` | 获取存储配额 | ⭐⭐⭐ | 存储管理 |
| `copy()` | 复制文件 | ⭐⭐ | 文件操作 |
| `move()` | 移动文件 | ⭐⭐ | 文件操作 |
| `rename()` | 重命名文件 | ⭐⭐ | 文件操作 |

### 实现模板

#### 基础驱动类模板

```python
from typing import List, Optional, Any
from fundrive.core import BaseDrive, DriveFile
from funutil import getLogger
from funsecret import read_secret

logger = getLogger("fundrive.your_drive")

class YourDrive(BaseDrive):
    """
    你的网盘驱动实现
    
    基于 Your Cloud API v1.0
    官方文档: https://api.yourcloud.com/docs
    """
    
    def __init__(self, api_key: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 配置管理 - 优先使用传入参数，然后尝试从配置读取
        self.api_key = api_key or read_secret(
            "fundrive.your_drive.api_key", 
            namespace="fundrive"
        )
        
        if not self.api_key:
            logger.warning("未找到 API 密钥，请配置后使用")
        
        self.client = None  # API 客户端实例
    
    def login(self, *args, **kwargs) -> bool:
        """登录认证"""
        try:
            logger.info("开始登录验证...")
            
            if not self.api_key:
                logger.error("缺少 API 密钥")
                return False
            
            # 初始化 API 客户端
            # self.client = YourCloudClient(api_key=self.api_key)
            
            # 验证连接
            # user_info = self.client.get_user_info()
            # logger.info(f"登录成功，用户: {user_info.get('name')}")
            
            return True
            
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    def exist(self, fid: str, *args, **kwargs) -> bool:
        """检查文件或目录是否存在"""
        try:
            # 实现存在性检查逻辑
            # result = self.client.get_metadata(fid)
            # return result is not None
            return True
            
        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
            return False
    
    # 实现其他必需方法...
```

### 不支持功能的处理

对于网盘 API 不支持的功能，请提供警告实现：

```python
def get_recycle_list(self, *args, **kwargs):
    """获取回收站文件列表 - 不支持的功能"""
    logger.warning(f"{self.__class__.__name__} 不支持回收站功能")
    return []

def restore(self, fid, *args, **kwargs):
    """恢复文件 - 不支持的功能"""
    logger.warning(f"{self.__class__.__name__} 不支持文件恢复功能")
    return False

def clear_recycle(self, *args, **kwargs):
    """清空回收站 - 不支持的功能"""
    logger.warning(f"{self.__class__.__name__} 不支持清空回收站功能")
    return False

def save_shared(self, shared_url, fid, *args, **kwargs):
    """保存分享文件 - 不支持的功能"""
    logger.warning(f"{self.__class__.__name__} 不支持保存分享文件功能")
    return False
```

---

## 🧪 测试指南

### 使用通用测试框架

FunDrive 提供了 `BaseDriveTest` 通用测试框架，让所有驱动都能使用标准化的测试逻辑。

#### 基本用法

```python
from fundrive.core import create_drive_tester
from .drive import YourDrive

def comprehensive_test():
    """运行综合功能测试"""
    # 1. 创建驱动实例
    drive = YourDrive(api_key="your_api_key")
    
    # 2. 创建测试器
    tester = create_drive_tester(drive, "/test_directory")
    
    # 3. 运行测试
    return tester.comprehensive_test()

def quick_demo():
    """运行快速演示"""
    drive = YourDrive(api_key="your_api_key")
    tester = create_drive_tester(drive, "/demo_directory")
    return tester.quick_demo()
```

#### 测试框架功能

| 测试类型 | 包含测试项 | 适用场景 |
|:--------|:----------|:---------|
| **comprehensive_test()** | 14个完整测试项 | 开发验证、CI/CD |
| **quick_demo()** | 5个核心测试项 | 快速验证、演示 |

#### 测试项目详情

**综合测试包含的14个测试项：**
1. 登录认证 ⭐⭐⭐⭐⭐
2. 获取配额信息 ⭐⭐⭐⭐
3. 检查根目录存在性 ⭐⭐⭐⭐
4. 获取根目录文件列表 ⭐⭐⭐⭐
5. 创建测试目录 ⭐⭐⭐⭐
6. 上传测试文件 ⭐⭐⭐⭐⭐
7. 下载测试文件 ⭐⭐⭐⭐⭐
8. 获取文件信息 ⭐⭐⭐
9. 重命名文件 ⭐⭐⭐
10. 复制文件 ⭐⭐
11. 搜索功能 ⭐⭐
12. 分享功能 ⭐⭐
13. 不支持功能测试 ⭐
14. 清理测试数据 ⭐⭐⭐⭐

### 自定义测试配置

```python
from fundrive.core import BaseDriveTest

class CustomDriveTest(BaseDriveTest):
    """自定义测试类"""
    
    def __init__(self, drive, test_dir="/custom_test"):
        super().__init__(drive, test_dir)
        # 添加自定义配置
    
    def test_custom_feature(self):
        """测试自定义功能"""
        try:
            # 实现自定义测试逻辑
            result = self.drive.custom_method()
            return result is not None
        except Exception as e:
            logger.error(f"自定义功能测试失败: {e}")
            return False
    
    def comprehensive_test(self):
        """扩展的综合测试"""
        # 先运行标准测试
        success = super().comprehensive_test()
        
        # 添加自定义测试
        if success:
            self.test_step("自定义功能测试", self.test_custom_feature)
        
        return success
```

---

## 📖 文档规范

### README.md 模板

每个驱动的 `README.md` 应包含以下内容：

```markdown
# Your Drive 网盘驱动

## 📖 网站介绍

[Your Cloud](https://yourcloud.com) 是一个...

- **存储容量**: 免费 10GB，付费最高 2TB
- **文件大小限制**: 单文件最大 5GB
- **API 限制**: 每小时 1000 次请求

## ✨ 功能支持

### ✅ 已实现功能
- [x] 文件上传/下载
- [x] 目录创建/删除
- [x] 文件搜索
- [x] 分享链接创建

### ❌ 不支持功能
- [ ] 回收站管理
- [ ] 文件版本控制
- [ ] 批量操作

## 🔧 配置指南

### 获取 API 密钥

1. 访问 [开发者控制台](https://yourcloud.com/developers)
2. 创建新应用
3. 获取 API Key

### 配置方法

```python
# 方法1: 直接传参
drive = YourDrive(api_key="your_api_key")

# 方法2: 环境变量
export YOUR_CLOUD_API_KEY="your_api_key"

# 方法3: funsecret 配置
funsecret set fundrive.your_drive.api_key "your_api_key"
```

## 🚀 使用示例

```python
from fundrive.drives.your_drive import YourDrive

# 初始化
drive = YourDrive()
drive.login()

# 基本操作
drive.upload_file("/local/file.txt", "/", "remote_file.txt")
files = drive.get_file_list("/")
```

## 🧪 测试

```bash
# 快速演示
python example.py --demo

# 完整测试
python example.py --test
```
```

---

## ❓ 常见问题

### Q1: 如何处理 API 限制？

**问题**: 网盘 API 有请求频率限制，如何优雅处理？

**解决方案**:
```python
import time
from functools import wraps

def rate_limit(calls_per_second=1):
    """API 限流装饰器"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

class YourDrive(BaseDrive):
    @rate_limit(calls_per_second=0.5)  # 每2秒最多1次请求
    def api_call(self, *args, **kwargs):
        # API 调用逻辑
        pass
```

### Q2: 如何处理大文件上传？

**问题**: 大文件上传容易超时或失败

**解决方案**:
```python
def upload_file(self, local_path, remote_dir, filename=None, chunk_size=8*1024*1024):
    """分块上传大文件"""
    file_size = os.path.getsize(local_path)
    
    if file_size > chunk_size:
        return self._upload_large_file(local_path, remote_dir, filename, chunk_size)
    else:
        return self._upload_small_file(local_path, remote_dir, filename)

def _upload_large_file(self, local_path, remote_dir, filename, chunk_size):
    """大文件分块上传"""
    try:
        # 1. 创建上传会话
        session = self.client.create_upload_session(filename)
        
        # 2. 分块上传
        with open(local_path, 'rb') as f:
            offset = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                self.client.upload_chunk(session.id, chunk, offset)
                offset += len(chunk)
                
                # 显示进度
                progress = (offset / file_size) * 100
                logger.info(f"上传进度: {progress:.1f}%")
        
        # 3. 完成上传
        return self.client.finish_upload(session.id)
        
    except Exception as e:
        logger.error(f"大文件上传失败: {e}")
        return False
```

### Q3: 如何处理网络异常？

**问题**: 网络不稳定导致操作失败

**解决方案**:
```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1, backoff=2):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"重试 {max_attempts} 次后仍然失败: {e}")
                        raise
                    
                    logger.warning(f"第 {attempts} 次尝试失败，{current_delay}秒后重试: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
            return None
        return wrapper
    return decorator

class YourDrive(BaseDrive):
    @retry(max_attempts=3, delay=1, backoff=2)
    def upload_file(self, *args, **kwargs):
        # 上传逻辑
        pass
```

### Q4: 如何调试驱动问题？

**启用详细日志**:
```python
import logging
from funutil import getLogger

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)
logger = getLogger("fundrive.your_drive")
logger.setLevel(logging.DEBUG)

# 在关键位置添加调试信息
def upload_file(self, local_path, remote_dir, filename=None):
    logger.debug(f"开始上传: {local_path} -> {remote_dir}/{filename}")
    
    try:
        # 上传逻辑
        result = self.client.upload(...)
        logger.debug(f"上传响应: {result}")
        return True
    except Exception as e:
        logger.debug(f"上传异常详情: {e}", exc_info=True)
        return False
```

---

## 🔧 故障排除

### 常见错误及解决方案

#### 1. 认证失败

**错误信息**: `登录失败: 401 Unauthorized`

**可能原因**:
- API 密钥错误或过期
- 网盘账户被禁用
- API 权限不足

**解决步骤**:
```bash
# 1. 检查 API 密钥
python -c "from funsecret import read_secret; print(read_secret('fundrive.your_drive.api_key'))"

# 2. 测试 API 连接
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.yourcloud.com/user

# 3. 重新获取 API 密钥
```

#### 2. 文件上传失败

**错误信息**: `上传文件失败: 413 Request Entity Too Large`

**可能原因**:
- 文件超过大小限制
- 网络超时
- 存储空间不足

**解决步骤**:
```python
# 检查文件大小
import os
file_size = os.path.getsize("your_file.txt")
print(f"文件大小: {file_size / (1024*1024):.2f} MB")

# 检查存储配额
drive = YourDrive()
drive.login()
quota = drive.get_quota()
print(f"剩余空间: {quota.get('available', 0) / (1024*1024*1024):.2f} GB")
```

#### 3. 测试失败

**错误信息**: `测试步骤异常: ModuleNotFoundError`

**解决步骤**:
```bash
# 1. 检查依赖安装
pip list | grep fundrive

# 2. 重新安装
pip install -e .

# 3. 检查 Python 路径
python -c "import sys; print('\n'.join(sys.path))"
```

### 性能优化建议

#### 1. 批量操作优化

```python
def batch_upload(self, file_list, remote_dir):
    """批量上传优化"""
    # 使用线程池并发上传
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for local_path in file_list:
            future = executor.submit(self.upload_file, local_path, remote_dir)
            futures.append(future)
        
        # 等待所有上传完成
        results = [future.result() for future in futures]
    
    return all(results)
```

#### 2. 缓存机制

```python
from functools import lru_cache
import time

class YourDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_list_cache = {}
        self._cache_ttl = 300  # 5分钟缓存
    
    def get_file_list(self, fid, use_cache=True):
        """带缓存的文件列表获取"""
        cache_key = f"file_list_{fid}"
        
        if use_cache and cache_key in self._file_list_cache:
            cached_data, timestamp = self._file_list_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"使用缓存数据: {cache_key}")
                return cached_data
        
        # 获取新数据
        file_list = self._fetch_file_list(fid)
        
        # 更新缓存
        self._file_list_cache[cache_key] = (file_list, time.time())
        
        return file_list
```

---

## 📝 代码风格和最佳实践

### 错误处理规范

```python
from funutil import getLogger

logger = getLogger("fundrive.your_drive")

def robust_operation(self, *args, **kwargs):
    """健壮的操作示例"""
    try:
        logger.info("开始执行操作...")
        
        # 参数验证
        if not args:
            raise ValueError("缺少必需参数")
        
        # 执行操作
        result = self._do_operation(*args, **kwargs)
        
        logger.info("操作执行成功")
        return result
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return None
    except ConnectionError as e:
        logger.error(f"网络连接错误: {e}")
        return None
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        return None
```

### 配置管理最佳实践

```python
from funsecret import read_secret
import os

class YourDrive(BaseDrive):
    def __init__(self, api_key=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 多层级配置读取
        self.api_key = (
            api_key or  # 1. 直接传参
            read_secret("fundrive.your_drive.api_key", namespace="fundrive") or  # 2. funsecret
            os.getenv("YOUR_DRIVE_API_KEY") or  # 3. 环境变量
            None
        )
        
        if not self.api_key:
            logger.warning("未找到 API 密钥，请通过以下方式之一进行配置：")
            logger.warning("1. 直接传参: YourDrive(api_key='your_key')")
            logger.warning("2. 环境变量: export YOUR_DRIVE_API_KEY='your_key'")
            logger.warning("3. funsecret: funsecret set fundrive.your_drive.api_key 'your_key'")
```

### 代码组织规范

```python
# 标准库导入
import os
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path

# 第三方库导入
import requests
from tqdm import tqdm
from funutil import getLogger
from funsecret import read_secret

# 项目内部导入
from fundrive.core import BaseDrive, DriveFile

# 常量定义
API_BASE_URL = "https://api.yourcloud.com/v1"
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024    # 8MB

logger = getLogger("fundrive.your_drive")
```

---

## ✅ 开发检查清单

### 🔴 必需项目（不可缺少）

- [ ] **继承 BaseDrive 基类**
- [ ] **实现所有10个核心抽象方法**
- [ ] **创建 drive.py、example.py、README.md 三个文件**
- [ ] **使用通用测试框架**
- [ ] **所有注释和错误信息使用中文**

### 🟡 重要项目（强烈推荐）

- [ ] **集成 funsecret 配置管理**
- [ ] **使用 funutil 统一日志记录**
- [ ] **实现高级功能（搜索、分享、配额查询）**
- [ ] **提供不支持功能的警告实现**
- [ ] **添加详细的 API 文档引用**

### 🟢 优化项目（锦上添花）

- [ ] **实现大文件分块上传**
- [ ] **添加 API 限流和重试机制**
- [ ] **提供缓存机制优化性能**
- [ ] **支持批量操作**
- [ ] **添加进度显示功能**

### 测试验证

```bash
# 1. 运行快速演示
python example.py --demo

# 2. 运行完整测试
python example.py --test

# 3. 检查成功率
# 目标：成功率 >= 70%（良好），>= 90%（优秀）
```

---

## 🎓 学习资源

### 参考实现

以下是已完成的高质量驱动实现，可作为参考：

1. **Dropbox 驱动** - 功能最完整，文档最齐全
2. **阿里云 OSS 驱动** - 企业级实现，性能优化好
3. **pCloud 驱动** - API 友好，实现简洁
4. **Zenodo 驱动** - 学术数据存储，特殊场景处理

### 相关文档

- [BaseDrive API 文档](src/fundrive/core/base.py)
- [通用测试框架文档](src/fundrive/core/test.py)
- [项目主 README](README.md)

---

## 🤝 贡献和支持

### 提交你的驱动

1. **Fork 项目仓库**
2. **创建功能分支**: `git checkout -b feature/your-drive`
3. **按照本指南开发驱动**
4. **确保通过所有检查清单**
5. **提交 Pull Request**

### 获取帮助

- 📧 **邮件支持**: 1007530194@qq.com
- 🐛 **问题反馈**: [GitHub Issues](https://github.com/farfarfun/fundrive/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/farfarfun/fundrive/discussions)

---

## 📋 版本信息

**文档版本**: v2.0.0  
**最后更新**: 2024-12-11  
**适用版本**: FunDrive v2.0+

### 更新历史

- **v2.0.0** (2024-12-11): 引入通用测试框架，重构开发规范
- **v1.2.0** (2024-10-01): 添加常见问题和故障排除指南
- **v1.1.0** (2024-08-01): 完善代码风格和最佳实践
- **v1.0.0** (2024-06-01): 初始版本，基础开发规范

---

**🎉 感谢你为 FunDrive 项目做出贡献！**
