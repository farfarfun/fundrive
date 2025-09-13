#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清华云盘驱动示例和测试脚本

本脚本演示如何使用清华云盘驱动进行文件操作，包括：
- 配置分享链接信息
- 浏览文件和目录
- 下载文件和目录
- 搜索文件
- 获取文件信息

使用方法:
1. 快速演示: python example.py --demo
2. 完整测试: python example.py --test
3. 交互式演示: python example.py --interactive

配置方法:
1. 使用funsecret: funsecret set fundrive.tsinghua.share_key "your_share_key"
2. 环境变量: export TSINGHUA_SHARE_KEY="your_share_key"
3. 代码中直接设置

作者: FunDrive Team
"""

import argparse
import os
import sys
from typing import List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

from fundrive.drives.tsinghua import TSingHuaDrive
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
        if file.ext.get("modified"):
            print(f"      修改时间: {file.ext['modified']}")


def demo_basic_operations(drive: TSingHuaDrive):
    """演示基本操作"""
    print_separator("基本操作演示")

    # 登录
    print("🔐 正在登录清华云盘...")
    if drive.login():
        print("✅ 登录成功")
    else:
        print("❌ 登录失败")
        return False

    # 获取根目录信息
    print("\n📁 获取根目录信息...")
    root_info = drive.get_dir_info("")
    if root_info:
        print(f"✅ 根目录: {root_info.name}")

    # 列出根目录文件
    print("\n📄 获取根目录文件列表...")
    files = drive.get_file_list("")
    print_files(files, "根目录文件")

    # 列出根目录子目录
    print("\n📁 获取根目录子目录列表...")
    dirs = drive.get_dir_list("")
    print_files(dirs, "根目录子目录")

    return True


def demo_file_operations(drive: TSingHuaDrive):
    """演示文件操作"""
    print_separator("文件操作演示")

    # 获取文件列表
    files = drive.get_file_list("")
    if not files:
        print("⚠️ 根目录没有文件，跳过文件操作演示")
        return

    # 选择第一个文件进行操作
    test_file = files[0]
    print(f"📄 选择测试文件: {test_file.name}")

    # 检查文件是否存在
    print(f"\n🔍 检查文件是否存在...")
    exists = drive.exist(test_file.fid)
    print(f"✅ 文件存在: {exists}")

    # 获取文件详细信息
    print(f"\n📋 获取文件详细信息...")
    file_info = drive.get_file_info(test_file.fid)
    if file_info:
        print(f"✅ 文件名: {file_info.name}")
        print(f"   大小: {file_info.size:,} bytes")
        print(f"   路径: {file_info.fid}")

    # 下载文件（小文件）
    if test_file.size < 10 * 1024 * 1024:  # 小于10MB
        print(f"\n⬇️ 下载文件到本地...")
        download_dir = "./test_downloads"
        success = drive.download_file(
            fid=test_file.fid, filedir=download_dir, filename=f"test_{test_file.name}"
        )
        if success:
            print(f"✅ 文件下载成功: {download_dir}/test_{test_file.name}")
        else:
            print("❌ 文件下载失败")
    else:
        print(f"⚠️ 文件太大 ({test_file.size:,} bytes)，跳过下载演示")


def demo_directory_operations(drive: TSingHuaDrive):
    """演示目录操作"""
    print_separator("目录操作演示")

    # 获取目录列表
    dirs = drive.get_dir_list("")
    if not dirs:
        print("⚠️ 根目录没有子目录，跳过目录操作演示")
        return

    # 选择第一个目录进行操作
    test_dir = dirs[0]
    print(f"📁 选择测试目录: {test_dir.name}")

    # 检查目录是否存在
    print(f"\n🔍 检查目录是否存在...")
    exists = drive.exist(test_dir.fid)
    print(f"✅ 目录存在: {exists}")

    # 获取目录详细信息
    print(f"\n📋 获取目录详细信息...")
    dir_info = drive.get_dir_info(test_dir.fid)
    if dir_info:
        print(f"✅ 目录名: {dir_info.name}")
        print(f"   路径: {dir_info.fid}")

    # 列出目录内容
    print(f"\n📄 列出目录内文件...")
    sub_files = drive.get_file_list(test_dir.fid)
    print_files(sub_files, f"目录 {test_dir.name} 中的文件")

    print(f"\n📁 列出目录内子目录...")
    sub_dirs = drive.get_dir_list(test_dir.fid)
    print_files(sub_dirs, f"目录 {test_dir.name} 中的子目录")


def demo_search_operations(drive: TSingHuaDrive):
    """演示搜索操作"""
    print_separator("搜索功能演示")

    # 搜索文件
    search_keywords = ["txt", "pdf", "doc", "md"]

    for keyword in search_keywords:
        print(f"\n🔍 搜索包含 '{keyword}' 的文件...")
        results = drive.search(keyword)

        if results:
            print(f"✅ 找到 {len(results)} 个结果:")
            for i, file in enumerate(results[:5], 1):  # 只显示前5个结果
                file_type = "📁" if file.ext.get("type") == "folder" else "📄"
                print(f"  {i}. {file_type} {file.name}")
                print(f"     路径: {file.fid}")

            if len(results) > 5:
                print(f"     ... 还有 {len(results) - 5} 个结果")
        else:
            print(f"❌ 未找到包含 '{keyword}' 的文件")

        # 只测试第一个关键词，避免过多搜索
        break


def demo_readonly_operations(drive: TSingHuaDrive):
    """演示只读操作限制"""
    print_separator("只读操作限制演示")

    print("📝 测试只读操作限制...")

    # 测试创建目录（应该失败）
    print("\n🚫 尝试创建目录（应该失败）...")
    success = drive.mkdir("", "test_folder")
    print(f"   结果: {'成功' if success else '失败（符合预期）'}")

    # 测试删除操作（应该失败）
    print("\n🚫 尝试删除文件（应该失败）...")
    success = drive.delete("/nonexistent")
    print(f"   结果: {'成功' if success else '失败（符合预期）'}")

    # 测试上传文件（应该失败）
    print("\n🚫 尝试上传文件（应该失败）...")
    success = drive.upload_file("nonexistent.txt", "", "test.txt")
    print(f"   结果: {'成功' if success else '失败（符合预期）'}")


def run_quick_demo():
    """运行快速演示"""
    print("🚀 清华云盘驱动快速演示")
    print("=" * 50)

    # 检查配置
    share_key = os.getenv("TSINGHUA_SHARE_KEY")
    if not share_key:
        print("⚠️ 未找到分享链接配置")
        print("请设置环境变量: export TSINGHUA_SHARE_KEY='your_share_key'")
        print(
            "或使用funsecret: funsecret set fundrive.tsinghua.share_key 'your_share_key'"
        )
        return

    # 创建驱动实例
    drive = TSingHuaDrive(share_key=share_key)

    # 运行演示
    if demo_basic_operations(drive):
        demo_readonly_operations(drive)

    print_separator("演示完成")
    print("✅ 清华云盘驱动快速演示完成！")


def run_full_test():
    """运行完整测试"""
    print("🧪 清华云盘驱动完整测试")
    print("=" * 50)

    # 检查配置
    share_key = os.getenv("TSINGHUA_SHARE_KEY")
    if not share_key:
        print("⚠️ 未找到分享链接配置")
        print("请设置环境变量: export TSINGHUA_SHARE_KEY='your_share_key'")
        print(
            "或使用funsecret: funsecret set fundrive.tsinghua.share_key 'your_share_key'"
        )
        return

    # 创建驱动实例
    drive = TSingHuaDrive(share_key=share_key)

    # 运行所有测试
    if demo_basic_operations(drive):
        demo_file_operations(drive)
        demo_directory_operations(drive)
        demo_search_operations(drive)
        demo_readonly_operations(drive)

    print_separator("测试完成")
    print("✅ 清华云盘驱动完整测试完成！")


def run_interactive_demo():
    """运行交互式演示"""
    print("🎮 清华云盘驱动交互式演示")
    print("=" * 50)

    # 获取配置
    share_key = input("请输入分享链接key (或按回车使用环境变量): ").strip()
    if not share_key:
        share_key = os.getenv("TSINGHUA_SHARE_KEY")
        if not share_key:
            print("❌ 未找到分享链接配置")
            return

    password = input("请输入分享密码 (如果没有请按回车): ").strip() or None

    # 创建驱动实例
    drive = TSingHuaDrive(share_key=share_key, password=password)

    # 登录
    if not drive.login():
        print("❌ 登录失败")
        return

    current_path = ""

    while True:
        print(f"\n📁 当前路径: /{current_path}")
        print("\n可用操作:")
        print("1. 列出文件 (ls)")
        print("2. 列出目录 (dir)")
        print("3. 进入目录 (cd)")
        print("4. 下载文件 (download)")
        print("5. 搜索文件 (search)")
        print("6. 获取文件信息 (info)")
        print("7. 返回上级目录 (..)")
        print("0. 退出 (quit)")

        choice = input("\n请选择操作 (0-7): ").strip()

        if choice == "0" or choice.lower() == "quit":
            break
        elif choice == "1" or choice.lower() == "ls":
            files = drive.get_file_list(current_path)
            print_files(files, f"路径 /{current_path} 中的文件")
        elif choice == "2" or choice.lower() == "dir":
            dirs = drive.get_dir_list(current_path)
            print_files(dirs, f"路径 /{current_path} 中的目录")
        elif choice == "3" or choice.lower() == "cd":
            dirs = drive.get_dir_list(current_path)
            if not dirs:
                print("❌ 当前目录没有子目录")
                continue

            print("\n可进入的目录:")
            for i, dir in enumerate(dirs, 1):
                print(f"  {i}. {dir.name}")

            try:
                dir_choice = int(input("请选择目录编号: ")) - 1
                if 0 <= dir_choice < len(dirs):
                    current_path = dirs[dir_choice].fid
                    print(f"✅ 已进入目录: {dirs[dir_choice].name}")
                else:
                    print("❌ 无效的目录编号")
            except ValueError:
                print("❌ 请输入有效的数字")
        elif choice == "4" or choice.lower() == "download":
            files = drive.get_file_list(current_path)
            if not files:
                print("❌ 当前目录没有文件")
                continue

            print("\n可下载的文件:")
            for i, file in enumerate(files, 1):
                size_str = f"{file.size:,} bytes" if file.size > 0 else "-"
                print(f"  {i}. {file.name} ({size_str})")

            try:
                file_choice = int(input("请选择文件编号: ")) - 1
                if 0 <= file_choice < len(files):
                    file = files[file_choice]
                    download_dir = (
                        input("请输入下载目录 (默认: ./downloads): ").strip()
                        or "./downloads"
                    )

                    success = drive.download_file(
                        fid=file.fid, filedir=download_dir, filename=file.name
                    )

                    if success:
                        print(f"✅ 文件下载成功: {download_dir}/{file.name}")
                    else:
                        print("❌ 文件下载失败")
                else:
                    print("❌ 无效的文件编号")
            except ValueError:
                print("❌ 请输入有效的数字")
        elif choice == "5" or choice.lower() == "search":
            keyword = input("请输入搜索关键词: ").strip()
            if keyword:
                results = drive.search(keyword, current_path)
                print_files(results, f"搜索 '{keyword}' 的结果")
        elif choice == "6" or choice.lower() == "info":
            files = drive.get_file_list(current_path)
            dirs = drive.get_dir_list(current_path)
            all_items = files + dirs

            if not all_items:
                print("❌ 当前目录为空")
                continue

            print("\n可查看信息的项目:")
            for i, item in enumerate(all_items, 1):
                item_type = "📁" if item.ext.get("type") == "folder" else "📄"
                print(f"  {i}. {item_type} {item.name}")

            try:
                item_choice = int(input("请选择项目编号: ")) - 1
                if 0 <= item_choice < len(all_items):
                    item = all_items[item_choice]
                    print(f"\n📋 项目信息:")
                    print(f"   名称: {item.name}")
                    print(f"   路径: {item.fid}")
                    print(
                        f"   类型: {'目录' if item.ext.get('type') == 'folder' else '文件'}"
                    )
                    print(
                        f"   大小: {item.size:,} bytes"
                        if item.size > 0
                        else "   大小: -"
                    )
                    if item.ext.get("modified"):
                        print(f"   修改时间: {item.ext['modified']}")
                else:
                    print("❌ 无效的项目编号")
            except ValueError:
                print("❌ 请输入有效的数字")
        elif choice == "7" or choice == "..":
            if current_path:
                current_path = os.path.dirname(current_path)
                print(f"✅ 已返回上级目录")
            else:
                print("❌ 已在根目录")
        else:
            print("❌ 无效的选择，请重试")

    print("\n👋 感谢使用清华云盘驱动交互式演示！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="清华云盘驱动示例和测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python example.py --demo          # 快速演示
  python example.py --test          # 完整测试
  python example.py --interactive   # 交互式演示

配置方法:
  # 使用funsecret (推荐)
  funsecret set fundrive.tsinghua.share_key "your_share_key"
  
  # 使用环境变量
  export TSINGHUA_SHARE_KEY="your_share_key"
  export TSINGHUA_PASSWORD="your_password"  # 可选
        """,
    )

    parser.add_argument("--demo", action="store_true", help="运行快速演示")

    parser.add_argument("--test", action="store_true", help="运行完整测试")

    parser.add_argument("--interactive", action="store_true", help="运行交互式演示")

    args = parser.parse_args()

    if args.demo:
        run_quick_demo()
    elif args.test:
        run_full_test()
    elif args.interactive:
        run_interactive_demo()
    else:
        # 默认运行快速演示
        print("未指定运行模式，执行快速演示...")
        print("使用 --help 查看所有选项")
        run_quick_demo()


if __name__ == "__main__":
    main()
