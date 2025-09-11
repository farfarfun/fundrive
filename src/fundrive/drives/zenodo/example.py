#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zenodo 网盘驱动完整使用示例

本示例包含了 Zenodo 驱动的所有功能演示：
- 基础功能测试
- 完整功能演示（文件上传下载、存储库管理等）
- 简单使用示例

使用方法：
1. 基础测试: python example.py --test
2. 完整演示: python example.py --demo
3. 简单示例: python example.py --simple
4. 默认运行: python example.py (运行简单示例)

配置方法：
- 在 funsecret 中设置: fundrive.zenodo.access_token
- 或者直接在代码中传入 access_token 参数

API 文档: https://developers.zenodo.org/#rest-api
"""

import os
import sys
import tempfile
from pathlib import Path

from .drive import ZenodoDrive
from funutil import getLogger

logger = getLogger("zenodo_example")


def create_test_files():
    """创建测试文件"""
    test_dir = tempfile.mkdtemp(prefix="zenodo_test_")

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
    print("🚀 开始测试 Zenodo 驱动基础功能")
    print("=" * 50)

    # 1. 初始化驱动（使用沙盒环境）
    print("\n1️⃣ 初始化驱动")
    drive = ZenodoDrive(sandbox=True)
    print("✅ 驱动初始化完成（沙盒模式）")

    # 2. 测试登录
    print("\n2️⃣ 测试登录")
    try:
        success = drive.login()
        if success:
            print("✅ 登录成功")
        else:
            print("❌ 登录失败 - 请检查访问令牌配置")
            return False
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return False

    # 3. 测试获取存储库列表
    print("\n3️⃣ 测试获取存储库列表")
    try:
        depositions = drive.get_dir_list("root")
        print(f"✅ 成功获取 {len(depositions)} 个存储库")

        # 显示前几个存储库
        for i, dep in enumerate(depositions[:3]):
            print(f"   📁 {dep.name} (ID: {dep.fid})")

    except Exception as e:
        print(f"❌ 获取存储库列表失败: {e}")
        return False

    # 4. 测试创建存储库
    print("\n4️⃣ 测试创建存储库")
    try:
        deposition_id = drive.mkdir("root", "fundrive 测试存储库")
        print(f"✅ 存储库创建成功，ID: {deposition_id}")
    except Exception as e:
        print(f"❌ 创建存储库失败: {e}")
        return False

    # 5. 测试搜索功能
    print("\n5️⃣ 测试搜索功能")
    try:
        results = drive.search("python", limit=5)
        print(f"✅ 搜索 'python' 找到 {len(results)} 条记录")

        for i, result in enumerate(results[:3]):
            print(f"   🔍 {result.name}")

    except Exception as e:
        print(f"❌ 搜索功能测试失败: {e}")

    # 6. 测试存储库信息获取
    print("\n6️⃣ 测试获取存储库信息")
    try:
        info = drive.get_file_info(deposition_id)
        if info:
            print(f"✅ 存储库信息: {info.name}")
            print(f"   📅 创建时间: {info.create_time}")
        else:
            print("❌ 获取存储库信息失败")
    except Exception as e:
        print(f"❌ 获取存储库信息异常: {e}")

    # 7. 测试删除存储库（清理）
    print("\n7️⃣ 清理测试存储库")
    try:
        success = drive.delete(deposition_id)
        if success:
            print("✅ 测试存储库删除成功")
        else:
            print("❌ 删除测试存储库失败")
    except Exception as e:
        print(f"❌ 删除存储库异常: {e}")

    print("\n" + "=" * 50)
    print("🎉 基础功能测试完成！")

    return True


def demo_full_functionality():
    """完整功能演示"""
    print("🚀 Zenodo 驱动完整功能演示")
    print("=" * 60)

    # 1. 初始化驱动（使用沙盒环境进行测试）
    print("\n1. 初始化 Zenodo 驱动")
    print("=" * 60)

    drive = ZenodoDrive(sandbox=True)

    # 2. 登录认证
    print("\n2. 登录认证")
    print("-" * 30)

    success = drive.login()
    if not success:
        print("❌ 登录失败，请检查访问令牌配置")
        print("提示：请在 funsecret 中配置 fundrive.zenodo.access_token")
        return

    print("✅ 登录成功")

    # 3. 获取存储库列表
    print("\n3. 获取存储库列表")
    print("-" * 30)

    depositions = drive.get_dir_list("root")
    print(f"📁 找到 {len(depositions)} 个存储库")

    for dep in depositions[:3]:  # 只显示前3个
        print(f"  - {dep.name} (ID: {dep.fid})")

    # 4. 创建新的存储库
    print("\n4. 创建新的存储库")
    print("-" * 30)

    try:
        deposition_id = drive.mkdir("root", "fundrive 测试存储库")
        print(f"✅ 存储库创建成功，ID: {deposition_id}")
    except Exception as e:
        print(f"❌ 创建存储库失败: {e}")
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
    success = drive.upload_file(test_file, deposition_id)
    if success:
        print("✅ 文件上传成功")
    else:
        print("❌ 文件上传失败")

    # 7. 上传整个目录
    print("\n7. 上传整个目录")
    print("-" * 30)

    success = drive.upload_dir(test_dir, deposition_id, recursion=True)
    if success:
        print("✅ 目录上传成功")
    else:
        print("❌ 目录上传失败")

    # 8. 获取存储库文件列表
    print("\n8. 获取存储库文件列表")
    print("-" * 30)

    files = drive.get_file_list(deposition_id)
    print(f"📄 存储库中有 {len(files)} 个文件:")

    for file_obj in files:
        size_str = f"({file_obj.size} bytes)" if file_obj.size else ""
        print(f"  - {file_obj.name} {size_str}")

    # 9. 更新存储库元数据并发布
    print("\n9. 发布存储库")
    print("-" * 30)

    success = drive.publish_deposition(
        deposition_id,
        title="fundrive Zenodo 驱动测试",
        description="这是使用 fundrive Zenodo 驱动创建的测试存储库，包含多个测试文件。",
    )

    if success:
        print("✅ 存储库发布成功")
        print(f"🔗 DOI: 10.5281/zenodo.{deposition_id}")
    else:
        print("❌ 存储库发布失败")

    # 10. 搜索记录
    print("\n10. 搜索记录")
    print("-" * 30)

    search_results = drive.search("fundrive")
    print(f"🔍 搜索 'fundrive' 找到 {len(search_results)} 条记录")

    for result in search_results[:3]:  # 只显示前3个结果
        print(f"  - {result.name}")

    # 11. 下载文件（如果存储库已发布）
    if success:  # 如果发布成功
        print("\n11. 下载文件")
        print("-" * 30)

        download_dir = tempfile.mkdtemp(prefix="zenodo_download_")
        print(f"📁 下载目录: {download_dir}")

        # 下载整个存储库
        download_success = drive.download_dir(deposition_id, download_dir)
        if download_success:
            print("✅ 文件下载成功")

            # 列出下载的文件
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, download_dir)
                    print(f"  📄 {rel_path}")
        else:
            print("❌ 文件下载失败")

    # 12. 清理测试文件
    print("\n12. 清理测试文件")
    print("-" * 30)

    try:
        import shutil

        shutil.rmtree(test_dir)
        if "download_dir" in locals():
            shutil.rmtree(download_dir)
        print("✅ 测试文件清理完成")
    except Exception as e:
        print(f"⚠️  清理测试文件时出错: {e}")

    print("\n" + "=" * 60)
    print("🎉 Zenodo 驱动功能演示完成！")
    print("=" * 60)

    print("\n📋 功能总结:")
    print("✅ 登录认证")
    print("✅ 存储库管理（创建、列表、元数据更新）")
    print("✅ 文件上传（单文件、目录递归）")
    print("✅ 文件下载（单文件、目录递归）")
    print("✅ 记录搜索")
    print("✅ 存储库发布")
    print("✅ 完整的错误处理和中文日志")


def simple_example():
    """简单使用示例"""
    print("🧪 Zenodo 驱动简单使用示例")
    print("=" * 40)

    # 初始化驱动（使用沙盒环境进行测试）
    drive = ZenodoDrive(sandbox=True)

    # 登录认证
    success = drive.login()
    if not success:
        print("❌ 登录失败，请检查访问令牌配置")
        print("💡 提示：请在 funsecret 中配置 fundrive.zenodo.access_token")
        return

    print("✅ 登录成功")

    # 获取存储库列表
    depositions = drive.get_dir_list("root")
    print(f"📁 找到 {len(depositions)} 个存储库")

    # 如果有存储库，获取第一个的文件列表
    if depositions:
        first_deposition = depositions[0]
        print(f"\n📋 存储库 '{first_deposition.name}' 的文件列表:")

        files = drive.get_file_list(first_deposition.fid)
        for file_obj in files:
            print(f"  📄 {file_obj.name}")

    # 创建新的存储库
    print("\n🆕 创建新存储库")
    try:
        deposition_id = drive.mkdir("root", "测试存储库")
        print(f"✅ 存储库创建成功，ID: {deposition_id}")

        # 清理测试存储库
        drive.delete(deposition_id)
        print("🗑️ 测试存储库已清理")

    except Exception as e:
        print(f"❌ 操作失败: {e}")

    print("\n🎉 简单示例运行完成！")


def main():
    """主函数"""
    print("🌟 Zenodo 网盘驱动示例程序")
    print("📖 请确保已配置 Zenodo 访问令牌")
    print("🌐 使用沙盒环境进行测试")

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
    print("- 访问令牌配置: funsecret 中设置 fundrive.zenodo.access_token")
    print("- 本示例使用 Zenodo 沙盒环境，不会影响正式数据")


if __name__ == "__main__":
    main()
