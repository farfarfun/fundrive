"""
OneDrive 网盘驱动测试和示例

这个文件展示了如何使用 OneDrive 驱动，并提供了完整的测试功能。
使用通用测试框架进行标准化测试。

使用方法:
    python example.py --test    # 运行完整测试
    python example.py --interactive  # 交互式演示
"""

import argparse
import sys

from nltlog import getLogger

from fundrive.core import create_drive_tester
from fundrive.drives.onedrive.drive import OneDrive

logger = getLogger("fundrive.onedrive.example")


def create_test_drive():
    """
    创建测试用的OneDrive驱动实例

    Returns:
        OneDrive: 配置好的驱动实例，如果配置失败则返回None
    """
    try:
        logger.info("正在创建OneDrive驱动实例...")

        # 创建驱动实例
        # 注意：需要预先配置好client_id、client_secret和access_token
        drive = OneDrive()

        # 尝试登录
        if not drive.login():
            logger.error("OneDrive登录失败，请检查配置")
            logger.error("请确保已正确配置以下项目:")
            logger.error("1. Microsoft Azure应用注册")
            logger.error("2. 获取客户端ID和密钥")
            logger.error("3. 完成OAuth2授权流程")
            logger.error("4. 使用funsecret配置凭据:")
            logger.error(
                "   funsecret set fundrive onedrive client_id 'your_client_id'"
            )
            logger.error(
                "   funsecret set fundrive onedrive client_secret 'your_client_secret'"
            )
            logger.error(
                "   funsecret set fundrive onedrive access_token 'your_access_token'"
            )
            return None

        logger.info("OneDrive驱动创建成功")
        return drive

    except Exception as e:
        logger.error(f"创建OneDrive驱动失败: {e}")
        logger.error("请检查以下配置:")
        logger.error("1. 是否安装了requests库: pip install requests")
        logger.error("2. 是否正确配置了Azure应用凭据")
        logger.error("3. 是否完成了OAuth2授权流程")
        return None


def comprehensive_test():
    """
    运行综合功能测试

    使用通用测试框架测试OneDrive驱动的所有功能

    Returns:
        bool: 测试是否成功
    """
    logger.info("🚀 开始OneDrive驱动综合测试")

    # 1. 创建驱动实例
    drive = create_test_drive()
    if not drive:
        logger.error("❌ 无法创建驱动实例，测试终止")
        return False

    # 2. 创建测试器
    test_dir = "/fundrive_onedrive_test"  # 测试目录
    tester = create_drive_tester(drive, test_dir)

    # 3. 运行综合测试
    logger.info(f"📂 测试目录: {test_dir}")
    logger.info("📋 开始执行14项综合测试...")

    success = tester.comprehensive_test()

    # 4. 输出测试结果
    if success:
        logger.success("🎉 OneDrive驱动综合测试通过！")
        logger.info("✅ 驱动功能正常，可以正式使用")
    else:
        logger.warning("⚠️ 部分测试未通过，请检查相关功能")
        logger.info("💡 建议查看详细日志，修复问题后重新测试")

    return success


def interactive_demo():
    """
    交互式演示

    提供一个简单的交互界面，让用户体验OneDrive驱动的功能
    """
    logger.info("🎮 OneDrive驱动交互式演示")

    # 创建驱动实例
    drive = create_test_drive()
    if not drive:
        logger.error("❌ 无法创建驱动实例")
        return

    logger.info("✅ 驱动初始化成功！")
    logger.info("📋 可用功能:")
    logger.info("1. 查看存储配额")
    logger.info("2. 列出根目录文件")
    logger.info("3. 搜索文件")
    logger.info("4. 退出")

    while True:
        try:
            choice = input("\n请选择功能 (1-4): ").strip()

            if choice == "1":
                # 查看存储配额
                logger.info("📊 正在获取存储配额信息...")
                quota = drive.get_quota()
                if quota:
                    total_gb = quota.get("total", 0) / (1024**3)
                    used_gb = quota.get("used", 0) / (1024**3)
                    available_gb = quota.get("available", 0) / (1024**3)
                    usage_pct = quota.get("usage_percentage", 0)

                    print("\n📊 OneDrive 存储配额:")
                    print(f"   总空间: {total_gb:.2f} GB")
                    print(f"   已使用: {used_gb:.2f} GB ({usage_pct:.1f}%)")
                    print(f"   可用空间: {available_gb:.2f} GB")
                else:
                    logger.error("❌ 获取配额信息失败")

            elif choice == "2":
                # 列出根目录文件
                logger.info("📁 正在获取根目录文件列表...")
                files = drive.get_file_list("root")
                dirs = drive.get_dir_list("root")

                print("\n📁 根目录内容:")
                print(f"   目录数量: {len(dirs)}")
                print(f"   文件数量: {len(files)}")

                if dirs:
                    print("\n📂 目录:")
                    for i, dir_info in enumerate(dirs[:5], 1):  # 只显示前5个
                        print(f"   {i}. {dir_info.name}")
                    if len(dirs) > 5:
                        print(f"   ... 还有 {len(dirs) - 5} 个目录")

                if files:
                    print("\n📄 文件:")
                    for i, file_info in enumerate(files[:5], 1):  # 只显示前5个
                        size_mb = (file_info.size or 0) / (1024**2)
                        print(f"   {i}. {file_info.name} ({size_mb:.2f} MB)")
                    if len(files) > 5:
                        print(f"   ... 还有 {len(files) - 5} 个文件")

            elif choice == "3":
                # 搜索文件
                keyword = input("请输入搜索关键词: ").strip()
                if keyword:
                    logger.info(f"🔍 正在搜索包含 '{keyword}' 的文件...")
                    results = drive.search(keyword)

                    print(f"\n🔍 搜索结果 (关键词: {keyword}):")
                    print(f"   找到 {len(results)} 个结果")

                    if results:
                        for i, file_info in enumerate(results[:10], 1):  # 只显示前10个
                            size_info = ""
                            if file_info.size:
                                size_mb = file_info.size / (1024**2)
                                size_info = f" ({size_mb:.2f} MB)"
                            type_icon = "📂" if file_info.type == "dir" else "📄"
                            print(f"   {i}. {type_icon} {file_info.name}{size_info}")

                        if len(results) > 10:
                            print(f"   ... 还有 {len(results) - 10} 个结果")
                    else:
                        print("   未找到匹配的文件")

            elif choice == "4":
                logger.info("👋 退出交互式演示")
                break

            else:
                print("❌ 无效选择，请输入 1-4")

        except KeyboardInterrupt:
            logger.info("\n👋 用户中断，退出演示")
            break
        except Exception as e:
            logger.error(f"❌ 操作失败: {e}")


def main():
    """主函数，解析命令行参数并执行相应功能"""
    parser = argparse.ArgumentParser(
        description="OneDrive 网盘驱动测试和示例",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python example.py --test     # 运行完整测试
  python example.py --interactive  # 交互式演示
  
配置说明:
  1. 注册Azure应用:
     - 访问 https://portal.azure.com/
     - 注册新应用并获取客户端ID和密钥
     - 配置重定向URI和API权限
  
  2. 配置凭据:
     funsecret set fundrive onedrive client_id "your_client_id"
     funsecret set fundrive onedrive client_secret "your_client_secret"
  
  3. 完成OAuth2授权获取访问令牌
        """,
    )

    parser.add_argument(
        "--test", action="store_true", help="运行完整的综合功能测试 (14项测试)"
    )
    parser.add_argument("--interactive", action="store_true", help="运行交互式演示")

    args = parser.parse_args()

    # 显示欢迎信息
    logger.info("=" * 60)
    logger.info("🚀 OneDrive 网盘驱动 - 测试和示例程序")
    logger.info("=" * 60)

    try:
        if args.test:
            # 运行综合测试
            success = comprehensive_test()
            sys.exit(0 if success else 1)

        elif args.interactive:
            # 运行交互式演示
            interactive_demo()

        else:
            # 默认运行完整测试
            logger.info("💡 未指定参数，运行完整测试")
            logger.info("💡 使用 --help 查看所有可用选项")
            success = comprehensive_test()
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\n👋 用户中断程序")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
