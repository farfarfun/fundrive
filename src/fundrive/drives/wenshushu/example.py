#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文叔叔网盘驱动示例和测试脚本

本脚本演示如何使用文叔叔网盘驱动进行文件操作，包括：
- 匿名登录
- 文件上传和分享
- 分享链接下载
- 存储空间查询
- 已上传文件管理

使用方法:
1. 快速演示: python example.py --demo
2. 完整测试: python example.py --test
3. 交互式演示: python example.py --interactive

配置方法:
文叔叔支持匿名使用，无需配置账号信息。

作者: FunDrive Team
"""

import argparse
import os
import tempfile


from fundrive.drives.wenshushu import WSSDrive
from fundrive.utils.file import print_files


def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 60)
    if title:
        print(f" {title} ")
        print("=" * 60)


def create_test_file(filename: str = "test_file.txt", content: str = None) -> str:
    """创建测试文件"""
    if content is None:
        content = f"""这是一个测试文件
文件名: {filename}
创建时间: {os.popen("date").read().strip()}
内容: 文叔叔网盘驱动测试文件

文叔叔是一个免费的临时文件分享服务，支持：
- 匿名上传
- 临时分享
- 快速下载
"""

    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📄 创建测试文件: {filepath}")
    return filepath


def demo_basic_operations(drive: WSSDrive):
    """演示基本操作"""
    print_separator("基本操作演示")

    # 登录
    print("🔐 正在匿名登录文叔叔...")
    if drive.login():
        print("✅ 匿名登录成功")
    else:
        print("❌ 登录失败")
        return False

    # 获取存储空间信息
    print("\n💾 获取存储空间信息...")
    storage_info = drive.get_storage_info()
    if storage_info:
        print("✅ 存储空间信息:")
        print(f"   已用空间: {storage_info['used_space_gb']} GB")
        print(f"   剩余空间: {storage_info['free_space_gb']} GB")
        print(f"   总空间: {storage_info['total_space_gb']} GB")
    else:
        print("⚠️ 无法获取存储空间信息")

    # 获取已上传文件列表
    print("\n📄 获取已上传文件列表...")
    files = drive.get_file_list()
    print_files(files, "已上传文件")

    return True


def demo_upload_operations(drive: WSSDrive):
    """演示上传操作"""
    print_separator("文件上传演示")

    # 创建测试文件
    test_file = create_test_file("wenshushu_test.txt")

    try:
        # 上传文件
        print("\n⬆️ 上传测试文件...")
        success = drive.upload_file(
            filepath=test_file,
            fid="",  # 文叔叔不支持目录结构
            filename="wenshushu_test.txt",
        )

        if success:
            print("✅ 文件上传成功")

            # 获取更新后的文件列表
            print("\n📄 获取更新后的文件列表...")
            files = drive.get_file_list()
            print_files(files, "上传后的文件列表")

            # 返回最新上传的文件信息
            if files:
                latest_file = files[-1]  # 假设最后一个是最新上传的
                return latest_file
        else:
            print("❌ 文件上传失败")

    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🗑️ 清理测试文件: {test_file}")

    return None


def demo_download_operations(drive: WSSDrive, share_url: str = None):
    """演示下载操作"""
    print_separator("文件下载演示")

    if not share_url:
        print("⚠️ 没有可用的分享链接，跳过下载演示")
        print("请先上传文件获取分享链接，或手动提供分享链接")
        return

    print(f"📥 准备下载文件: {share_url}")

    # 创建下载目录
    download_dir = "./test_downloads"
    os.makedirs(download_dir, exist_ok=True)

    # 下载文件
    print(f"\n⬇️ 下载文件到: {download_dir}")
    success = drive.download_file(fid=share_url, filedir=download_dir)

    if success:
        print("✅ 文件下载成功")

        # 列出下载的文件
        if os.path.exists(download_dir):
            files = os.listdir(download_dir)
            if files:
                print("📁 下载的文件:")
                for file in files:
                    filepath = os.path.join(download_dir, file)
                    size = os.path.getsize(filepath)
                    print(f"   📄 {file} ({size:,} bytes)")
            else:
                print("⚠️ 下载目录为空")
    else:
        print("❌ 文件下载失败")


def demo_file_info_operations(drive: WSSDrive):
    """演示文件信息操作"""
    print_separator("文件信息查询演示")

    # 获取已上传文件列表
    files = drive.get_file_list()

    if not files:
        print("⚠️ 没有已上传的文件，跳过文件信息演示")
        return

    # 选择第一个文件进行信息查询
    test_file = files[0]
    print(f"📄 选择测试文件: {test_file.name}")

    # 获取文件详细信息
    print("\n📋 获取文件详细信息...")
    file_info = drive.get_file_info(test_file.fid)

    if file_info:
        print("✅ 文件信息:")
        print(f"   文件名: {file_info.name}")
        print(f"   文件ID: {file_info.fid}")
        print(f"   大小: {file_info.size:,} bytes")
        print(f"   类型: {file_info.ext.get('type', '未知')}")
        if file_info.ext.get("upload_time"):
            print(f"   上传时间: {file_info.ext['upload_time']}")
        if file_info.ext.get("share_url"):
            print(f"   分享链接: {file_info.ext['share_url']}")
        if file_info.ext.get("mgr_url"):
            print(f"   管理链接: {file_info.ext['mgr_url']}")
    else:
        print("❌ 无法获取文件信息")

    # 检查文件是否存在
    print("\n🔍 检查文件是否存在...")
    exists = drive.exist(test_file.fid)
    print(f"✅ 文件存在: {exists}")


def demo_search_operations(drive: WSSDrive):
    """演示搜索操作"""
    print_separator("搜索功能演示")

    # 搜索文件
    search_keywords = ["test", "txt", "wenshushu"]

    for keyword in search_keywords:
        print(f"\n🔍 搜索包含 '{keyword}' 的文件...")
        results = drive.search(keyword)

        if results:
            print(f"✅ 找到 {len(results)} 个结果:")
            for i, file in enumerate(results, 1):
                print(f"  {i}. 📄 {file.name}")
                print(f"     ID: {file.fid}")
                if file.ext.get("share_url"):
                    print(f"     分享: {file.ext['share_url']}")
        else:
            print(f"❌ 未找到包含 '{keyword}' 的文件")

        # 只测试第一个关键词，避免过多搜索
        break


def demo_limitations(drive: WSSDrive):
    """演示功能限制"""
    print_separator("功能限制演示")

    print("📝 测试文叔叔的功能限制...")

    # 测试创建目录（应该失败）
    print("\n🚫 尝试创建目录（应该失败）...")
    success = drive.mkdir("", "test_folder")
    print(f"   结果: {'成功' if success else '失败（符合预期）'}")

    # 测试删除操作（应该失败）
    print("\n🚫 尝试删除文件（应该失败）...")
    success = drive.delete("nonexistent")
    print(f"   结果: {'成功' if success else '失败（符合预期）'}")

    # 测试获取目录列表（应该为空）
    print("\n📁 尝试获取目录列表（应该为空）...")
    dirs = drive.get_dir_list("")
    print(f"   结果: 找到 {len(dirs)} 个目录（符合预期）")

    # 测试获取目录信息（应该为None）
    print("\n📋 尝试获取目录信息（应该为None）...")
    dir_info = drive.get_dir_info("")
    print(f"   结果: {'有信息' if dir_info else '无信息（符合预期）'}")


def run_quick_demo():
    """运行快速演示"""
    print("🚀 文叔叔网盘驱动快速演示")
    print("=" * 50)

    # 创建驱动实例
    drive = WSSDrive()

    # 运行演示
    if demo_basic_operations(drive):
        demo_limitations(drive)

    print_separator("演示完成")
    print("✅ 文叔叔网盘驱动快速演示完成！")


def run_full_test():
    """运行完整测试"""
    print("🧪 文叔叔网盘驱动完整测试")
    print("=" * 50)

    # 创建驱动实例
    drive = WSSDrive()

    # 运行所有测试
    if demo_basic_operations(drive):
        uploaded_file = demo_upload_operations(drive)

        # 如果上传成功，尝试下载
        share_url = None
        if uploaded_file and uploaded_file.ext.get("share_url"):
            share_url = uploaded_file.ext["share_url"]

        demo_download_operations(drive, share_url)
        demo_file_info_operations(drive)
        demo_search_operations(drive)
        demo_limitations(drive)

    print_separator("测试完成")
    print("✅ 文叔叔网盘驱动完整测试完成！")


def run_interactive_demo():
    """运行交互式演示"""
    print("🎮 文叔叔网盘驱动交互式演示")
    print("=" * 50)

    # 创建驱动实例
    drive = WSSDrive()

    # 登录
    if not drive.login():
        print("❌ 登录失败")
        return

    while True:
        print("\n📋 可用操作:")
        print("1. 查看存储空间信息")
        print("2. 查看已上传文件列表")
        print("3. 上传文件")
        print("4. 下载文件（需要分享链接）")
        print("5. 搜索文件")
        print("6. 获取文件信息")
        print("7. 创建测试文件并上传")
        print("0. 退出")

        choice = input("\n请选择操作 (0-7): ").strip()

        if choice == "0" or choice.lower() == "quit":
            break
        elif choice == "1":
            storage_info = drive.get_storage_info()
            if storage_info:
                print("\n💾 存储空间信息:")
                print(f"   已用: {storage_info['used_space_gb']} GB")
                print(f"   剩余: {storage_info['free_space_gb']} GB")
                print(f"   总计: {storage_info['total_space_gb']} GB")
            else:
                print("❌ 无法获取存储空间信息")
        elif choice == "2":
            files = drive.get_file_list()
            print_files(files, "已上传文件")
        elif choice == "3":
            filepath = input("请输入要上传的文件路径: ").strip()
            if filepath and os.path.exists(filepath):
                filename = input(
                    f"请输入文件名 (默认: {os.path.basename(filepath)}): "
                ).strip()
                filename = filename or os.path.basename(filepath)

                success = drive.upload_file(
                    filepath=filepath, fid="", filename=filename
                )

                if success:
                    print("✅ 文件上传成功")
                    # 显示更新后的文件列表
                    files = drive.get_file_list()
                    if files:
                        latest_file = files[-1]
                        print(f"📄 最新上传: {latest_file.name}")
                        if latest_file.ext.get("share_url"):
                            print(f"🔗 分享链接: {latest_file.ext['share_url']}")
                else:
                    print("❌ 文件上传失败")
            else:
                print("❌ 文件不存在")
        elif choice == "4":
            share_url = input("请输入分享链接: ").strip()
            if share_url:
                download_dir = (
                    input("请输入下载目录 (默认: ./downloads): ").strip()
                    or "./downloads"
                )

                success = drive.download_file(fid=share_url, filedir=download_dir)

                if success:
                    print(f"✅ 文件下载成功到: {download_dir}")
                else:
                    print("❌ 文件下载失败")
            else:
                print("❌ 请输入有效的分享链接")
        elif choice == "5":
            keyword = input("请输入搜索关键词: ").strip()
            if keyword:
                results = drive.search(keyword)
                print_files(results, f"搜索 '{keyword}' 的结果")
        elif choice == "6":
            files = drive.get_file_list()
            if not files:
                print("❌ 没有已上传的文件")
                continue

            print("\n📄 已上传文件:")
            for i, file in enumerate(files, 1):
                print(f"  {i}. {file.name}")

            try:
                file_choice = int(input("请选择文件编号: ")) - 1
                if 0 <= file_choice < len(files):
                    file = files[file_choice]
                    file_info = drive.get_file_info(file.fid)

                    if file_info:
                        print("\n📋 文件信息:")
                        print(f"   名称: {file_info.name}")
                        print(f"   ID: {file_info.fid}")
                        print(f"   大小: {file_info.size:,} bytes")
                        if file_info.ext.get("upload_time"):
                            print(f"   上传时间: {file_info.ext['upload_time']}")
                        if file_info.ext.get("share_url"):
                            print(f"   分享链接: {file_info.ext['share_url']}")
                    else:
                        print("❌ 无法获取文件信息")
                else:
                    print("❌ 无效的文件编号")
            except ValueError:
                print("❌ 请输入有效的数字")
        elif choice == "7":
            # 创建并上传测试文件
            content = input("请输入测试文件内容 (按回车使用默认内容): ").strip()
            test_file = create_test_file("interactive_test.txt", content or None)

            try:
                success = drive.upload_file(
                    filepath=test_file, fid="", filename="interactive_test.txt"
                )

                if success:
                    print("✅ 测试文件上传成功")
                    files = drive.get_file_list()
                    if files:
                        latest_file = files[-1]
                        if latest_file.ext.get("share_url"):
                            print(f"🔗 分享链接: {latest_file.ext['share_url']}")
                else:
                    print("❌ 测试文件上传失败")
            finally:
                if os.path.exists(test_file):
                    os.remove(test_file)
        else:
            print("❌ 无效的选择，请重试")

    print("\n👋 感谢使用文叔叔网盘驱动交互式演示！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="文叔叔网盘驱动示例和测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python example.py --demo          # 快速演示
  python example.py --test          # 完整测试
  python example.py --interactive   # 交互式演示

特点说明:
  - 文叔叔是免费的临时文件分享服务
  - 支持匿名使用，无需注册
  - 文件有过期时间限制
  - 不支持目录结构
  - 适合临时文件分享
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
