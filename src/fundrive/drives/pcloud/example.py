#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pCloud 网盘驱动完整使用示例

本示例包含了 pCloud 驱动的所有功能演示：
- 基础功能测试
- 完整功能演示（文件上传下载、目录管理等）
- 简单使用示例

使用方法：
1. 基础测试: python example.py --test
2. 完整演示: python example.py --demo
3. 简单示例: python example.py --simple
4. 默认运行: python example.py (运行简单示例)

配置方法：
- 在 funsecret 中设置: fundrive.pcloud.username 和 fundrive.pcloud.password
- 或者直接在代码中传入用户名和密码

API 文档: https://docs.pcloud.com/
"""

import os
import sys
import tempfile


from fundrive.drives.pcloud import PCloudDrive
from funutil import getLogger

logger = getLogger("pcloud_example")


def create_test_files():
    """创建测试文件"""
    test_dir = tempfile.mkdtemp(prefix="pcloud_test_")

    # 创建测试文件
    test_file1 = os.path.join(test_dir, "test1.txt")
    with open(test_file1, "w", encoding="utf-8") as f:
        f.write("这是第一个测试文件\n包含中文内容")

    test_file2 = os.path.join(test_dir, "test2.md")
    with open(test_file2, "w", encoding="utf-8") as f:
        f.write("# 测试文档\n\n这是一个 Markdown 测试文件。")

    # 创建子目录和文件
    sub_dir = os.path.join(test_dir, "subdir")
    os.makedirs(sub_dir)

    test_file3 = os.path.join(sub_dir, "test3.json")
    with open(test_file3, "w", encoding="utf-8") as f:
        f.write('{"name": "测试", "type": "JSON文件"}')

    return test_dir


def test_basic_functionality():
    """基础功能测试"""
    print("🚀 开始测试 pCloud 驱动基础功能")
    print("=" * 50)

    # 1. 初始化驱动
    print("\n1️⃣ 初始化驱动")
    drive = PCloudDrive()
    print("✅ 驱动初始化完成")

    # 2. 测试登录
    print("\n2️⃣ 测试登录")
    try:
        success = drive.login()
        if success:
            print("✅ 登录成功")
        else:
            print("❌ 登录失败 - 请检查用户名和密码配置")
            return False
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return False

    # 3. 测试获取根目录列表
    print("\n3️⃣ 测试获取根目录列表")
    try:
        files = drive.get_file_list("0")  # pCloud 根目录 ID 为 0
        dirs = drive.get_dir_list("0")
        print(f"✅ 根目录包含 {len(files)} 个文件，{len(dirs)} 个子目录")

        # 显示前几个文件和目录
        for i, file_obj in enumerate(files[:3]):
            print(f"   📄 {file_obj.name}")
        for i, dir_obj in enumerate(dirs[:3]):
            print(f"   📁 {dir_obj.name}")

    except Exception as e:
        print(f"❌ 获取目录列表失败: {e}")
        return False

    # 4. 测试创建目录
    print("\n4️⃣ 测试创建目录")
    try:
        test_dir_id = drive.mkdir("0", "fundrive_测试目录")
        print(f"✅ 测试目录创建成功，ID: {test_dir_id}")
    except Exception as e:
        print(f"❌ 创建目录失败: {e}")
        return False

    # 5. 测试搜索功能
    print("\n5️⃣ 测试搜索功能")
    try:
        results = drive.search("fundrive", limit=5)
        print(f"✅ 搜索 'fundrive' 找到 {len(results)} 条记录")

        for i, result in enumerate(results[:3]):
            print(f"   🔍 {result.name}")

    except Exception as e:
        print(f"❌ 搜索功能测试失败: {e}")

    # 6. 测试获取配额信息
    print("\n6️⃣ 测试获取配额信息")
    try:
        quota = drive.get_quota()
        if quota:
            total_gb = quota.get("total", 0) / (1024**3)
            used_gb = quota.get("used", 0) / (1024**3)
            free_gb = quota.get("free", 0) / (1024**3)
            print(
                f"✅ 配额信息: 总容量 {total_gb:.2f}GB, 已用 {used_gb:.2f}GB, 剩余 {free_gb:.2f}GB"
            )
        else:
            print("❌ 获取配额信息失败")
    except Exception as e:
        print(f"❌ 获取配额信息异常: {e}")

    # 7. 测试删除目录（清理）
    print("\n7️⃣ 清理测试目录")
    try:
        success = drive.delete(test_dir_id)
        if success:
            print("✅ 测试目录删除成功")
        else:
            print("❌ 删除测试目录失败")
    except Exception as e:
        print(f"❌ 删除目录异常: {e}")

    print("\n" + "=" * 50)
    print("🎉 基础功能测试完成！")

    return True


def demo_full_functionality():
    """完整功能演示"""
    print("🚀 pCloud 驱动完整功能演示")
    print("=" * 60)

    # 1. 初始化驱动
    print("\n1. 初始化 pCloud 驱动")
    print("=" * 60)

    drive = PCloudDrive()

    # 2. 登录认证
    print("\n2. 登录认证")
    print("-" * 30)

    success = drive.login()
    if not success:
        print("❌ 登录失败，请检查用户名和密码配置")
        print(
            "提示：请在 funsecret 中配置 fundrive.pcloud.username 和 fundrive.pcloud.password"
        )
        return

    print("✅ 登录成功")

    # 3. 获取根目录列表
    print("\n3. 获取根目录列表")
    print("-" * 30)

    files = drive.get_file_list("0")
    dirs = drive.get_dir_list("0")
    print(f"📁 根目录包含 {len(files)} 个文件，{len(dirs)} 个子目录")

    for file_obj in files[:3]:  # 只显示前3个
        print(f"  📄 {file_obj.name} ({file_obj.size} bytes)")
    for dir_obj in dirs[:3]:  # 只显示前3个
        print(f"  📁 {dir_obj.name}")

    # 4. 创建新的测试目录
    print("\n4. 创建新的测试目录")
    print("-" * 30)

    try:
        test_dir_id = drive.mkdir("0", "fundrive_完整测试目录")
        print(f"✅ 测试目录创建成功，ID: {test_dir_id}")
    except Exception as e:
        print(f"❌ 创建测试目录失败: {e}")
        return

    # 5. 创建测试文件
    print("\n5. 准备测试文件")
    print("-" * 30)

    test_dir = create_test_files()
    print(f"📁 测试文件目录: {test_dir}")

    # 列出测试文件
    for root, dirs, files in os.walk(test_dir):
        level = root.replace(test_dir, "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            print(f"{subindent}📄 {file}")

    # 6. 上传单个文件
    print("\n6. 上传单个文件")
    print("-" * 30)

    test_file = os.path.join(test_dir, "test1.txt")
    success = drive.upload_file(test_file, test_dir_id)
    if success:
        print("✅ 文件上传成功")
    else:
        print("❌ 文件上传失败")

    # 7. 上传整个目录
    print("\n7. 上传整个目录")
    print("-" * 30)

    success = drive.upload_dir(test_dir, test_dir_id, recursion=True)
    if success:
        print("✅ 目录上传成功")
    else:
        print("❌ 目录上传失败")

    # 8. 获取测试目录文件列表
    print("\n8. 获取测试目录文件列表")
    print("-" * 30)

    files = drive.get_file_list(test_dir_id)
    print(f"📄 测试目录中有 {len(files)} 个文件:")

    for file_obj in files:
        size_str = f"({file_obj.size} bytes)" if file_obj.size else ""
        print(f"  - {file_obj.name} {size_str}")

    # 9. 下载文件
    print("\n9. 下载文件")
    print("-" * 30)

    if files:
        download_dir = tempfile.mkdtemp(prefix="pcloud_download_")
        print(f"📁 下载目录: {download_dir}")

        # 下载第一个文件
        first_file = files[0]
        download_success = drive.download_file(first_file.fid, download_dir)
        if download_success:
            print(f"✅ 文件 '{first_file.name}' 下载成功")
        else:
            print(f"❌ 文件 '{first_file.name}' 下载失败")

    # 10. 测试重命名功能
    print("\n10. 测试重命名功能")
    print("-" * 30)

    if files:
        first_file = files[0]
        new_name = f"重命名_{first_file.name}"
        success = drive.rename(first_file.fid, new_name)
        if success:
            print(f"✅ 文件重命名成功: {first_file.name} -> {new_name}")
        else:
            print("❌ 文件重命名失败")

    # 11. 测试分享功能
    print("\n11. 测试分享功能")
    print("-" * 30)

    if files:
        first_file = files[0]
        share_result = drive.share(first_file.fid)
        if share_result:
            print("✅ 文件分享成功")
            print(f"   🔗 分享链接: {share_result.get('link', '')}")
        else:
            print("❌ 文件分享失败")

    # 12. 清理测试文件
    print("\n12. 清理测试文件")
    print("-" * 30)

    try:
        import shutil

        shutil.rmtree(test_dir)
        if "download_dir" in locals():
            shutil.rmtree(download_dir)
        print("✅ 本地测试文件清理完成")
    except Exception as e:
        print(f"⚠️  清理本地测试文件时出错: {e}")

    # 清理云端测试目录
    try:
        success = drive.delete(test_dir_id)
        if success:
            print("✅ 云端测试目录清理完成")
        else:
            print("❌ 云端测试目录清理失败")
    except Exception as e:
        print(f"⚠️  清理云端测试目录时出错: {e}")

    print("\n" + "=" * 60)
    print("🎉 pCloud 驱动功能演示完成！")
    print("=" * 60)

    print("\n📋 功能总结:")
    print("✅ 登录认证")
    print("✅ 目录管理（创建、列表、删除）")
    print("✅ 文件上传（单文件、目录递归）")
    print("✅ 文件下载")
    print("✅ 文件重命名")
    print("✅ 文件分享")
    print("✅ 搜索功能")
    print("✅ 配额查询")
    print("✅ 完整的错误处理和中文日志")


def simple_example():
    """简单使用示例"""
    print("🧪 pCloud 驱动简单使用示例")
    print("=" * 40)

    # 初始化驱动
    drive = PCloudDrive()

    # 登录认证
    success = drive.login()
    if not success:
        print("❌ 登录失败，请检查用户名和密码配置")
        print(
            "💡 提示：请在 funsecret 中配置 fundrive.pcloud.username 和 fundrive.pcloud.password"
        )
        return

    print("✅ 登录成功")

    # 获取根目录列表
    files = drive.get_file_list("0")
    dirs = drive.get_dir_list("0")
    print(f"📁 根目录包含 {len(files)} 个文件，{len(dirs)} 个子目录")

    # 显示前几个文件和目录
    if files:
        print("\n📄 文件列表:")
        for file_obj in files[:5]:
            size_mb = file_obj.size / (1024 * 1024) if file_obj.size else 0
            print(f"  - {file_obj.name} ({size_mb:.2f} MB)")

    if dirs:
        print("\n📁 目录列表:")
        for dir_obj in dirs[:5]:
            print(f"  - {dir_obj.name}")

    # 获取配额信息
    quota = drive.get_quota()
    if quota:
        total_gb = quota.get("total", 0) / (1024**3)
        used_gb = quota.get("used", 0) / (1024**3)
        free_gb = quota.get("free", 0) / (1024**3)
        print(
            f"\n💾 配额信息: 总容量 {total_gb:.2f}GB, 已用 {used_gb:.2f}GB, 剩余 {free_gb:.2f}GB"
        )

    # 创建测试目录
    print("\n🆕 创建测试目录")
    try:
        test_dir_id = drive.mkdir("0", "简单测试目录")
        print(f"✅ 测试目录创建成功，ID: {test_dir_id}")

        # 清理测试目录
        drive.delete(test_dir_id)
        print("🗑️ 测试目录已清理")

    except Exception as e:
        print(f"❌ 操作失败: {e}")

    print("\n🎉 简单示例运行完成！")


def main():
    """主函数"""
    print("🌟 pCloud 网盘驱动示例程序")
    print("📖 请确保已配置 pCloud 用户名和密码")

    # 解析命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--test":
            test_basic_functionality()
        elif mode == "--demo":
            demo_full_functionality()
        elif mode == "--simple":
            simple_example()
        else:
            print(f"❌ 未知参数: {mode}")
            print("💡 可用参数: --test, --demo, --simple")
    else:
        # 默认运行简单示例
        simple_example()

    print("\n📝 使用说明:")
    print("- python example.py --test    # 基础功能测试")
    print("- python example.py --demo    # 完整功能演示")
    print("- python example.py --simple  # 简单使用示例")
    print("- python example.py           # 默认运行简单示例")
    print("\n🔧 配置说明:")
    print("- 用户名配置: funsecret 中设置 fundrive.pcloud.username")
    print("- 密码配置: funsecret 中设置 fundrive.pcloud.password")
    print("- API 文档: https://docs.pcloud.com/")


if __name__ == "__main__":
    main()
