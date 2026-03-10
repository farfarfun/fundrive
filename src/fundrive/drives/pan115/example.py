#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
115网盘驱动测试和演示脚本

使用方法:
    python example.py --test          # 运行完整测试
    python example.py --interactive   # 运行交互式演示
    python example.py --help         # 显示帮助信息

配置方法:
    # 使用funsecret配置（推荐）
    funsecret set fundrive pan115 uid "your_uid"
    funsecret set fundrive pan115 cid "your_cid"
    funsecret set fundrive pan115 seid "your_seid"

    # 凭据获取方式：
    # 登录 https://115.com/ 后，从浏览器Cookie中获取 UID、CID、SEID 三个值
"""

import argparse
import os
import tempfile

from nltlog import getLogger

from fundrive.drives.pan115 import Pan115Drive

logger = getLogger("fundrive.pan115.example")


def create_pan115_drive():
    """创建115网盘驱动实例"""
    try:
        drive = Pan115Drive()
        logger.info("成功创建Pan115Drive实例")
        return drive
    except Exception as e:
        logger.error(f"创建Pan115Drive实例失败: {e}")
        logger.info("请确保已正确配置凭据:")
        logger.info("funsecret set fundrive pan115 uid 'your_uid'")
        logger.info("funsecret set fundrive pan115 cid 'your_cid'")
        logger.info("funsecret set fundrive pan115 seid 'your_seid'")
        return None


def run_comprehensive_test(drive):
    """运行完整的驱动功能测试"""
    logger.info("\n开始115网盘完整功能测试...")

    test_results = []

    # 测试1: 登录认证
    logger.info("\n1. 测试登录认证...")
    try:
        result = drive.login()
        if result:
            logger.info("登录成功")
            test_results.append(("登录认证", True))
        else:
            logger.error("登录失败")
            test_results.append(("登录认证", False))
            return test_results
    except Exception as e:
        logger.error(f"登录异常: {e}")
        test_results.append(("登录认证", False))
        return test_results

    # 测试2: 获取空间信息
    logger.info("\n2. 测试获取空间信息...")
    try:
        quota = drive.get_quota()
        total_gb = quota["total"] / (1024**3)
        used_gb = quota["used"] / (1024**3)
        free_gb = quota["free"] / (1024**3)
        logger.info(f"总空间: {total_gb:.2f} GB, 已用: {used_gb:.2f} GB, 剩余: {free_gb:.2f} GB")
        test_results.append(("获取空间信息", True))
    except Exception as e:
        logger.error(f"获取空间信息失败: {e}")
        test_results.append(("获取空间信息", False))

    # 测试3: 获取根目录文件列表
    logger.info("\n3. 测试获取文件列表...")
    try:
        files = drive.get_file_list("0")
        logger.info(f"获取到 {len(files)} 个文件")
        for f in files[:5]:
            logger.info(f"  - {f.name} ({f.size} 字节)")
        test_results.append(("获取文件列表", True))
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        test_results.append(("获取文件列表", False))

    # 测试4: 获取根目录列表
    logger.info("\n4. 测试获取目录列表...")
    try:
        dirs = drive.get_dir_list("0")
        logger.info(f"获取到 {len(dirs)} 个目录")
        for d in dirs[:5]:
            logger.info(f"  - {d.name}")
        test_results.append(("获取目录列表", True))
    except Exception as e:
        logger.error(f"获取目录列表失败: {e}")
        test_results.append(("获取目录列表", False))

    # 测试5: 创建测试目录
    test_dir_name = "fundrive_test_dir"
    logger.info(f"\n5. 测试创建目录: {test_dir_name}")
    test_dir_fid = None
    try:
        test_dir_fid = drive.mkdir("0", test_dir_name)
        if test_dir_fid:
            logger.info(f"目录创建成功, fid={test_dir_fid}")
            test_results.append(("创建目录", True))
        else:
            logger.error("目录创建失败")
            test_results.append(("创建目录", False))
    except Exception as e:
        logger.error(f"创建目录失败: {e}")
        test_results.append(("创建目录", False))

    # 测试6: 创建测试文件并上传
    logger.info("\n6. 测试文件上传...")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("115网盘测试文件内容\nfundrive test")
        temp_file = f.name

    try:
        target_fid = test_dir_fid or "0"
        result = drive.upload_file(temp_file, target_fid)
        if result:
            logger.info("文件上传成功")
            test_results.append(("文件上传", True))
        else:
            logger.error("文件上传失败")
            test_results.append(("文件上传", False))
    except Exception as e:
        logger.error(f"文件上传异常: {e}")
        test_results.append(("文件上传", False))
    finally:
        os.unlink(temp_file)

    # 测试7: 搜索文件
    logger.info("\n7. 测试搜索文件...")
    try:
        results = drive.search("fundrive")
        logger.info(f"搜索到 {len(results)} 个结果")
        test_results.append(("搜索文件", True))
    except Exception as e:
        logger.error(f"搜索文件失败: {e}")
        test_results.append(("搜索文件", False))

    # 测试8: 清理测试目录
    logger.info("\n8. 清理测试目录...")
    try:
        if test_dir_fid:
            result = drive.delete(test_dir_fid)
            if result:
                logger.info("测试目录删除成功")
                test_results.append(("删除目录", True))
            else:
                logger.error("测试目录删除失败")
                test_results.append(("删除目录", False))
        else:
            logger.warning("没有测试目录需要删除")
            test_results.append(("删除目录", True))
    except Exception as e:
        logger.error(f"删除目录异常: {e}")
        test_results.append(("删除目录", False))

    # 输出测试结果汇总
    logger.info("\n测试结果汇总:")
    passed = 0
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n总体结果: {passed}/{len(test_results)} 项测试通过")
    return test_results


def run_interactive_demo():
    """运行交互式演示"""
    logger.info("\n115网盘驱动交互式演示")
    logger.info("=" * 50)

    drive = create_pan115_drive()
    if not drive:
        logger.error("无法创建驱动实例，退出演示")
        return

    logger.info("\n正在登录115网盘...")
    try:
        if not drive.login():
            logger.error("登录失败，退出演示")
            return
        logger.info("登录成功!")
    except Exception as e:
        logger.error(f"登录异常: {e}")
        return

    while True:
        print("\n115网盘可用操作:")
        print("1. 查看根目录文件")
        print("2. 查看根目录文件夹")
        print("3. 查看空间使用情况")
        print("4. 搜索文件")
        print("5. 上传文件")
        print("6. 创建文件夹")
        print("7. 退出")

        choice = input("\n请选择操作 (1-7): ").strip()

        if choice == "1":
            try:
                files = drive.get_file_list("0")
                logger.info(f"\n根目录文件列表 (共 {len(files)} 个):")
                for i, file in enumerate(files[:10], 1):
                    logger.info(f"  {i}. {file.name} ({file.size} 字节)")
                if len(files) > 10:
                    logger.info(f"  ... 还有 {len(files) - 10} 个文件")
            except Exception as e:
                logger.error(f"获取文件列表失败: {e}")

        elif choice == "2":
            try:
                dirs = drive.get_dir_list("0")
                logger.info(f"\n根目录文件夹列表 (共 {len(dirs)} 个):")
                for i, d in enumerate(dirs[:10], 1):
                    logger.info(f"  {i}. {d.name}")
                if len(dirs) > 10:
                    logger.info(f"  ... 还有 {len(dirs) - 10} 个文件夹")
            except Exception as e:
                logger.error(f"获取文件夹列表失败: {e}")

        elif choice == "3":
            try:
                quota = drive.get_quota()
                total_gb = quota["total"] / (1024**3)
                used_gb = quota["used"] / (1024**3)
                logger.info(f"\n空间使用情况: {used_gb:.2f} GB / {total_gb:.2f} GB")
            except Exception as e:
                logger.error(f"获取空间信息失败: {e}")

        elif choice == "4":
            keyword = input("请输入搜索关键词: ").strip()
            if keyword:
                try:
                    results = drive.search(keyword)
                    logger.info(f"\n搜索结果 (共 {len(results)} 个):")
                    for i, f in enumerate(results[:10], 1):
                        logger.info(f"  {i}. {f.name} ({f.size} 字节)")
                except Exception as e:
                    logger.error(f"搜索失败: {e}")

        elif choice == "5":
            file_path = input("请输入要上传的文件路径: ").strip()
            if os.path.exists(file_path):
                try:
                    result = drive.upload_file(file_path, "0")
                    if result:
                        logger.info(f"文件 {os.path.basename(file_path)} 上传成功")
                    else:
                        logger.error("文件上传失败")
                except Exception as e:
                    logger.error(f"上传文件异常: {e}")
            else:
                logger.error("文件不存在")

        elif choice == "6":
            dir_name = input("请输入要创建的文件夹名称: ").strip()
            if dir_name:
                try:
                    result = drive.mkdir("0", dir_name)
                    if result:
                        logger.info(f"文件夹 {dir_name} 创建成功")
                    else:
                        logger.error(f"文件夹 {dir_name} 创建失败")
                except Exception as e:
                    logger.error(f"创建文件夹异常: {e}")

        elif choice == "7":
            logger.info("退出交互式演示")
            break

        else:
            print("无效选择，请输入 1-7")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="115网盘驱动测试和演示")
    parser.add_argument("--test", action="store_true", help="运行完整测试")
    parser.add_argument("--interactive", action="store_true", help="运行交互式演示")

    args = parser.parse_args()

    if args.test:
        logger.info("开始115网盘驱动完整测试")
        drive = create_pan115_drive()
        if drive:
            run_comprehensive_test(drive)
        logger.info("\n115网盘驱动测试完成!")

    elif args.interactive:
        run_interactive_demo()

    else:
        parser.print_help()
        logger.info("\n使用提示:")
        logger.info("  python example.py --test        # 运行完整测试")
        logger.info("  python example.py --interactive # 运行交互式演示")


if __name__ == "__main__":
    main()
