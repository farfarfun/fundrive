#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pCloud 网盘驱动使用示例

本示例展示了如何使用 PCloudDrive 类进行各种网盘操作，包括：
- 登录认证
- 文件夹操作（创建、列表、删除）
- 文件操作（上传、下载、删除）
- 高级功能（重命名、移动、复制、分享）
- 搜索和配额查询

作者: fundrive 项目组
日期: 2024
"""

import os
from fundrive.drives.plcoud.drive import PCloudDrive


def main():
    """主函数，演示 PCloudDrive 的各种功能"""

    # 初始化 pCloud 驱动
    print("=== pCloud 网盘驱动使用示例 ===\n")

    # 创建驱动实例
    drive = PCloudDrive()

    # 1. 登录认证
    print("1. 登录认证")
    print("-" * 40)

    # 方式一：使用用户名和密码登录

    if drive.login():
        print("✓ 登录成功")
    else:
        print("✗ 登录失败，请检查用户名和密码")
        return

    # 方式二：使用 auth token 登录（如果已有 token）
    # auth_token = "your_auth_token_here"
    # if drive.login(auth_token=auth_token):
    #     print(f"✓ Token 登录成功")

    print()

    # 2. 获取网盘配额信息
    print("2. 网盘配额信息")
    print("-" * 40)
    quota = drive.get_quota()
    if quota:
        total_gb = quota["total"] / (1024**3)
        used_gb = quota["used"] / (1024**3)
        free_gb = quota["free"] / (1024**3)
        print(f"总容量: {total_gb:.2f} GB")
        print(f"已使用: {used_gb:.2f} GB")
        print(f"剩余空间: {free_gb:.2f} GB")
    print()

    # 3. 文件夹操作
    print("3. 文件夹操作")
    print("-" * 40)

    # 获取根目录文件列表
    print("根目录文件列表:")
    files = drive.get_file_list("0")  # "0" 是根目录的 ID
    for file in files[:5]:  # 只显示前5个文件
        print(f"  📄 {file.name} ({file.size} bytes)")

    # 获取根目录文件夹列表
    print("\n根目录文件夹列表:")
    dirs = drive.get_dir_list("0")
    for dir in dirs[:5]:  # 只显示前5个文件夹
        print(f"  📁 {dir.name}")

    # 创建测试文件夹
    test_folder_name = "fundrive_test_folder"
    print(f"\n创建测试文件夹: {test_folder_name}")
    test_folder_id = drive.mkdir("0", test_folder_name)
    if test_folder_id:
        print(f"✓ 文件夹创建成功，ID: {test_folder_id}")
    else:
        print("✗ 文件夹创建失败")

    print()

    # 4. 文件操作
    print("4. 文件操作")
    print("-" * 40)

    # 创建一个测试文件
    test_file_path = "/tmp/test_file.txt"
    test_content = "这是一个测试文件，用于演示 pCloud 上传功能。\nHello, pCloud!"

    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    print(f"创建本地测试文件: {test_file_path}")

    # 上传文件到测试文件夹
    if test_folder_id:
        print("上传文件到测试文件夹...")
        if drive.upload_file(test_file_path, test_folder_id):
            print("✓ 文件上传成功")
        else:
            print("✗ 文件上传失败")

        # 获取测试文件夹中的文件列表
        print("\n测试文件夹中的文件:")
        folder_files = drive.get_file_list(test_folder_id)
        for file in folder_files:
            print(f"  📄 {file.name} ({file.size} bytes)")

            # 下载文件
            download_path = f"/tmp/downloaded_{file.name}"
            print(f"下载文件到: {download_path}")
            if drive.download_file(file.fid, filepath=download_path):
                print("✓ 文件下载成功")

                # 验证下载的文件内容
                with open(download_path, "r", encoding="utf-8") as f:
                    downloaded_content = f.read()
                if downloaded_content == test_content:
                    print("✓ 文件内容验证成功")
                else:
                    print("✗ 文件内容验证失败")
            else:
                print("✗ 文件下载失败")

    print()

    # 5. 搜索功能
    print("5. 搜索功能")
    print("-" * 40)

    # 搜索文件
    search_keyword = "test"
    print(f"搜索关键词: {search_keyword}")
    search_results = drive.search(search_keyword)

    if search_results:
        print(f"找到 {len(search_results)} 个结果:")
        for result in search_results[:3]:  # 只显示前3个结果
            file_type = "📁" if result.is_dir else "📄"
            print(f"  {file_type} {result.name}")
    else:
        print("未找到匹配的文件")

    print()

    # 6. 高级功能演示
    print("6. 高级功能演示")
    print("-" * 40)

    if test_folder_id and folder_files:
        test_file = folder_files[0]

        # 重命名文件
        new_name = "renamed_test_file.txt"
        print(f"重命名文件: {test_file.name} -> {new_name}")
        if drive.rename(test_file.fid, new_name):
            print("✓ 文件重命名成功")
        else:
            print("✗ 文件重命名失败")

        # 分享文件 - 使用修复后的分享功能
        print(f"分享文件: {new_name}")

        # 先测试无密码分享
        print("  测试无密码分享...")
        share_result = drive.share(test_file.fid)
        if share_result:
            print("  ✓ 无密码分享成功")
            print(f"    分享链接: {share_result.get('link', 'N/A')}")
            print(f"    链接ID: {share_result.get('linkid', 'N/A')}")
            print(f"    代码: {share_result.get('code', 'N/A')}")
        else:
            print("  ✗ 无密码分享失败")

        # 再测试带密码分享
        print("  测试带密码分享...")
        share_result_with_pwd = drive.share(
            test_file.fid, password="test123", expire_days=7
        )
        if share_result_with_pwd:
            print("  ✓ 带密码分享成功")
            print(f"    分享链接: {share_result_with_pwd.get('link', 'N/A')}")
            print("    分享密码: test123")
            print("    有效期: 7天")
        else:
            print("  ✗ 带密码分享失败")

    print()

    # 7. 清理测试数据
    print("7. 清理测试数据")
    print("-" * 40)

    if test_folder_id:
        print("删除测试文件夹及其内容...")
        if drive.delete(test_folder_id):
            print("✓ 测试文件夹删除成功")
        else:
            print("✗ 测试文件夹删除失败")

    # 删除本地测试文件
    try:
        os.remove(test_file_path)
        if os.path.exists("/tmp/downloaded_test_file.txt"):
            os.remove("/tmp/downloaded_test_file.txt")
        print("✓ 本地测试文件清理完成")
    except Exception as e:
        print(f"✗ 本地文件清理失败: {e}")

    print("\n=== 示例演示完成 ===")


def advanced_example():
    """高级功能示例"""
    print("\n=== 高级功能示例 ===\n")

    drive = PCloudDrive()

    # 登录
    if not drive.login():
        print("✗ 登录失败，无法运行高级示例")
        return

    print("✓ 登录成功")

    # 1. 分享功能完整测试
    print("\n1. 分享功能完整测试")
    print("-" * 40)

    # 创建临时测试文件
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(
            "这是一个专门用于测试分享功能的文件\n创建时间: " + str(os.path.getmtime)
        )
        temp_file_path = f.name

    try:
        # 上传测试文件
        print(f"上传测试文件: {os.path.basename(temp_file_path)}")
        if drive.upload_file(temp_file_path, "0"):
            print("✓ 文件上传成功")

            # 找到上传的文件
            files = drive.get_file_list("0")
            test_file = None
            for file in files:
                if file.name == os.path.basename(temp_file_path):
                    test_file = file
                    break

            if test_file:
                print(f"找到测试文件: {test_file.name} (ID: {test_file.fid})")

                # 测试各种分享方式
                print("\n测试无密码分享:")
                share_result = drive.share(test_file.fid)
                if share_result:
                    print("✓ 无密码分享成功")
                    print(f"  链接: {share_result.get('link', 'N/A')}")
                else:
                    print("✗ 无密码分享失败")

                print("\n测试带密码分享:")
                share_with_pwd = drive.share(test_file.fid, password="demo123")
                if share_with_pwd:
                    print("✓ 带密码分享成功")
                    print(f"  链接: {share_with_pwd.get('link', 'N/A')}")
                    print("  密码: demo123")
                else:
                    print("✗ 带密码分享失败")

                # 清理测试文件
                print("\n清理测试文件...")
                if drive.delete(test_file.fid):
                    print("✓ 测试文件删除成功")

    finally:
        # 删除本地临时文件
        try:
            os.unlink(temp_file_path)
        except:
            pass


if __name__ == "__main__":
    # 运行基本示例
    main()

    # 如需运行高级示例，请取消注释下面这行
    # advanced_example()
