#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gitee驱动使用示例

本示例展示如何使用Gitee驱动进行各种文件操作，包括：
- 基本连接和认证
- 文件上传下载
- 目录操作
- 搜索功能
- 分享链接生成

使用前请确保已配置Gitee访问令牌和仓库信息。

作者: FunDrive Team
"""

import os
import sys
import argparse

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

from fundrive.drives.gitee import GiteeDrive


def quick_demo():
    """快速演示Gitee驱动基本功能"""
    print("🚀 Gitee驱动快速演示")
    print("=" * 50)

    # 创建驱动实例
    drive = GiteeDrive()

    # 登录连接
    print("\n1. 连接Gitee...")
    if drive.login():
        print("✅ Gitee连接成功")

        # 获取仓库信息
        print("\n2. 获取仓库信息...")
        quota = drive.get_quota()
        if quota:
            print(f"   仓库: {quota.get('repo_name', 'N/A')}")
            print(f"   描述: {quota.get('description', '无')}")
            print(f"   大小: {quota.get('size_mb', 0)} MB")
            print(f"   星标: {quota.get('stars', 0)}")
            print(f"   语言: {quota.get('language', '未知')}")

        # 列出根目录内容
        print("\n3. 列出根目录内容...")
        files = drive.get_file_list("")
        dirs = drive.get_dir_list("")

        print(f"   找到 {len(dirs)} 个目录:")
        for dir_item in dirs[:5]:  # 只显示前5个
            print(f"   📁 {dir_item.name}")

        print(f"   找到 {len(files)} 个文件:")
        for file in files[:5]:  # 只显示前5个
            print(f"   📄 {file.name} ({file.size} bytes)")

        print("\n✅ 快速演示完成")
    else:
        print("❌ Gitee连接失败，请检查配置")


def file_operations_demo():
    """文件操作演示"""
    print("\n🔧 文件操作演示")
    print("=" * 50)

    drive = GiteeDrive()

    if not drive.login():
        print("❌ 连接失败")
        return

    # 创建测试目录
    print("\n1. 创建测试目录...")
    test_dir = "fundrive_test"
    if drive.mkdir("", test_dir):
        print(f"✅ 目录创建成功: {test_dir}")

    # 上传文本文件
    print("\n2. 上传文本文件...")
    test_content = f"""# FunDrive Gitee测试文件

这是一个通过FunDrive Gitee驱动创建的测试文件。

创建时间: {os.popen("date").read().strip()}
驱动版本: Gitee Drive v1.0.0

## 功能特性
- ✅ 文件上传下载
- ✅ 目录操作
- ✅ 搜索功能
- ✅ 分享链接
- ✅ 版本控制集成

## 使用说明
请参考README.md获取详细使用说明。
"""

    if drive.upload_file(
        filepath=None,
        fid=test_dir,
        filename="test_file.md",
        content=test_content,
        commit_message="Add test file via FunDrive",
    ):
        print("✅ 文件上传成功")

    # 检查文件是否存在
    print("\n3. 检查文件存在性...")
    test_file_path = f"{test_dir}/test_file.md"
    if drive.exist(test_file_path):
        print(f"✅ 文件存在: {test_file_path}")

        # 获取文件信息
        file_info = drive.get_file_info(test_file_path)
        if file_info:
            print(f"   文件大小: {file_info.size} bytes")
            print(f"   SHA: {file_info.ext.get('sha', 'N/A')[:8]}...")

    # 创建分享链接
    print("\n4. 创建分享链接...")
    share_url = drive.create_share_link(test_file_path)
    if share_url:
        print(f"✅ 分享链接: {share_url}")

    # 下载文件
    print("\n5. 下载文件...")
    download_dir = "./downloads"
    if drive.download_file(test_file_path, download_dir, "downloaded_test.md"):
        print(f"✅ 文件下载成功: {download_dir}/downloaded_test.md")

    print("\n✅ 文件操作演示完成")


def search_demo():
    """搜索功能演示"""
    print("\n🔍 搜索功能演示")
    print("=" * 50)

    drive = GiteeDrive()

    if not drive.login():
        print("❌ 连接失败")
        return

    # 搜索README文件
    print("\n1. 搜索README文件...")
    results = drive.search("README")
    print(f"找到 {len(results)} 个结果:")
    for file in results[:5]:  # 只显示前5个
        print(f"   📄 {file.name} - {file.fid}")

    # 搜索Python文件
    print("\n2. 搜索Python文件...")
    results = drive.search(".py")
    print(f"找到 {len(results)} 个Python文件:")
    for file in results[:5]:
        print(f"   🐍 {file.name} - {file.fid}")

    # 搜索配置文件
    print("\n3. 搜索配置文件...")
    results = drive.search("config")
    print(f"找到 {len(results)} 个配置文件:")
    for file in results[:3]:
        print(f"   ⚙️ {file.name} - {file.fid}")

    print("\n✅ 搜索演示完成")


def comprehensive_test():
    """完整功能测试"""
    print("\n🧪 完整功能测试")
    print("=" * 50)

    drive = GiteeDrive()

    # 测试结果统计
    tests = []

    def add_test(name: str, success: bool, details: str = ""):
        tests.append({"name": name, "success": success, "details": details})
        _status = "✅" if success else "❌"
        print(f"{_status} {name}: {details}")

    # 1. 连接测试
    print("\n1. 连接测试...")
    login_success = drive.login()
    add_test(
        "Gitee连接", login_success, "成功连接到仓库" if login_success else "连接失败"
    )

    if not login_success:
        print("\n❌ 连接失败，跳过后续测试")
        return

    # 2. 仓库信息测试
    print("\n2. 仓库信息测试...")
    quota = drive.get_quota()
    add_test(
        "获取仓库信息",
        bool(quota),
        f"仓库大小: {quota.get('size_mb', 0)} MB" if quota else "获取失败",
    )

    # 3. 目录操作测试
    print("\n3. 目录操作测试...")
    test_dir = "fundrive_test_suite"
    mkdir_success = drive.mkdir("", test_dir)
    add_test("创建目录", mkdir_success, f"目录: {test_dir}")

    # 4. 文件上传测试
    print("\n4. 文件上传测试...")
    test_content = "# FunDrive测试\n这是一个测试文件。\n"
    upload_success = drive.upload_file(
        filepath=None, fid=test_dir, filename="test.md", content=test_content
    )
    add_test("文件上传", upload_success, "上传测试文件")

    # 5. 文件存在性测试
    print("\n5. 文件存在性测试...")
    test_file = f"{test_dir}/test.md"
    exist_success = drive.exist(test_file)
    add_test("文件存在检查", exist_success, f"文件: {test_file}")

    # 6. 文件信息测试
    print("\n6. 文件信息测试...")
    file_info = drive.get_file_info(test_file)
    info_success = file_info is not None
    add_test(
        "获取文件信息",
        info_success,
        f"大小: {file_info.size if file_info else 0} bytes",
    )

    # 7. 文件列表测试
    print("\n7. 文件列表测试...")
    files = drive.get_file_list(test_dir)
    list_success = len(files) > 0
    add_test("获取文件列表", list_success, f"找到 {len(files)} 个文件")

    # 8. 搜索测试
    print("\n8. 搜索测试...")
    search_results = drive.search("test")
    search_success = len(search_results) > 0
    add_test("文件搜索", search_success, f"找到 {len(search_results)} 个结果")

    # 9. 分享链接测试
    print("\n9. 分享链接测试...")
    share_url = drive.create_share_link(test_file)
    share_success = bool(share_url)
    add_test("创建分享链接", share_success, "生成分享链接")

    # 10. 文件下载测试
    print("\n10. 文件下载测试...")
    download_dir = "./test_downloads"
    download_success = drive.download_file(
        test_file, download_dir, "downloaded_test.md"
    )
    add_test("文件下载", download_success, f"下载到: {download_dir}")

    # 11. 文件删除测试
    print("\n11. 文件删除测试...")
    delete_success = drive.delete(test_file)
    add_test("文件删除", delete_success, "删除测试文件")

    # 测试结果汇总
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)

    passed = sum(1 for test in tests if test["success"])
    total = len(tests)

    for test in tests:
        status = "✅ PASS" if test["success"] else "❌ FAIL"
        print(f"{status} {test['name']}")

    print(f"\n总计: {passed}/{total} 个测试通过")
    if passed == total:
        print("🎉 所有测试通过！Gitee驱动工作正常")
    else:
        print(f"⚠️  {total - passed} 个测试失败，请检查配置和网络连接")


def interactive_demo():
    """交互式演示"""
    print("\n🎮 Gitee驱动交互式演示")
    print("=" * 50)

    drive = GiteeDrive()

    # 登录
    if not drive.login():
        print("❌ 连接失败，请检查配置")
        return

    print("✅ 连接成功！")

    while True:
        print("\n" + "-" * 30)
        print("请选择操作:")
        print("1. 列出文件和目录")
        print("2. 上传文件")
        print("3. 下载文件")
        print("4. 搜索文件")
        print("5. 获取仓库信息")
        print("6. 创建分享链接")
        print("0. 退出")

        try:
            choice = input("\n请输入选择 (0-6): ").strip()

            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                path = input("请输入目录路径 (留空表示根目录): ").strip()

                print(f"\n📁 目录: {path or '/'}")
                dirs = drive.get_dir_list(path)
                files = drive.get_file_list(path)

                if dirs:
                    print(f"\n子目录 ({len(dirs)} 个):")
                    for i, dir_item in enumerate(dirs, 1):
                        print(f"  {i}. 📁 {dir_item.name}")

                if files:
                    print(f"\n文件 ({len(files)} 个):")
                    for i, file in enumerate(files, 1):
                        size_str = (
                            f"{file.size} bytes"
                            if file.size < 1024
                            else f"{file.size / 1024:.1f} KB"
                        )
                        print(f"  {i}. 📄 {file.name} ({size_str})")

                if not dirs and not files:
                    print("  (空目录)")

            elif choice == "2":
                content = input("请输入文件内容: ").strip()
                filename = input("请输入文件名: ").strip()
                path = input("请输入目标目录 (留空表示根目录): ").strip()

                if content and filename:
                    success = drive.upload_file(
                        filepath=None, fid=path, filename=filename, content=content
                    )
                    if success:
                        print(f"✅ 文件上传成功: {path}/{filename}")
                    else:
                        print("❌ 文件上传失败")
                else:
                    print("❌ 请提供文件内容和文件名")

            elif choice == "3":
                file_path = input("请输入文件路径: ").strip()
                download_dir = (
                    input("请输入下载目录 (默认: ./downloads): ").strip()
                    or "./downloads"
                )

                if file_path:
                    success = drive.download_file(file_path, download_dir)
                    if success:
                        print(f"✅ 文件下载成功: {download_dir}")
                    else:
                        print("❌ 文件下载失败")
                else:
                    print("❌ 请提供文件路径")

            elif choice == "4":
                keyword = input("请输入搜索关键词: ").strip()

                if keyword:
                    results = drive.search(keyword)
                    if results:
                        print(f"\n🔍 找到 {len(results)} 个结果:")
                        for i, file in enumerate(results[:10], 1):  # 只显示前10个
                            print(f"  {i}. 📄 {file.name} - {file.fid}")
                        if len(results) > 10:
                            print(f"  ... 还有 {len(results) - 10} 个结果")
                    else:
                        print("❌ 没有找到匹配的文件")
                else:
                    print("❌ 请提供搜索关键词")

            elif choice == "5":
                quota = drive.get_quota()
                if quota:
                    print("\n📊 仓库信息:")
                    print(f"  名称: {quota.get('repo_name', 'N/A')}")
                    print(f"  描述: {quota.get('description', '无')}")
                    print(f"  大小: {quota.get('size_mb', 0)} MB")
                    print(f"  星标: {quota.get('stars', 0)}")
                    print(f"  分支: {quota.get('default_branch', 'master')}")
                    print(f"  语言: {quota.get('language', '未知')}")
                else:
                    print("❌ 获取仓库信息失败")

            elif choice == "6":
                file_path = input("请输入文件路径: ").strip()

                if file_path:
                    share_url = drive.create_share_link(file_path)
                    if share_url:
                        print(f"✅ 分享链接: {share_url}")
                    else:
                        print("❌ 生成分享链接失败")
                else:
                    print("❌ 请提供文件路径")

            else:
                print("❌ 无效选择，请重试")

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 操作失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Gitee驱动使用示例")
    parser.add_argument("--demo", action="store_true", help="运行快速演示")
    parser.add_argument("--test", action="store_true", help="运行完整测试")
    parser.add_argument("--interactive", action="store_true", help="运行交互式演示")
    parser.add_argument("--file-ops", action="store_true", help="运行文件操作演示")
    parser.add_argument("--search", action="store_true", help="运行搜索演示")

    args = parser.parse_args()

    if args.demo:
        quick_demo()
    elif args.test:
        comprehensive_test()
    elif args.interactive:
        interactive_demo()
    elif args.file_ops:
        file_operations_demo()
    elif args.search:
        search_demo()
    else:
        # 默认运行快速演示
        print("Gitee驱动示例程序")
        print("\n使用方法:")
        print("  python example.py --demo        # 快速演示")
        print("  python example.py --test        # 完整测试")
        print("  python example.py --interactive # 交互式演示")
        print("  python example.py --file-ops    # 文件操作演示")
        print("  python example.py --search      # 搜索演示")
        print("\n配置说明:")
        print("  请先配置Gitee访问令牌和仓库信息:")
        print("  - nltsecret set fundrive.gitee.access_token 'your_token'")
        print("  - nltsecret set fundrive.gitee.repo_owner 'your_username'")
        print("  - nltsecret set fundrive.gitee.repo_name 'your_repo'")
        print("\n或使用环境变量:")
        print("  - export GITEE_ACCESS_TOKEN='your_token'")
        print("  - export GITEE_REPO_OWNER='your_username'")
        print("  - export GITEE_REPO_NAME='your_repo'")

        print("\n正在运行快速演示...")
        quick_demo()


if __name__ == "__main__":
    main()
