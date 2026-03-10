#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pCloud 网盘驱动标准化示例

本示例使用通用测试框架展示 pCloud 驱动的综合功能测试。

基于官方 API 文档: https://docs.pcloud.com/
API 版本: v1.0

使用方法：
- python example.py  # 运行综合功能测试

配置方法：
- 在 funsecret 中设置: fundrive.pcloud.username 和 fundrive.pcloud.password
- 或者直接在代码中传入用户名和密码

更新历史:
- 2024-12-11: 简化为只保留综合功能测试
- 2024-12-11: 重构为使用通用测试框架
- 2024-06-01: 初始版本
"""

from typing import Optional

from nltlog import getLogger

from fundrive.core import create_drive_tester
from fundrive.drives.pcloud import PCloudDrive

logger = getLogger("fundrive")


def create_drive() -> Optional[PCloudDrive]:
    """创建 pCloud 驱动实例"""
    try:
        drive = PCloudDrive()
        logger.info("pCloud 驱动实例创建成功")
        return drive
    except Exception as e:
        logger.error(f"创建 pCloud 驱动实例失败: {e}")
        return None


def main():
    """主函数 - 运行综合功能测试"""
    logger.info("🚀 pCloud 网盘驱动综合功能测试")
    logger.info("=" * 50)

    # 创建驱动实例
    drive = create_drive()
    if not drive:
        logger.error("❌ 驱动实例创建失败")
        return

    # 使用通用测试框架
    tester = create_drive_tester(drive, "/fundrive_pcloud_测试")

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
    logger.info("🔧 配置说明:")
    logger.info("请确保已通过 funsecret 配置以下信息:")
    logger.info("- fundrive.pcloud.username  # pCloud 用户名")
    logger.info("- fundrive.pcloud.password  # pCloud 密码")
    logger.info("📚 相关文档:")
    logger.info("- API 文档: https://docs.pcloud.com/")
    logger.info("- 开发指南: 查看项目 DEVELOPMENT_GUIDE.md")


if __name__ == "__main__":
    main()
