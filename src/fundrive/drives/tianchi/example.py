#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
天池驱动测试和演示脚本

使用方法:
    python example.py --test          # 运行完整测试
    python example.py --interactive   # 运行交互式演示
    python example.py --help         # 显示帮助信息

配置方法:
    # 使用funsecret配置（推荐）
    funsecret set fundrive tianchi cookies tc "your_tc_cookie"
    funsecret set fundrive tianchi cookies _csrf "your_csrf_cookie"
    funsecret set fundrive tianchi headers csrf-token "your_csrf_token"

    # 或者设置环境变量
    export TIANCHI_TC_COOKIE="your_tc_cookie"
    export TIANCHI_CSRF_COOKIE="your_csrf_cookie"
    export TIANCHI_CSRF_TOKEN="your_csrf_token"

注意：天池是只读平台，主要用于竞赛数据集下载和浏览
"""

import argparse
import os
import tempfile


from fundrive.drives.tianchi import TianChiDrive
from funutil import getLogger

logger = getLogger("fundrive.tianchi.example")


def create_tianchi_drive():
    """创建天池驱动实例"""
    try:
        # 尝试从配置或环境变量获取凭据
        drive = TianChiDrive()
        logger.info("✅ 成功创建TianChiDrive实例")
        return drive
    except Exception as e:
        logger.error(f"❌ 创建TianChiDrive实例失败: {e}")
        logger.info("请确保已正确配置天池认证信息:")
        logger.info("funsecret set fundrive tianchi cookies tc 'your_tc_cookie'")
        logger.info("funsecret set fundrive tianchi cookies _csrf 'your_csrf_cookie'")
        logger.info(
            "funsecret set fundrive tianchi headers csrf-token 'your_csrf_token'"
        )
        return None


def run_comprehensive_test(drive):
    """运行完整的驱动功能测试"""
    logger.info("\n🧪 开始天池完整功能测试...")

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

    # 测试数据集ID（使用一个公开的测试数据集）
    test_dataset_id = "75730"  # 示例数据集ID

    # 测试2: 检查数据集是否存在
    logger.info(f"\n2️⃣ 测试数据集存在性检查: {test_dataset_id}")
    try:
        exists = drive.exist(test_dataset_id)
        if exists:
            logger.info("✅ 数据集存在")
            test_results.append(("数据集存在检查", True))
        else:
            logger.warning("⚠️ 测试数据集不存在，将使用其他数据集")
            test_results.append(("数据集存在检查", False))
            # 尝试其他数据集
            test_dataset_id = "12345"
    except Exception as e:
        logger.error(f"❌ 数据集存在检查失败: {e}")
        test_results.append(("数据集存在检查", False))

    # 测试3: 获取数据集文件列表
    logger.info(f"\n3️⃣ 测试获取文件列表: {test_dataset_id}")
    try:
        files = drive.get_file_list(test_dataset_id)
        logger.info(f"✅ 获取到 {len(files)} 个文件")
        test_results.append(("获取文件列表", True))

        # 保存第一个文件用于后续测试
        test_file = files[0] if files else None

    except Exception as e:
        logger.error(f"❌ 获取文件列表失败: {e}")
        test_results.append(("获取文件列表", False))
        test_file = None

    # 测试4: 获取数据集目录列表
    logger.info(f"\n4️⃣ 测试获取目录列表: {test_dataset_id}")
    try:
        dirs = drive.get_dir_list(test_dataset_id)
        logger.info(f"✅ 获取到 {len(dirs)} 个目录")
        test_results.append(("获取目录列表", True))
    except Exception as e:
        logger.error(f"❌ 获取目录列表失败: {e}")
        test_results.append(("获取目录列表", False))

    # 测试5: 获取文件信息
    if test_file:
        logger.info(f"\n5️⃣ 测试获取文件信息: {test_file.name}")
        try:
            file_id = test_file.ext.get("file_id", test_file.fid)

            file_info = drive.get_file_info(file_id)
            if file_info:
                logger.info(
                    f"✅ 文件信息: {file_info.name}, 大小: {file_info.size} 字节"
                )
                test_results.append(("获取文件信息", True))
            else:
                logger.error("❌ 获取文件信息失败")
                test_results.append(("获取文件信息", False))
        except Exception as e:
            logger.error(f"❌ 获取文件信息异常: {e}")
            test_results.append(("获取文件信息", False))
    else:
        logger.warning("⚠️ 没有测试文件，跳过文件信息测试")
        test_results.append(("获取文件信息", False))

    # 测试6: 文件下载（只下载小文件）
    if test_file and test_file.size < 1024 * 1024:  # 只下载小于1MB的文件
        logger.info(f"\n6️⃣ 测试文件下载: {test_file.name}")
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                file_id = test_file.ext.get("file_id", test_file.fid)

                result = drive.download_file(
                    file_id, filedir=temp_dir, filename="test_download"
                )
                if result:
                    downloaded_file = os.path.join(temp_dir, "test_download")
                    if os.path.exists(downloaded_file):
                        logger.info("✅ 文件下载成功")
                        test_results.append(("文件下载", True))
                    else:
                        logger.error("❌ 下载的文件不存在")
                        test_results.append(("文件下载", False))
                else:
                    logger.error("❌ 文件下载失败")
                    test_results.append(("文件下载", False))
        except Exception as e:
            logger.error(f"❌ 文件下载异常: {e}")
            test_results.append(("文件下载", False))
    else:
        logger.warning("⚠️ 没有合适的测试文件或文件太大，跳过下载测试")
        test_results.append(("文件下载", False))

    # 测试7: 搜索功能
    logger.info(f"\n7️⃣ 测试搜索功能: {test_dataset_id}")
    try:
        results = drive.search("train", fid=test_dataset_id)
        logger.info(f"✅ 搜索完成，找到 {len(results)} 个结果")
        test_results.append(("搜索功能", True))
    except Exception as e:
        logger.error(f"❌ 搜索功能异常: {e}")
        test_results.append(("搜索功能", False))

    # 测试8: 测试只读操作（应该失败）
    logger.info("\n8️⃣ 测试只读平台限制...")
    try:
        # 测试创建目录（应该失败）
        mkdir_result = drive.mkdir("test", "new_dir")
        if not mkdir_result:
            logger.info("✅ 正确拒绝了创建目录操作")
            test_results.append(("只读限制-创建目录", True))
        else:
            logger.warning("⚠️ 意外允许了创建目录操作")
            test_results.append(("只读限制-创建目录", False))

        # 测试文件上传（应该失败）
        upload_result = drive.upload_file("nonexistent.txt", "test")
        if not upload_result:
            logger.info("✅ 正确拒绝了文件上传操作")
            test_results.append(("只读限制-文件上传", True))
        else:
            logger.warning("⚠️ 意外允许了文件上传操作")
            test_results.append(("只读限制-文件上传", False))

        # 测试删除操作（应该失败）
        delete_result = drive.delete("test")
        if not delete_result:
            logger.info("✅ 正确拒绝了删除操作")
            test_results.append(("只读限制-删除操作", True))
        else:
            logger.warning("⚠️ 意外允许了删除操作")
            test_results.append(("只读限制-删除操作", False))

    except Exception as e:
        logger.error(f"❌ 只读限制测试异常: {e}")
        test_results.append(("只读限制-创建目录", False))
        test_results.append(("只读限制-文件上传", False))
        test_results.append(("只读限制-删除操作", False))

    # 输出测试结果汇总
    logger.info("\n📊 天池测试结果汇总:")
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
    logger.info("\n🎮 天池驱动交互式演示")
    logger.info("=" * 50)

    # 创建驱动实例
    drive = create_tianchi_drive()
    if not drive:
        logger.error("❌ 无法创建驱动实例，退出演示")
        return

    # 登录
    logger.info("\n🔐 正在登录天池...")
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
        print("\n天池可用操作:")
        print("1. 浏览数据集文件")
        print("2. 浏览数据集目录")
        print("3. 下载文件")
        print("4. 搜索文件")
        print("5. 检查数据集存在性")
        print("6. 下载整个数据集")
        print("7. 退出")

        choice = input("\n请选择操作 (1-7): ").strip()

        if choice == "1":
            dataset_id = input("请输入数据集ID: ").strip()
            if dataset_id:
                try:
                    files = drive.get_file_list(dataset_id)
                    logger.info(f"\n📁 数据集文件列表 (共 {len(files)} 个):")
                    for i, file in enumerate(files[:20], 1):  # 只显示前20个
                        logger.info(f"  {i}. {file.name} ({file.size} 字节)")
                    if len(files) > 20:
                        logger.info(f"  ... 还有 {len(files) - 20} 个文件")
                except Exception as e:
                    logger.error(f"❌ 获取文件列表失败: {e}")
            else:
                logger.error("❌ 数据集ID不能为空")

        elif choice == "2":
            dataset_id = input("请输入数据集ID: ").strip()
            if dataset_id:
                try:
                    dirs = drive.get_dir_list(dataset_id)
                    logger.info(f"\n📂 数据集目录列表 (共 {len(dirs)} 个):")
                    for i, dir in enumerate(dirs[:20], 1):  # 只显示前20个
                        logger.info(f"  {i}. {dir.name}")
                    if len(dirs) > 20:
                        logger.info(f"  ... 还有 {len(dirs) - 20} 个目录")
                except Exception as e:
                    logger.error(f"❌ 获取目录列表失败: {e}")
            else:
                logger.error("❌ 数据集ID不能为空")

        elif choice == "3":
            file_id = input("请输入文件ID: ").strip()
            download_dir = (
                input("请输入下载目录 (默认: ./downloads): ").strip() or "./downloads"
            )
            filename = input("请输入保存文件名 (可选): ").strip() or None

            if file_id:
                try:
                    result = drive.download_file(
                        file_id, filedir=download_dir, filename=filename
                    )
                    if result:
                        logger.info(f"✅ 文件下载成功到: {download_dir}")
                    else:
                        logger.error("❌ 文件下载失败")
                except Exception as e:
                    logger.error(f"❌ 下载文件异常: {e}")
            else:
                logger.error("❌ 文件ID不能为空")

        elif choice == "4":
            dataset_id = input("请输入数据集ID: ").strip()
            keyword = input("请输入搜索关键词: ").strip()
            if dataset_id and keyword:
                try:
                    results = drive.search(keyword, fid=dataset_id)
                    logger.info(f"\n🔍 搜索结果 (共 {len(results)} 个):")
                    for i, file in enumerate(results[:10], 1):  # 只显示前10个
                        logger.info(f"  {i}. {file.name} ({file.size} 字节)")
                    if len(results) > 10:
                        logger.info(f"  ... 还有 {len(results) - 10} 个结果")
                except Exception as e:
                    logger.error(f"❌ 搜索失败: {e}")
            else:
                logger.error("❌ 数据集ID和搜索关键词不能为空")

        elif choice == "5":
            dataset_id = input("请输入数据集ID: ").strip()
            if dataset_id:
                try:
                    exists = drive.exist(dataset_id)
                    if exists:
                        logger.info(f"✅ 数据集 {dataset_id} 存在")
                    else:
                        logger.info(f"❌ 数据集 {dataset_id} 不存在")
                except Exception as e:
                    logger.error(f"❌ 检查数据集存在性失败: {e}")
            else:
                logger.error("❌ 数据集ID不能为空")

        elif choice == "6":
            dataset_id = input("请输入数据集ID: ").strip()
            download_dir = (
                input("请输入下载目录 (默认: ./datasets): ").strip() or "./datasets"
            )

            if dataset_id:
                try:
                    logger.info("⚠️ 警告：下载整个数据集可能需要很长时间")
                    confirm = input("确认下载？(y/N): ").strip().lower()
                    if confirm == "y":
                        result = drive.download_dir(dataset_id, filedir=download_dir)
                        if result:
                            logger.info(f"✅ 数据集下载完成到: {download_dir}")
                        else:
                            logger.error("❌ 数据集下载失败")
                    else:
                        logger.info("取消下载")
                except Exception as e:
                    logger.error(f"❌ 下载数据集异常: {e}")
            else:
                logger.error("❌ 数据集ID不能为空")

        elif choice == "7":
            logger.info("👋 退出交互式演示")
            break

        else:
            print("❌ 无效选择，请输入 1-7")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="天池驱动测试和演示")
    parser.add_argument("--test", action="store_true", help="运行完整测试")
    parser.add_argument("--interactive", action="store_true", help="运行交互式演示")

    args = parser.parse_args()

    if args.test:
        logger.info("🚀 开始天池驱动完整测试")

        drive = create_tianchi_drive()
        if drive:
            run_comprehensive_test(drive)

        logger.info("\n🎉 天池驱动测试完成!")

    elif args.interactive:
        run_interactive_demo()

    else:
        parser.print_help()
        logger.info("\n💡 使用提示:")
        logger.info("  python example.py --test        # 运行完整测试")
        logger.info("  python example.py --interactive # 运行交互式演示")
        logger.info("\n📝 注意事项:")
        logger.info("  - 天池是只读平台，不支持上传、创建、删除操作")
        logger.info("  - 数据集ID为数字格式")
        logger.info("  - 需要配置有效的Cookie和CSRF Token进行认证")


if __name__ == "__main__":
    main()
