#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MediaFire驱动测试和演示脚本

使用方法:
    python example.py --test          # 运行完整测试
    python example.py --interactive   # 运行交互式演示
    python example.py --help         # 显示帮助信息

配置方法:
    # 使用funsecret配置（推荐）
    funsecret set fundrive mediafire email "your_email@example.com"
    funsecret set fundrive mediafire password "your_password"
    funsecret set fundrive mediafire app_id "your_app_id"
    funsecret set fundrive mediafire api_key "your_api_key"

    # 或者设置环境变量
    export MEDIAFIRE_EMAIL="your_email@example.com"
    export MEDIAFIRE_PASSWORD="your_password"
    export MEDIAFIRE_APP_ID="your_app_id"
    export MEDIAFIRE_API_KEY="your_api_key"
"""

import argparse
import os
import tempfile

from nltlog import getLogger

from fundrive.drives.mediafire import MediaFireDrive

logger = getLogger("fundrive.mediafire.example")


def create_mediafire_drive():
    """创建MediaFire驱动实例"""
    try:
        # 尝试从配置或环境变量获取凭据
        drive = MediaFireDrive()
        logger.info("✅ 成功创建MediaFireDrive实例")
        return drive
    except Exception as e:
        logger.error(f"❌ 创建MediaFireDrive实例失败: {e}")
        logger.info("请确保已正确配置MediaFire认证信息:")
        logger.info("funsecret set fundrive mediafire email 'your_email@example.com'")
        logger.info("funsecret set fundrive mediafire password 'your_password'")
        logger.info("funsecret set fundrive mediafire app_id 'your_app_id'")
        logger.info("funsecret set fundrive mediafire api_key 'your_api_key'")
        return None


def run_comprehensive_test(drive):
    """运行完整的驱动功能测试"""
    logger.info("\n🧪 开始MediaFire完整功能测试...")

    test_results = []

    # 测试1: 登录认证
    logger.info("\n1️⃣ 测试登录认证...")
    try:
        result = drive.login()
        if result:
            logger.info("✅ 登录成功")
            test_results.append(("登录认证", True))
        else:
            logger.error("❌ 登录失败")
            test_results.append(("登录认证", False))
            return test_results
    except Exception as e:
        logger.error(f"❌ 登录异常: {e}")
        test_results.append(("登录认证", False))
        return test_results

    # 测试2: 获取根目录文件列表
    logger.info("\n2️⃣ 测试获取文件列表...")
    try:
        files = drive.get_file_list("root")
        logger.info(f"✅ 获取到 {len(files)} 个文件")
        test_results.append(("获取文件列表", True))
    except Exception as e:
        logger.error(f"❌ 获取文件列表失败: {e}")
        test_results.append(("获取文件列表", False))

    # 测试3: 获取根目录列表
    logger.info("\n3️⃣ 测试获取目录列表...")
    try:
        dirs = drive.get_dir_list("root")
        logger.info(f"✅ 获取到 {len(dirs)} 个目录")
        test_results.append(("获取目录列表", True))
    except Exception as e:
        logger.error(f"❌ 获取目录列表失败: {e}")
        test_results.append(("获取目录列表", False))

    # 测试4: 创建测试目录
    test_dir_name = "fundrive_test_dir"
    logger.info(f"\n4️⃣ 测试创建目录: {test_dir_name}")
    try:
        result = drive.mkdir("root", test_dir_name)
        if result:
            logger.info("✅ 目录创建成功")
            test_results.append(("创建目录", True))
        else:
            logger.warning("⚠️ 目录可能已存在")
            test_results.append(("创建目录", True))
    except Exception as e:
        logger.error(f"❌ 创建目录失败: {e}")
        test_results.append(("创建目录", False))

    # 测试5: 创建测试文件并上传
    logger.info("\n5️⃣ 测试文件上传...")
    test_content = (
        f"这是MediaFire的测试文件内容\n测试时间: {os.popen('date').read().strip()}"
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        result = drive.upload_file(temp_file, "root", filename="fundrive_test.txt")
        if result:
            logger.info("✅ 文件上传成功")
            test_results.append(("文件上传", True))
        else:
            logger.error("❌ 文件上传失败")
            test_results.append(("文件上传", False))
    except Exception as e:
        logger.error(f"❌ 文件上传异常: {e}")
        test_results.append(("文件上传", False))
    finally:
        os.unlink(temp_file)

    # 测试6: 检查文件是否存在
    logger.info("\n6️⃣ 测试文件存在性检查...")
    try:
        exists = drive.exist("root", "fundrive_test.txt")
        if exists:
            logger.info("✅ 文件存在性检查通过")
            test_results.append(("文件存在检查", True))
        else:
            logger.warning("⚠️ 文件不存在")
            test_results.append(("文件存在检查", False))
    except Exception as e:
        logger.error(f"❌ 文件存在检查失败: {e}")
        test_results.append(("文件存在检查", False))

    # 测试7: 获取文件信息
    logger.info("\n7️⃣ 测试获取文件信息...")
    try:
        # 先获取文件列表找到测试文件
        files = drive.get_file_list("root")
        test_file = None
        for file in files:
            if file.name == "fundrive_test.txt":
                test_file = file
                break

        if test_file:
            file_info = drive.get_file_info(test_file.fid)
            if file_info:
                logger.info(
                    f"✅ 文件信息: {file_info.name}, 大小: {file_info.size} 字节"
                )
                test_results.append(("获取文件信息", True))
            else:
                logger.error("❌ 获取文件信息失败")
                test_results.append(("获取文件信息", False))
        else:
            logger.warning("⚠️ 未找到测试文件")
            test_results.append(("获取文件信息", False))
    except Exception as e:
        logger.error(f"❌ 获取文件信息异常: {e}")
        test_results.append(("获取文件信息", False))

    # 测试8: 文件下载
    logger.info("\n8️⃣ 测试文件下载...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            if test_file:
                result = drive.download_file(
                    test_file.fid, filedir=temp_dir, filename="downloaded_test.txt"
                )
                if result:
                    downloaded_file = os.path.join(temp_dir, "downloaded_test.txt")
                    if os.path.exists(downloaded_file):
                        logger.info("✅ 文件下载成功")
                        test_results.append(("文件下载", True))
                    else:
                        logger.error("❌ 下载的文件不存在")
                        test_results.append(("文件下载", False))
                else:
                    logger.error("❌ 文件下载失败")
                    test_results.append(("文件下载", False))
            else:
                logger.warning("⚠️ 没有测试文件可下载")
                test_results.append(("文件下载", False))
    except Exception as e:
        logger.error(f"❌ 文件下载异常: {e}")
        test_results.append(("文件下载", False))

    # 测试9: 搜索功能
    logger.info("\n9️⃣ 测试搜索功能...")
    try:
        results = drive.search("fundrive")
        logger.info(f"✅ 搜索完成，找到 {len(results)} 个结果")
        test_results.append(("搜索功能", True))
    except Exception as e:
        logger.error(f"❌ 搜索功能异常: {e}")
        test_results.append(("搜索功能", False))

    # 测试10: 获取存储配额
    logger.info("\n🔟 测试获取存储配额...")
    try:
        quota = drive.get_quota()
        if quota:
            logger.info(
                f"✅ 存储配额: 总计 {quota['total'] / (1024**3):.2f}GB, "
                f"已用 {quota['used'] / (1024**3):.2f}GB"
            )
            test_results.append(("获取存储配额", True))
        else:
            logger.error("❌ 获取存储配额失败")
            test_results.append(("获取存储配额", False))
    except Exception as e:
        logger.error(f"❌ 获取存储配额异常: {e}")
        test_results.append(("获取存储配额", False))

    # 测试11: 清理测试文件
    logger.info("\n1️⃣1️⃣ 清理测试文件...")
    try:
        if test_file:
            result = drive.delete(test_file.fid)
            if result:
                logger.info("✅ 测试文件删除成功")
                test_results.append(("删除文件", True))
            else:
                logger.error("❌ 测试文件删除失败")
                test_results.append(("删除文件", False))
        else:
            logger.warning("⚠️ 没有测试文件需要删除")
            test_results.append(("删除文件", True))
    except Exception as e:
        logger.error(f"❌ 删除文件异常: {e}")
        test_results.append(("删除文件", False))

    # 输出测试结果汇总
    logger.info("\n📊 MediaFire测试结果汇总:")
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n🎯 总体结果: {passed}/{len(test_results)} 项测试通过")

    return test_results


def run_interactive_demo():
    """运行交互式演示"""
    logger.info("\n🎮 MediaFire驱动交互式演示")
    logger.info("=" * 50)

    # 创建驱动实例
    drive = create_mediafire_drive()
    if not drive:
        logger.error("❌ 无法创建驱动实例，退出演示")
        return

    # 登录
    logger.info("\n🔐 正在登录MediaFire...")
    try:
        if not drive.login():
            logger.error("❌ 登录失败，退出演示")
            return
        logger.info("✅ 登录成功!")
    except Exception as e:
        logger.error(f"❌ 登录异常: {e}")
        return

    # 交互式操作循环
    while True:
        print("\nMediaFire可用操作:")
        print("1. 查看根目录文件")
        print("2. 查看根目录文件夹")
        print("3. 上传文件")
        print("4. 创建文件夹")
        print("5. 搜索文件")
        print("6. 查看存储配额")
        print("7. 退出")

        choice = input("\n请选择操作 (1-7): ").strip()

        if choice == "1":
            try:
                files = drive.get_file_list("root")
                logger.info(f"\n📁 根目录文件列表 (共 {len(files)} 个):")
                for i, file in enumerate(files[:10], 1):  # 只显示前10个
                    logger.info(f"  {i}. {file.name} ({file.size} 字节)")
                if len(files) > 10:
                    logger.info(f"  ... 还有 {len(files) - 10} 个文件")
            except Exception as e:
                logger.error(f"❌ 获取文件列表失败: {e}")

        elif choice == "2":
            try:
                dirs = drive.get_dir_list("root")
                logger.info(f"\n📂 根目录文件夹列表 (共 {len(dirs)} 个):")
                for i, dir in enumerate(dirs[:10], 1):  # 只显示前10个
                    logger.info(f"  {i}. {dir.name}")
                if len(dirs) > 10:
                    logger.info(f"  ... 还有 {len(dirs) - 10} 个文件夹")
            except Exception as e:
                logger.error(f"❌ 获取文件夹列表失败: {e}")

        elif choice == "3":
            file_path = input("请输入要上传的文件路径: ").strip()
            if os.path.exists(file_path):
                try:
                    filename = os.path.basename(file_path)
                    result = drive.upload_file(file_path, "root", filename=filename)
                    if result:
                        logger.info(f"✅ 文件 {filename} 上传成功")
                    else:
                        logger.error(f"❌ 文件 {filename} 上传失败")
                except Exception as e:
                    logger.error(f"❌ 上传文件异常: {e}")
            else:
                logger.error("❌ 文件不存在")

        elif choice == "4":
            dir_name = input("请输入要创建的文件夹名称: ").strip()
            if dir_name:
                try:
                    result = drive.mkdir("root", dir_name)
                    if result:
                        logger.info(f"✅ 文件夹 {dir_name} 创建成功")
                    else:
                        logger.error(f"❌ 文件夹 {dir_name} 创建失败")
                except Exception as e:
                    logger.error(f"❌ 创建文件夹异常: {e}")
            else:
                logger.error("❌ 文件夹名称不能为空")

        elif choice == "5":
            keyword = input("请输入搜索关键词: ").strip()
            if keyword:
                try:
                    results = drive.search(keyword)
                    logger.info(f"\n🔍 搜索结果 (共 {len(results)} 个):")
                    for i, file in enumerate(results[:10], 1):  # 只显示前10个
                        logger.info(f"  {i}. {file.name} ({file.size} 字节)")
                    if len(results) > 10:
                        logger.info(f"  ... 还有 {len(results) - 10} 个结果")
                except Exception as e:
                    logger.error(f"❌ 搜索失败: {e}")
            else:
                logger.error("❌ 搜索关键词不能为空")

        elif choice == "6":
            try:
                quota = drive.get_quota()
                if quota:
                    logger.info("\n💾 存储配额信息:")
                    logger.info(f"  总空间: {quota['total'] / (1024**3):.2f} GB")
                    logger.info(f"  已使用: {quota['used'] / (1024**3):.2f} GB")
                    logger.info(f"  可用空间: {quota['available'] / (1024**3):.2f} GB")
                    logger.info(
                        f"  使用率: {(quota['used'] / quota['total'] * 100):.1f}%"
                    )
                else:
                    logger.error("❌ 获取存储配额失败")
            except Exception as e:
                logger.error(f"❌ 获取存储配额异常: {e}")

        elif choice == "7":
            logger.info("👋 退出交互式演示")
            break

        else:
            print("❌ 无效选择，请输入 1-7")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MediaFire驱动测试和演示")
    parser.add_argument("--test", action="store_true", help="运行完整测试")
    parser.add_argument("--interactive", action="store_true", help="运行交互式演示")

    args = parser.parse_args()

    if args.test:
        logger.info("🚀 开始MediaFire驱动完整测试")

        drive = create_mediafire_drive()
        if drive:
            run_comprehensive_test(drive)

        logger.info("\n🎉 MediaFire驱动测试完成!")

    elif args.interactive:
        run_interactive_demo()

    else:
        parser.print_help()
        logger.info("\n💡 使用提示:")
        logger.info("  python example.py --test        # 运行完整测试")
        logger.info("  python example.py --interactive # 运行交互式演示")


if __name__ == "__main__":
    main()
