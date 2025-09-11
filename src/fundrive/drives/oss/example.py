#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云 OSS 存储驱动标准化示例

本示例使用通用测试框架展示阿里云 OSS 驱动的综合功能测试。

基于官方 API 文档: https://help.aliyun.com/document_detail/32026.html
API 版本: v2.0

使用方法：
- python example.py  # 运行综合功能测试

配置方法：
请在 funsecret 中配置以下信息：
- fundrive.oss.access_key     # 阿里云访问密钥ID
- fundrive.oss.access_secret  # 阿里云访问密钥密码
- fundrive.oss.bucket_name    # OSS Bucket名称
- fundrive.oss.endpoint       # OSS访问域名

更新历史:
- 2024-12-11: 简化为只保留综合功能测试
- 2024-12-11: 重构为使用通用测试框架
- 2024-08-01: 初始版本
"""

from typing import Optional

from fundrive.drives.oss import OSSDrive
from fundrive.core import BaseDriveTest, create_drive_tester
from funutil import getLogger

logger = getLogger("fundrive.oss.example")


def create_drive() -> Optional[OSSDrive]:
    """创建阿里云 OSS 驱动实例"""
    try:
        drive = OSSDrive()
        logger.info("阿里云 OSS 驱动实例创建成功")
        return drive
    except Exception as e:
        logger.error(f"创建阿里云 OSS 驱动实例失败: {e}")
        return None


def main():
    """主函数 - 运行综合功能测试"""
    logger.info("🚀 阿里云 OSS 存储驱动综合功能测试")
    logger.info("=" * 50)

    # 创建驱动实例
    drive = create_drive()
    if not drive:
        logger.error("❌ 驱动实例创建失败")
        return

    # 使用通用测试框架
    tester = create_drive_tester(drive, "/fundrive_oss_测试")

    try:
        # 运行综合测试
        success = tester.comprehensive_test()

        # 输出结果
        if success:
            logger.success("🎉 测试运行成功！")
        else:
            logger.error("❌ 测试运行失败，请检查配置和网络连接")

    except KeyboardInterrupt:
        logger.warning("⚠️ 用户中断测试")
    except Exception as e:
        logger.error(f"💥 运行测试时发生异常: {e}")

    # 配置说明
    logger.info("\n🔧 配置说明:")
    logger.info("请确保已通过 funsecret 配置以下信息:")
    logger.info("- fundrive.oss.access_key     # 阿里云访问密钥ID")
    logger.info("- fundrive.oss.access_secret  # 阿里云访问密钥密码")
    logger.info("- fundrive.oss.bucket_name    # OSS Bucket名称")
    logger.info("- fundrive.oss.endpoint       # OSS访问域名")
    logger.info("\n📚 相关文档:")
    logger.info("- API 文档: https://help.aliyun.com/document_detail/32026.html")
    logger.info("- 开发指南: 查看项目 DEVELOPMENT_GUIDE.md")


if __name__ == "__main__":
    main()
