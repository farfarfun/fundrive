#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Amazon S3驱动示例和测试脚本

本脚本演示如何使用Amazon S3驱动进行文件操作，包括：
- AWS认证配置
- 存储桶操作
- 文件上传下载
- 目录管理
- 搜索和分享功能

使用方法:
1. 快速演示: python example.py --demo
2. 完整测试: python example.py --test
3. 交互式演示: python example.py --interactive

配置方法:
1. 使用funsecret: funsecret set fundrive.amazon.access_key_id "your_key"
2. 环境变量: export AWS_ACCESS_KEY_ID="your_key"
3. 代码中直接设置

作者: FunDrive Team
"""

import argparse
import os
import tempfile
from typing import List

from fundrive.drives.amazon import S3Drive
from fundrive.core import DriveFile
from funutil import getLogger

logger = getLogger("fundrive")


def log_separator(title: str = ""):
    """记录分隔线"""
    logger.info("=" * 60)
    if title:
        logger.info(f" {title} ")
        logger.info("=" * 60)


def log_files(files: List[DriveFile], title: str = "文件列表"):
    """记录文件列表"""
    logger.info(f"📁 {title} (共 {len(files)} 个):")
    if not files:
        logger.info("  (空)")
        return

    for i, file in enumerate(files, 1):
        file_type = "📁" if file.ext.get("type") == "folder" else "📄"
        size_str = f"{file.size:,} bytes" if file.size > 0 else "-"
        logger.info(f"  {i:2d}. {file_type} {file.name}")
        logger.info(f"      键: {file.fid}")
        logger.info(f"      大小: {size_str}")
        if file.ext.get("last_modified"):
            logger.info(f"      修改时间: {file.ext['last_modified']}")


def create_test_file(filename: str = "s3_test.txt", content: str = None) -> str:
    """创建测试文件"""
    if content is None:
        content = f"""Amazon S3测试文件
文件名: {filename}
创建时间: {os.popen("date").read().strip()}

Amazon S3特性:
- 高可用性和持久性
- 无限扩展能力
- 多种存储类别
- 版本控制支持
- 细粒度权限控制
"""

    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"📄 创建测试文件: {filepath}")
    return filepath


def demo_basic_operations(drive: S3Drive):
    """演示基本操作"""
    log_separator("基本操作演示")

    # 登录
    logger.info("🔐 正在连接Amazon S3...")
    if drive.login():
        logger.info("✅ S3连接成功")
    else:
        logger.error("❌ S3连接失败")
        return False

    # 获取存储桶信息
    logger.info("💾 获取存储桶信息...")
    quota_info = drive.get_quota()
    if quota_info:
        logger.info("✅ 存储桶信息:")
        logger.info(f"   存储桶: {quota_info.get('bucket_name', 'N/A')}")
        logger.info(f"   区域: {quota_info.get('region', 'N/A')}")
        logger.info(f"   对象数量: {quota_info.get('object_count', 0):,}")
        logger.info(f"   总大小: {quota_info.get('total_size_gb', 0)} GB")

    # 列出根目录文件
    logger.info("📄 获取根目录文件列表...")
    files = drive.get_file_list("")
    log_files(files, "根目录文件")

    # 列出根目录子目录
    logger.info("📁 获取根目录子目录列表...")
    dirs = drive.get_dir_list("")
    log_files(dirs, "根目录子目录")

    return True


def run_quick_demo():
    """运行快速演示"""
    logger.info("🚀 Amazon S3驱动快速演示")
    logger.info("=" * 50)

    # 检查配置
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("S3_BUCKET_NAME")

    if not all([access_key, secret_key, bucket_name]):
        logger.warning("⚠️ 未找到AWS配置信息")
        logger.info("请设置以下环境变量:")
        logger.info("  export AWS_ACCESS_KEY_ID='your_access_key'")
        logger.info("  export AWS_SECRET_ACCESS_KEY='your_secret_key'")
        logger.info("  export S3_BUCKET_NAME='your_bucket_name'")
        logger.info("或使用funsecret配置")
        return

    # 创建驱动实例
    drive = S3Drive(
        access_key_id=access_key, secret_access_key=secret_key, bucket_name=bucket_name
    )

    # 运行演示
    demo_basic_operations(drive)

    log_separator("演示完成")
    logger.success("✅ Amazon S3驱动快速演示完成！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Amazon S3驱动示例和测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python example.py --demo          # 快速演示

配置方法:
  # 使用环境变量
  export AWS_ACCESS_KEY_ID="your_access_key"
  export AWS_SECRET_ACCESS_KEY="your_secret_key"
  export S3_BUCKET_NAME="your_bucket_name"
  
  # 使用funsecret (推荐)
  funsecret set fundrive.amazon.access_key_id "your_access_key"
  funsecret set fundrive.amazon.secret_access_key "your_secret_key"
  funsecret set fundrive.amazon.bucket_name "your_bucket_name"
        """,
    )

    parser.add_argument("--demo", action="store_true", help="运行快速演示")

    args = parser.parse_args()

    if args.demo:
        run_quick_demo()
    else:
        # 默认运行快速演示
        logger.info("未指定运行模式，执行快速演示...")
        logger.info("使用 --help 查看所有选项")
        run_quick_demo()


if __name__ == "__main__":
    main()
