#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub驱动示例和测试脚本

本脚本演示如何使用GitHub驱动进行文件操作，包括：
- GitHub认证配置
- 仓库文件管理
- 文件上传下载
- 版本控制操作
- 搜索和分享功能

使用方法:
1. 快速演示: python example.py --demo
2. 完整测试: python example.py --test
3. 交互式演示: python example.py --interactive

配置方法:
1. 使用funsecret: funsecret set fundrive.github.access_token "your_token"
2. 环境变量: export GITHUB_ACCESS_TOKEN="your_token"
3. 代码中直接设置

作者: FunDrive Team
"""

import argparse
import os
import tempfile
from typing import List


from fundrive.drives.github import GitHubDrive
from fundrive.core import DriveFile


def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 60)
    if title:
        print(f" {title} ")
        print("=" * 60)


def print_files(files: List[DriveFile], title: str = "文件列表"):
    """打印文件列表"""
    print(f"\n📁 {title} (共 {len(files)} 个):")
    if not files:
        print("  (空)")
        return

    for i, file in enumerate(files, 1):
        file_type = "📁" if file.ext.get("type") == "folder" else "📄"
        size_str = f"{file.size:,} bytes" if file.size > 0 else "-"
        print(f"  {i:2d}. {file_type} {file.name}")
        print(f"      路径: {file.fid}")
        print(f"      大小: {size_str}")
        if file.ext.get("sha"):
            print(f"      SHA: {file.ext['sha'][:8]}...")


def create_test_file(filename: str = "github_test.txt", content: str = None) -> str:
    """创建测试文件"""
    if content is None:
        content = f"""GitHub云存储测试文件
文件名: {filename}
创建时间: {os.popen("date").read().strip()}

GitHub特性:
- 版本控制
- 协作开发
- 代码托管
- 文档管理
- 开源社区
"""

    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📄 创建测试文件: {filepath}")
    return filepath


def demo_basic_operations(drive: GitHubDrive):
    """演示基本操作"""
    print_separator("基本操作演示")

    # 登录
    print("🔐 正在连接GitHub...")
    if drive.login():
        print("✅ GitHub连接成功")
    else:
        print("❌ GitHub连接失败")
        return False

    # 获取仓库信息
    print("\n💾 获取仓库信息...")
    quota_info = drive.get_quota()
    if quota_info:
        print("✅ 仓库信息:")
        print(f"   仓库: {quota_info.get('repo_name', 'N/A')}")
        print(f"   描述: {quota_info.get('description', '无')}")
        print(f"   大小: {quota_info.get('size_mb', 0)} MB")
        print(f"   默认分支: {quota_info.get('default_branch', 'main')}")
        print(f"   语言: {quota_info.get('language', '未知')}")
        print(f"   星标: {quota_info.get('stars', 0)}")

    # 列出根目录文件
    print("\n📄 获取根目录文件列表...")
    files = drive.get_file_list("")
    print_files(files, "根目录文件")

    # 列出根目录子目录
    print("\n📁 获取根目录子目录列表...")
    dirs = drive.get_dir_list("")
    print_files(dirs, "根目录子目录")

    return True


def demo_file_operations(drive: GitHubDrive):
    """演示文件操作"""
    print_separator("文件操作演示")

    # 创建测试文件
    test_file = create_test_file("fundrive_test.md")
    test_filename = "fundrive_github_test.md"

    # 上传文件
    print(f"\n📤 上传文件: {test_filename}")
    success = drive.upload_file(
        filepath=test_file,
        fid="test",
        filename=test_filename,
        commit_message="Add test file via FunDrive",
    )

    if success:
        print("✅ 文件上传成功")

        # 获取文件信息
        print(f"\n📋 获取文件信息: test/{test_filename}")
        file_info = drive.get_file_info(f"test/{test_filename}")
        if file_info:
            print("✅ 文件信息:")
            print(f"   名称: {file_info.name}")
            print(f"   大小: {file_info.size} bytes")
            print(f"   SHA: {file_info.ext.get('sha', 'N/A')[:8]}...")

            # 创建分享链接
            share_url = drive.create_share_link(f"test/{test_filename}")
            if share_url:
                print(f"   分享链接: {share_url}")

        # 下载文件
        print(f"\n📥 下载文件: test/{test_filename}")
        download_dir = tempfile.mkdtemp()
        success = drive.download_file(
            fid=f"test/{test_filename}",
            filedir=download_dir,
            filename="downloaded_test.md",
        )

        if success:
            print(f"✅ 文件下载成功: {download_dir}/downloaded_test.md")

    # 清理测试文件
    try:
        os.remove(test_file)
    except:
        pass

    return success


def demo_search_features(drive: GitHubDrive):
    """演示搜索功能"""
    print_separator("搜索功能演示")

    # 搜索README文件
    print("🔍 搜索README文件...")
    results = drive.search("README")
    print_files(results, "搜索结果")

    # 搜索Python文件
    print("\n🔍 搜索Python文件...")
    results = drive.search("*.py")
    print_files(results[:5], "Python文件 (前5个)")

    return True


def run_quick_demo():
    """运行快速演示"""
    print("🚀 GitHub驱动快速演示")
    print("=" * 50)

    # 检查配置
    access_token = os.getenv("GITHUB_ACCESS_TOKEN")
    repo_owner = os.getenv("GITHUB_REPO_OWNER")
    repo_name = os.getenv("GITHUB_REPO_NAME")

    if not all([access_token, repo_owner, repo_name]):
        print("⚠️ 未找到GitHub配置信息")
        print("请设置以下环境变量:")
        print("  export GITHUB_ACCESS_TOKEN='your_access_token'")
        print("  export GITHUB_REPO_OWNER='your_username'")
        print("  export GITHUB_REPO_NAME='your_repo_name'")
        print("或使用funsecret配置")
        return

    # 创建驱动实例
    drive = GitHubDrive(
        access_token=access_token, repo_owner=repo_owner, repo_name=repo_name
    )

    # 运行演示
    if demo_basic_operations(drive):
        demo_search_features(drive)

    print_separator("演示完成")
    print("✅ GitHub驱动快速演示完成！")


def run_full_test():
    """运行完整测试"""
    print("🧪 GitHub驱动完整测试")
    print("=" * 50)

    # 检查配置
    access_token = os.getenv("GITHUB_ACCESS_TOKEN")
    repo_owner = os.getenv("GITHUB_REPO_OWNER")
    repo_name = os.getenv("GITHUB_REPO_NAME")

    if not all([access_token, repo_owner, repo_name]):
        print("⚠️ 未找到GitHub配置信息")
        return False

    # 创建驱动实例
    drive = GitHubDrive(
        access_token=access_token, repo_owner=repo_owner, repo_name=repo_name
    )

    # 运行测试
    success = True

    if demo_basic_operations(drive):
        success &= demo_file_operations(drive)
        demo_search_features(drive)
    else:
        success = False

    print_separator("测试完成")
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")

    return success


def run_interactive_demo():
    """运行交互式演示"""
    print("🎮 GitHub驱动交互式演示")
    print("=" * 50)

    # 获取配置
    access_token = input("请输入GitHub访问令牌: ").strip()
    repo_owner = input("请输入仓库所有者: ").strip()
    repo_name = input("请输入仓库名称: ").strip()

    if not all([access_token, repo_owner, repo_name]):
        print("❌ 配置信息不完整")
        return

    # 创建驱动实例
    drive = GitHubDrive(
        access_token=access_token, repo_owner=repo_owner, repo_name=repo_name
    )

    # 登录
    if not drive.login():
        print("❌ 连接失败")
        return

    while True:
        print("\n" + "=" * 40)
        print("请选择操作:")
        print("1. 查看仓库信息")
        print("2. 列出文件")
        print("3. 列出目录")
        print("4. 上传文件")
        print("5. 下载文件")
        print("6. 搜索文件")
        print("7. 创建分享链接")
        print("0. 退出")

        choice = input("\n请输入选项 (0-7): ").strip()

        if choice == "0":
            break
        elif choice == "1":
            quota = drive.get_quota()
            if quota:
                print("\n📊 仓库信息:")
                for key, value in quota.items():
                    print(f"   {key}: {value}")
        elif choice == "2":
            path = input("请输入目录路径 (默认根目录): ").strip()
            files = drive.get_file_list(path)
            print_files(files, f"文件列表 ({path or 'root'})")
        elif choice == "3":
            path = input("请输入目录路径 (默认根目录): ").strip()
            dirs = drive.get_dir_list(path)
            print_files(dirs, f"目录列表 ({path or 'root'})")
        elif choice == "4":
            filepath = input("请输入本地文件路径: ").strip()
            if os.path.exists(filepath):
                target_path = input("请输入目标路径: ").strip()
                filename = input("请输入文件名 (默认使用原文件名): ").strip()
                success = drive.upload_file(filepath, target_path, filename or None)
                print("✅ 上传成功" if success else "❌ 上传失败")
            else:
                print("❌ 文件不存在")
        elif choice == "5":
            file_path = input("请输入文件路径: ").strip()
            download_dir = input("请输入下载目录 (默认当前目录): ").strip() or "."
            success = drive.download_file(file_path, download_dir)
            print("✅ 下载成功" if success else "❌ 下载失败")
        elif choice == "6":
            keyword = input("请输入搜索关键词: ").strip()
            if keyword:
                results = drive.search(keyword)
                print_files(results, f"搜索结果: {keyword}")
        elif choice == "7":
            file_path = input("请输入文件路径: ").strip()
            if file_path:
                share_url = drive.create_share_link(file_path)
                print(f"🔗 分享链接: {share_url}" if share_url else "❌ 生成失败")
        else:
            print("❌ 无效选项")

    print("\n👋 再见！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="GitHub驱动示例和测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python example.py --demo          # 快速演示
  python example.py --test          # 完整测试
  python example.py --interactive   # 交互式演示

配置方法:
  # 使用环境变量
  export GITHUB_ACCESS_TOKEN="your_access_token"
  export GITHUB_REPO_OWNER="your_username"
  export GITHUB_REPO_NAME="your_repo_name"
  
  # 使用funsecret (推荐)
  funsecret set fundrive.github.access_token "your_access_token"
  funsecret set fundrive.github.repo_owner "your_username"
  funsecret set fundrive.github.repo_name "your_repo_name"
        """,
    )

    parser.add_argument("--demo", action="store_true", help="运行快速演示")

    parser.add_argument("--test", action="store_true", help="运行完整测试")

    parser.add_argument("--interactive", action="store_true", help="运行交互式演示")

    args = parser.parse_args()

    if args.test:
        run_full_test()
    elif args.interactive:
        run_interactive_demo()
    elif args.demo:
        run_quick_demo()
    else:
        # 默认运行快速演示
        print("未指定运行模式，执行快速演示...")
        print("使用 --help 查看所有选项")
        run_quick_demo()


if __name__ == "__main__":
    main()
