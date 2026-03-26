#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenXLab驱动测试和演示脚本

使用方法:
    python example.py --test          # 运行完整测试
    python example.py --interactive   # 运行交互式演示
    python example.py --help         # 显示帮助信息

配置方法:
    # 使用nltsecret配置（推荐）
    nltsecret set fundrive openxlab opendatalab_session "your_session_cookie"
    nltsecret set fundrive openxlab ssouid "your_ssouid_cookie"

    # 或者设置环境变量
    export OPENXLAB_SESSION="your_session_cookie"
    export OPENXLAB_SSOUID="your_ssouid_cookie"

注意：OpenXLab是只读平台，主要用于数据集下载和浏览
"""

import argparse
import os
import tempfile

from nltlog import getLogger

from fundrive.drives.openxlab import OpenXLabDrive

logger = getLogger("fundrive.openxlab.example")


def create_openxlab_drive():
    """创建OpenXLab驱动实例"""
    try:
        # 尝试从配置或环境变量获取凭据
        drive = OpenXLabDrive()
        logger.info("✅ 成功创建OpenXLabDrive实例")
        return drive
    except Exception as e:
        logger.error(f"❌ 创建OpenXLabDrive实例失败: {e}")
        logger.info("请确保已正确配置OpenXLab认证信息:")
        logger.info(
            "nltsecret set fundrive openxlab opendatalab_session 'your_session_cookie'"
        )
        logger.info("nltsecret set fundrive openxlab ssouid 'your_ssouid_cookie'")
        return None


def run_comprehensive_test(drive):
    """运行完整的驱动功能测试"""
    logger.info("\n🧪 开始OpenXLab完整功能测试...")

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

    # 测试数据集名称（使用一个公开的测试数据集）
    test_dataset = "OpenDataLab/MNIST"  # 示例数据集

    # 测试2: 检查数据集是否存在
    logger.info(f"\n2️⃣ 测试数据集存在性检查: {test_dataset}")
    try:
        exists = drive.exist(test_dataset)
        if exists:
            logger.info("✅ 数据集存在")
            test_results.append(("数据集存在检查", True))
        else:
            logger.warning("⚠️ 测试数据集不存在，将使用其他数据集")
            test_results.append(("数据集存在检查", False))
            # 尝试其他数据集
            test_dataset = "OpenMMLab/COCO"
    except Exception as e:
        logger.error(f"❌ 数据集存在检查失败: {e}")
        test_results.append(("数据集存在检查", False))

    # 测试3: 获取数据集文件列表
    logger.info(f"\n3️⃣ 测试获取文件列表: {test_dataset}")
    try:
        files = drive.get_file_list(test_dataset)
        logger.info(f"✅ 获取到 {len(files)} 个文件")
        test_results.append(("获取文件列表", True))

        # 保存第一个文件用于后续测试
        test_file = files[0] if files else None

    except Exception as e:
        logger.error(f"❌ 获取文件列表失败: {e}")
        test_results.append(("获取文件列表", False))
        test_file = None

    # 测试4: 获取数据集目录列表
    logger.info(f"\n4️⃣ 测试获取目录列表: {test_dataset}")
    try:
        dirs = drive.get_dir_list(test_dataset)
        logger.info(f"✅ 获取到 {len(dirs)} 个目录")
        test_results.append(("获取目录列表", True))
    except Exception as e:
        logger.error(f"❌ 获取目录列表失败: {e}")
        test_results.append(("获取目录列表", False))

    # 测试5: 获取文件信息
    if test_file:
        logger.info(f"\n5️⃣ 测试获取文件信息: {test_file.name}")
        try:
            # 构建文件ID
            dataset_id = test_file.ext.get("dataset_id", "")
            file_path = test_file.ext.get("path", "")
            file_fid = f"{dataset_id}{file_path}"

            file_info = drive.get_file_info(file_fid)
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
                # 构建文件ID
                dataset_id = test_file.ext.get("dataset_id", "")
                file_path = test_file.ext.get("path", "")
                file_fid = f"{dataset_id}{file_path}"

                result = drive.download_file(
                    file_fid, filedir=temp_dir, filename="test_download"
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
    logger.info(f"\n7️⃣ 测试搜索功能: {test_dataset}")
    try:
        results = drive.search("test", fid=test_dataset)
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
    logger.info("\n📊 OpenXLab测试结果汇总:")
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
    logger.info("\n🎮 OpenXLab驱动交互式演示")
    logger.info("=" * 50)

    # 创建驱动实例
    drive = create_openxlab_drive()
    if not drive:
        logger.error("❌ 无法创建驱动实例，退出演示")
        return

    # 登录
    logger.info("\n🔐 正在登录OpenXLab...")
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
        print("\nOpenXLab可用操作:")
        print("1. 浏览数据集文件")
        print("2. 浏览数据集目录")
        print("3. 下载文件")
        print("4. 搜索文件")
        print("5. 检查数据集存在性")
        print("6. 退出")

        choice = input("\n请选择操作 (1-6): ").strip()

        if choice == "1":
            dataset_name = input(
                "请输入数据集名称 (格式: owner/dataset_name): "
            ).strip()
            if dataset_name:
                try:
                    files = drive.get_file_list(dataset_name)
                    logger.info(f"\n📁 数据集文件列表 (共 {len(files)} 个):")
                    for i, file in enumerate(files[:20], 1):  # 只显示前20个
                        logger.info(f"  {i}. {file.name} ({file.size} 字节)")
                    if len(files) > 20:
                        logger.info(f"  ... 还有 {len(files) - 20} 个文件")
                except Exception as e:
                    logger.error(f"❌ 获取文件列表失败: {e}")
            else:
                logger.error("❌ 数据集名称不能为空")

        elif choice == "2":
            dataset_name = input(
                "请输入数据集名称 (格式: owner/dataset_name): "
            ).strip()
            if dataset_name:
                try:
                    dirs = drive.get_dir_list(dataset_name)
                    logger.info(f"\n📂 数据集目录列表 (共 {len(dirs)} 个):")
                    for i, dir in enumerate(dirs[:20], 1):  # 只显示前20个
                        logger.info(f"  {i}. {dir.name}")
                    if len(dirs) > 20:
                        logger.info(f"  ... 还有 {len(dirs) - 20} 个目录")
                except Exception as e:
                    logger.error(f"❌ 获取目录列表失败: {e}")
            else:
                logger.error("❌ 数据集名称不能为空")

        elif choice == "3":
            dataset_name = input(
                "请输入数据集名称 (格式: owner/dataset_name): "
            ).strip()
            file_path = input("请输入文件路径 (如: /data/train.txt): ").strip()
            download_dir = (
                input("请输入下载目录 (默认: ./downloads): ").strip() or "./downloads"
            )

            if dataset_name and file_path:
                try:
                    # 构建文件ID
                    file_fid = f"{dataset_name}{file_path}"
                    result = drive.download_file(file_fid, filedir=download_dir)
                    if result:
                        logger.info(f"✅ 文件下载成功到: {download_dir}")
                    else:
                        logger.error("❌ 文件下载失败")
                except Exception as e:
                    logger.error(f"❌ 下载文件异常: {e}")
            else:
                logger.error("❌ 数据集名称和文件路径不能为空")

        elif choice == "4":
            dataset_name = input(
                "请输入数据集名称 (格式: owner/dataset_name): "
            ).strip()
            keyword = input("请输入搜索关键词: ").strip()
            if dataset_name and keyword:
                try:
                    results = drive.search(keyword, fid=dataset_name)
                    logger.info(f"\n🔍 搜索结果 (共 {len(results)} 个):")
                    for i, file in enumerate(results[:10], 1):  # 只显示前10个
                        logger.info(f"  {i}. {file.name} ({file.size} 字节)")
                    if len(results) > 10:
                        logger.info(f"  ... 还有 {len(results) - 10} 个结果")
                except Exception as e:
                    logger.error(f"❌ 搜索失败: {e}")
            else:
                logger.error("❌ 数据集名称和搜索关键词不能为空")

        elif choice == "5":
            dataset_name = input(
                "请输入数据集名称 (格式: owner/dataset_name): "
            ).strip()
            if dataset_name:
                try:
                    exists = drive.exist(dataset_name)
                    if exists:
                        logger.info(f"✅ 数据集 {dataset_name} 存在")
                    else:
                        logger.info(f"❌ 数据集 {dataset_name} 不存在")
                except Exception as e:
                    logger.error(f"❌ 检查数据集存在性失败: {e}")
            else:
                logger.error("❌ 数据集名称不能为空")

        elif choice == "6":
            logger.info("👋 退出交互式演示")
            break

        else:
            print("❌ 无效选择，请输入 1-6")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="OpenXLab驱动测试和演示")
    parser.add_argument("--test", action="store_true", help="运行完整测试")
    parser.add_argument("--interactive", action="store_true", help="运行交互式演示")

    args = parser.parse_args()

    if args.test:
        logger.info("🚀 开始OpenXLab驱动完整测试")

        drive = create_openxlab_drive()
        if drive:
            run_comprehensive_test(drive)

        logger.info("\n🎉 OpenXLab驱动测试完成!")

    elif args.interactive:
        run_interactive_demo()

    else:
        parser.print_help()
        logger.info("\n💡 使用提示:")
        logger.info("  python example.py --test        # 运行完整测试")
        logger.info("  python example.py --interactive # 运行交互式演示")
        logger.info("\n📝 注意事项:")
        logger.info("  - OpenXLab是只读平台，不支持上传、创建、删除操作")
        logger.info("  - 数据集名称格式：owner/dataset_name")
        logger.info("  - 需要配置有效的Cookie进行认证")


if __name__ == "__main__":
    main()
