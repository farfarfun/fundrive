#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dropbox 网盘驱动示例

本示例展示了如何使用 DropboxDrive 类进行各种网盘操作。
支持多种运行模式：
- --test: 基础功能测试
- --demo: 完整功能演示
- --simple: 简单使用示例

使用前请确保已配置 Dropbox API 访问令牌。

作者: fundrive 开发团队
文档: https://github.com/farfarfun/fundrive
"""

import argparse
import os
import tempfile

from nltlog import getLogger

from fundrive.drives.dropbox.drive import DropboxDrive

logger = getLogger("fundrive")


def comprehensive_test():
    """综合测试所有功能，按优先级顺序测试核心接口"""
    logger.info("=" * 80)
    logger.info("🧪 Dropbox 驱动综合功能测试")
    logger.info("=" * 80)

    # 初始化驱动
    drive = DropboxDrive()
    test_results = {"passed": 0, "failed": 0, "total": 0}

    def test_step(step_name, test_func):
        """执行单个测试步骤"""
        test_results["total"] += 1
        logger.info(f"📋 {test_results['total']}. {step_name}")
        try:
            if test_func():
                logger.info(f"✅ {step_name} - 通过")
                test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ {step_name} - 失败")
                test_results["failed"] += 1
                return False
        except Exception as error:
            logger.error(f"💥 {step_name} - 异常: {error}")
            test_results["failed"] += 1
            return False

    # 1. 登录测试（最重要）
    def test_login():
        return drive.login()

    if not test_step("登录认证", test_login):
        logger.error("❌ 登录失败，无法继续测试")
        return False

    # 2. 文件存在性检查
    def test_exist():
        return drive.exist("/")  # 根目录必须存在

    test_step("文件存在性检查", test_exist)

    # 3. 获取配额信息
    def test_quota():
        quota = drive.get_quota()
        return quota and "used_space" in quota and "total_space" in quota

    test_step("获取配额信息", test_quota)

    # 4. 获取根目录文件列表
    def test_file_list():
        files = drive.get_file_list("/")
        return isinstance(files, list)

    test_step("获取文件列表", test_file_list)

    # 5. 获取根目录子目录列表
    def test_dir_list():
        dirs = drive.get_dir_list("/")
        return isinstance(dirs, list)

    test_step("获取目录列表", test_dir_list)

    test_dir_name = "fundrive_test"
    test_dir = f"/{test_dir_name}"

    # 6. 创建目录
    def test_mkdir():
        result = drive.mkdir("/", test_dir_name)
        return bool(result)

    test_step("创建目录", test_mkdir)

    # 7. 验证目录存在
    def test_dir_exist():
        return drive.exist(test_dir)

    test_step("验证目录存在", test_dir_exist)

    # 8. 获取目录信息
    def test_dir_info():
        info = drive.get_dir_info(test_dir)
        return info is not None and not info.isfile

    test_step("获取目录信息", test_dir_info)

    # 创建临时测试文件
    test_file_content = "这是一个 Dropbox 驱动测试文件\\n测试时间: " + str(
        os.path.getctime(__file__)
    )
    temp_file = None

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(test_file_content)
            temp_file = f.name
    except Exception as e:
        logger.error(f"❌ 创建临时文件失败: {e}")
        temp_file = None

    if temp_file:
        test_file_name = "test_file.txt"
        test_file_path = f"{test_dir}/{test_file_name}"

        # 9. 上传文件
        def test_upload():
            return drive.upload_file(temp_file, test_dir)

        test_step("上传文件", test_upload)

        # 10. 验证文件存在
        def test_file_exist():
            return drive.exist(test_file_path)

        test_step("验证文件存在", test_file_exist)

        # 11. 获取文件信息
        def test_file_info():
            info = drive.get_file_info(test_file_path)
            return info is not None and info.isfile

        test_step("获取文件信息", test_file_info)

        # 12. 下载文件
        download_file = None
        try:
            download_dir = tempfile.mkdtemp()
            download_file = os.path.join(download_dir, "downloaded_test.txt")
        except Exception:
            download_file = None

        def test_download():
            if download_file:
                return drive.download_file(test_file_path, filepath=download_file)
            return False

        test_step("下载文件", test_download)

        # 13. 文件重命名
        new_file_name = "renamed_test.txt"
        new_file_path = f"{test_dir}/{new_file_name}"

        def test_rename():
            return drive.rename(test_file_path, new_file_name)

        test_step("文件重命名", test_rename)

        # 14. 文件复制
        def test_copy():
            return drive.copy(new_file_path, test_dir)

        test_step("文件复制", test_copy)

        # 15. 搜索功能
        def test_search():
            results = drive.search("test", fid=test_dir)
            return isinstance(results, list)

        test_step("搜索功能", test_search)

        # 16. 分享功能
        def test_share():
            result = drive.share(new_file_path, expire_days=7)
            return result is not None and "links" in result

        test_step("分享功能", test_share)

        # 17. 回收站功能（应该返回警告）
        def test_recycle():
            recycle_files = drive.get_recycle_list()
            return isinstance(recycle_files, list) and len(recycle_files) == 0

        test_step("回收站功能（警告测试）", test_recycle)

        # 18. 保存分享功能（应该返回False）
        def test_save_shared():
            result = drive.save_shared("https://example.com/share", test_dir)
            return not result  # 应该返回False表示不支持

        test_step("保存分享功能（警告测试）", test_save_shared)

        # 19. 删除测试文件
        def test_delete_files():
            success_count = 0
            files_to_delete = drive.get_file_list(test_dir)
            for file in files_to_delete:
                if drive.delete(file.fid):
                    success_count += 1
            return success_count > 0

        test_step("删除测试文件", test_delete_files)

        # 清理本地临时文件
        try:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            if download_file and os.path.exists(download_file):
                os.unlink(download_file)
                os.rmdir(os.path.dirname(download_file))
        except Exception as e:
            logger.error(f"error:{e}")

    # 20. 删除测试目录
    def test_delete_dir():
        return drive.delete(test_dir)

    test_step("删除测试目录", test_delete_dir)

    # ========== 测试结果汇总 ==========
    logger.info("=" * 80)
    logger.info("📊 测试结果汇总")
    logger.info("=" * 80)
    logger.info(f"✅ 通过: {test_results['passed']} 项")
    logger.info(f"❌ 失败: {test_results['failed']} 项")
    logger.info(f"📋 总计: {test_results['total']} 项")

    success_rate = (
        (test_results["passed"] / test_results["total"]) * 100
        if test_results["total"] > 0
        else 0
    )
    logger.info(f"🎯 成功率: {success_rate:.1f}%")

    if success_rate >= 90:
        logger.success("🎉 测试结果优秀！Dropbox 驱动运行良好")
    elif success_rate >= 70:
        logger.info("👍 测试结果良好，部分功能可能需要优化")
    else:
        logger.warning("⚠️  测试结果需要改进，请检查失败的功能")

    return success_rate >= 70


def quick_demo():
    """快速演示核心功能"""
    logger.info("=" * 60)
    logger.info("🚀 Dropbox 驱动快速演示")
    logger.info("=" * 60)

    # 初始化驱动
    drive = DropboxDrive()

    # 登录
    logger.info("1. 登录测试...")
    if not drive.login():
        logger.error("❌ 登录失败，请检查配置")
        return False
    logger.info("✅ 登录成功")

    # 获取配额信息
    logger.info("2. 获取配额信息...")
    quota = drive.get_quota()
    if quota:
        used_gb = quota.get("used_space", 0) / (1024**3)
        total_gb = quota.get("total_space", 0) / (1024**3)
        logger.info(f"✅ 已使用: {used_gb:.2f} GB / {total_gb:.2f} GB")

    # 获取根目录文件列表
    logger.info("3. 获取根目录文件列表...")
    files = drive.get_file_list("/")
    logger.info(f"✅ 找到 {len(files)} 个文件")
    for i, file in enumerate(files[:3]):  # 只显示前3个
        logger.info(f"   {i + 1}. {file.name} ({file.size} bytes)")

    # 创建测试目录
    logger.info("4. 创建测试目录...")
    test_dir_name = "quick_test"
    test_dir = f"/{test_dir_name}"
    if drive.mkdir("/", test_dir_name):
        logger.info(f"✅ 目录创建成功: {test_dir}")

        # 删除测试目录
        if drive.delete(test_dir):
            logger.info(f"✅ 目录删除成功: {test_dir}")

    logger.success("🎉 快速演示完成!")
    logger.info("💡 运行 'python example.py --test' 进行完整测试")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Dropbox 网盘驱动示例",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python example.py --test     # 运行综合功能测试（推荐）
  python example.py --demo     # 运行快速演示
  python example.py            # 默认运行快速演示

配置要求:
  需要在 nltsecret 中配置 Dropbox 访问令牌:
  - fundrive.dropbox.access_token: 您的 Dropbox API 访问令牌
  
  或者在环境变量中设置:
  - DROPBOX_ACCESS_TOKEN: 您的 Dropbox API 访问令牌

测试说明:
  --test: 运行完整的20项测试，包括核心接口、文件操作、高级功能等
  --demo: 运行快速演示，只测试最基本的4个功能
        """,
    )

    parser.add_argument("--test", action="store_true", help="运行综合功能测试")
    parser.add_argument("--demo", action="store_true", help="运行快速演示")

    args = parser.parse_args()

    # 显示欢迎信息
    logger.info("🎯 Dropbox 网盘驱动示例程序")
    logger.info("📦 基于 fundrive 框架开发")
    logger.info("🔗 项目地址: https://github.com/farfarfun/fundrive")

    try:
        if args.test:
            # 运行综合测试（优先测试核心接口）
            success = comprehensive_test()
        else:  # 默认或 --demo
            # 运行快速演示
            success = quick_demo()

        if success:
            logger.success("✨ 示例程序执行成功!")
            return 0
        else:
            logger.error("❌ 示例程序执行失败!")
            return 1

    except KeyboardInterrupt:
        logger.warning("⏹️  用户中断执行")
        return 1
    except Exception as e:
        logger.error(f"💥 程序执行出错: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
