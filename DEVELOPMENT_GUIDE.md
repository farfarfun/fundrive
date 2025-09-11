# FunDrive 开发规范

本文档规定了 FunDrive 项目中所有网盘驱动的开发标准和规范。

## 📋 目录结构规范

每个网盘驱动必须遵循以下目录结构：

```
src/fundrive/drives/{drive_name}/
├── __init__.py          # 模块初始化文件
├── drive.py             # 驱动主文件（必需）
├── example.py           # 使用示例文件（必需）
└── README.md            # 驱动说明文档（必需）
```

### 必需文件说明

1. **`drive.py`** - 驱动主文件
   - 包含驱动的核心实现类
   - 必须继承 `BaseDrive` 基类
   - 必须实现所有抽象方法

2. **`example.py`** - 使用示例文件
   - 包含驱动的使用示例和测试代码
   - 支持多种运行模式（基础测试、完整演示、简单示例）
   - 提供清晰的使用说明

3. **`README.md`** - 驱动说明文档
   - 简单介绍对应的网盘网站
   - 说明驱动的主要功能和特点
   - 提供配置和使用指南

## 🏗️ 驱动实现规范

### 1. 基类继承要求

所有驱动类必须继承 `BaseDrive` 基类：

```python
from fundrive.core import BaseDrive

class YourDrive(BaseDrive):
    """你的网盘驱动类"""
    pass
```

### 2. 抽象方法实现要求

**必须实现所有 `BaseDrive` 的抽象方法**，即使某些功能不支持，也要提供实现：

#### 核心方法（必须有实际功能）
- `login()` - 登录认证
- `get_dir_list()` - 获取目录列表
- `get_file_list()` - 获取文件列表
- `upload_file()` - 上传文件
- `download_file()` - 下载文件

#### 可选方法（可以返回空实现 + 警告）
对于不支持的功能，使用以下模式：

```python
def unsupported_method(self, *args, **kwargs):
    """不支持的方法示例"""
    logger.warning(f"{self.__class__.__name__} 不支持此操作")
    return False  # 或适当的默认返回值
```

### 3. 错误处理规范

- 使用统一的日志记录：`from funutil import getLogger`
- 所有错误信息使用中文
- 提供详细的异常处理和用户友好的错误提示
- 关键操作要有成功/失败的明确反馈

```python
from funutil import getLogger

logger = getLogger("your_drive")

try:
    # 操作代码
    logger.info("操作成功")
    return True
except Exception as e:
    logger.error(f"操作失败: {e}")
    return False
```

### 4. 配置管理规范

- 使用 `funsecret` 进行敏感信息管理
- 支持多种配置方式（环境变量、配置文件等）
- 提供清晰的配置说明

```python
from funsecret import read_secret

# 推荐的配置读取方式
access_token = read_secret("fundrive", "your_drive", "access_token")
```

## 📝 代码风格规范

### 1. 注释规范
- 所有注释使用中文
- 类和方法必须有详细的文档字符串
- 重要的业务逻辑要有行内注释

### 2. 命名规范
- 类名使用 PascalCase：`ZenodoDrive`
- 方法名使用 snake_case：`get_file_list`
- 常量使用 UPPER_CASE：`API_BASE_URL`

### 3. 导入规范
- 标准库导入放在最前面
- 第三方库导入放在中间
- 项目内部导入放在最后
- 使用相对导入引用同目录文件

```python
# 标准库
import os
import sys
from typing import Optional, List

# 第三方库
import requests
from funutil import getLogger

# 项目内部
from fundrive.core import BaseDrive, DriveFile
```

## 📖 示例文件规范

### 1. 功能要求
`example.py` 文件必须包含以下功能：

- **基础测试模式** (`--test`)：测试核心功能
- **完整演示模式** (`--demo`)：展示所有功能
- **简单示例模式** (`--simple` 或默认)：快速上手示例

### 2. 命令行支持
```python
def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--test":
            test_basic_functionality()
        elif mode == "--demo":
            demo_full_functionality()
        elif mode == "--simple":
            simple_example()
    else:
        simple_example()  # 默认运行简单示例
```

### 3. 使用说明
在文件末尾提供清晰的使用说明：

```python
print("\n📝 使用说明:")
print("- python example.py --test    # 基础功能测试")
print("- python example.py --demo    # 完整功能演示")
print("- python example.py --simple  # 简单使用示例")
print("- python example.py           # 默认运行简单示例")
```

## 📄 README 文档规范

每个驱动的 `README.md` 必须包含以下内容：

### 1. 网站介绍
- 网盘网站的基本信息
- 主要特点和用途
- 官方网站链接

### 2. 驱动功能
- 支持的功能列表
- 不支持的功能说明
- 特殊限制或注意事项

### 3. 配置指南
- 如何获取 API 密钥或访问令牌
- 配置方法和示例
- 环境要求

### 4. 使用示例
- 基本使用代码示例
- 常见操作演示
- 参考 `example.py` 的使用方法

## 🧪 测试规范

### 1. 测试环境
- 优先使用沙盒或测试环境
- 避免影响用户的正式数据
- 提供测试数据的清理机制

### 2. 测试覆盖
- 核心功能必须有测试
- 错误处理场景要有覆盖
- 边界条件要有验证

### 3. 测试数据
- 使用临时文件和目录
- 测试完成后自动清理
- 不要硬编码敏感信息

## 📚 文档规范

### 1. API 文档引用
在代码中引用官方 API 文档：

```python
"""
网盘驱动实现

基于官方 API 文档: https://api-docs-url.com
API 版本: v1.0.0
"""
```

### 2. 更新日志
重大更新要在文件头部添加更新说明：

```python
"""
更新历史:
- 2024-01-01: 初始版本
- 2024-01-15: 添加批量上传功能
- 2024-02-01: 修复下载错误处理
"""
```

## ✅ 检查清单

在提交新的驱动实现前，请确认以下项目：

- [ ] 继承了 `BaseDrive` 基类
- [ ] 实现了所有抽象方法（不支持的功能也要有警告实现）
- [ ] 包含了三个必需文件：`drive.py`、`example.py`、`README.md`
- [ ] 所有注释和错误信息使用中文
- [ ] 使用了统一的日志记录和错误处理
- [ ] 集成了 `funsecret` 配置管理
- [ ] `example.py` 支持多种运行模式
- [ ] `README.md` 包含了网站介绍和使用指南
- [ ] 代码通过了基础功能测试
- [ ] 遵循了项目的代码风格规范

## 🔄 持续改进

本开发规范会根据项目发展和社区反馈持续更新。如有建议或问题，请提交 Issue 或 Pull Request。

---

**最后更新**: 2024-01-01  
**版本**: v1.0.0
