#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zenodo 学术数据存储驱动标准化示例

本示例使用通用测试框架展示 Zenodo 驱动的综合功能测试。

基于官方 API 文档: https://developers.zenodo.org/#rest-api
API 版本: v1.0

使用方法：
- python example.py  # 运行综合功能测试

配置方法：
- 在 funsecret 中设置: fundrive.zenodo.access_token
- 或者直接在代码中传入 access_token 参数

注意事项：
- 本示例默认使用 Zenodo 沙盒环境进行测试
- 沙盒环境数据不会影响正式的 Zenodo 记录

更新历史:
- 2024-12-11: 简化为只保留综合功能测试
- 2024-12-11: 重构为使用通用测试框架
- 2024-09-01: 初始版本
"""

from typing import Optional

from nltlog import getLogger

from fundrive.core import create_drive_tester
from fundrive.drives.zenodo import ZenodoDrive

logger = getLogger("fundrive.zenodo.example")


def create_drive() -> Optional[ZenodoDrive]:
    """创建 Zenodo 驱动实例"""
    try:
        # 使用沙盒环境进行测试
        drive = ZenodoDrive(sandbox=True)
        logger.info("Zenodo 驱动实例创建成功（沙盒模式）")
        return drive
    except Exception as e:
        logger.error(f"创建 Zenodo 驱动实例失败: {e}")
        return None


def main():
    """主函数 - 运行综合功能测试"""
    logger.info("🚀 Zenodo 学术数据存储驱动综合功能测试")
    logger.info("=" * 50)
    logger.info("🌐 注意：本示例使用 Zenodo 沙盒环境进行测试")

    # 创建驱动实例
    drive = create_drive()
    if not drive:
        logger.error("❌ 驱动实例创建失败")
        return

    # 使用通用测试框架
    tester = create_drive_tester(drive, "/fundrive_zenodo_测试存储库")

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
    logger.info("- fundrive.zenodo.access_token  # Zenodo 访问令牌")
    logger.info("📚 相关文档:")
    logger.info("- API 文档: https://developers.zenodo.org/#rest-api")
    logger.info("- 开发指南: 查看项目 DEVELOPMENT_GUIDE.md")
    logger.info("- 沙盒环境: https://sandbox.zenodo.org/")


if __name__ == "__main__":
    main()
