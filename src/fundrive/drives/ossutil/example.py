# 标准库导入
import os
import tempfile
from typing import Optional

# 第三方库导入
from nltlog import getLogger

# 项目内部导入
from fundrive.drives.ossutil import OSSUtilDrive


def test_ossutil_basic_operations():
    """测试ossutil驱动的基本操作"""
    logger = getLogger("ossutil_test")

    # 创建驱动实例
    drive = OSSUtilDrive()

    try:
        # 登录测试
        logger.info("🚀 开始登录测试...")
        if not drive.login():
            logger.error("❌ 登录失败，请检查配置")
            return False
        logger.success("✅ 登录成功")

        # 创建测试目录
        logger.info("🚀 测试创建目录...")
        test_dir = "fundrive_test"
        dir_id = drive.mkdir("", test_dir)
        if dir_id:
            logger.success(f"✅ 创建目录成功: {dir_id}")
        else:
            logger.error("❌ 创建目录失败")
            return False

        # 创建测试文件
        logger.info("🚀 测试文件上传...")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write("这是一个测试文件，用于验证ossutil驱动功能。")
            temp_file_path = temp_file.name

        try:
            # 上传文件
            if drive.upload_file(temp_file_path, test_dir):
                logger.success("✅ 文件上传成功")

                # 获取文件列表
                logger.info("🚀 测试获取文件列表...")
                files = drive.get_file_list(test_dir)
                logger.info(f"📊 找到 {len(files)} 个文件")
                for file in files:
                    logger.info(f"  - {file.name} ({file.size} bytes)")

                # 下载文件测试
                logger.info("🚀 测试文件下载...")
                if files:
                    download_dir = tempfile.mkdtemp()
                    if drive.download_file(files[0].fid, save_dir=download_dir):
                        logger.success("✅ 文件下载成功")
                    else:
                        logger.error("❌ 文件下载失败")

                # 搜索测试
                logger.info("🚀 测试文件搜索...")
                search_results = drive.search("test", fid=test_dir)
                logger.info(f"📊 搜索到 {len(search_results)} 个匹配文件")

                # 获取配额信息
                logger.info("🚀 测试获取配额信息...")
                quota = drive.get_quota()
                if quota:
                    logger.info(f"💾 存储空间使用情况:")
                    logger.info(f"  - 已用空间: {quota.get('used_space', 0)} bytes")
                    logger.info(f"  - 对象数量: {quota.get('object_count', 0)}")
                    logger.info(f"  - Bucket: {quota.get('bucket_name', 'N/A')}")

            else:
                logger.error("❌ 文件上传失败")
                return False

        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

        # 清理测试目录
        logger.info("🧹 清理测试数据...")
        if drive.delete(test_dir):
            logger.success("✅ 测试数据清理完成")

        logger.success("🎉 所有基本操作测试通过！")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False


def test_ossutil_advanced_features():
    """测试ossutil驱动的高级功能"""
    logger = getLogger("ossutil_advanced_test")

    drive = OSSUtilDrive()

    try:
        # 登录
        if not drive.login():
            logger.error("❌ 登录失败")
            return False

        # 创建测试环境
        test_dir = "fundrive_advanced_test"
        drive.mkdir("", test_dir)

        # 创建多个测试文件
        test_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=f"_test_{i}.txt", delete=False
            ) as temp_file:
                temp_file.write(f"测试文件 {i + 1} 的内容")
                test_files.append(temp_file.name)

        try:
            # 批量上传
            logger.info("🚀 测试批量上传...")
            for file_path in test_files:
                drive.upload_file(file_path, test_dir)

            # 获取文件列表
            files = drive.get_file_list(test_dir)
            if len(files) >= 3:
                logger.success("✅ 批量上传成功")

                # 测试文件复制
                logger.info("🚀 测试文件复制...")
                copy_dir = "fundrive_copy_test"
                drive.mkdir("", copy_dir)

                if drive.copy(files[0].fid, copy_dir):
                    logger.success("✅ 文件复制成功")

                # 测试文件移动
                logger.info("🚀 测试文件移动...")
                move_dir = "fundrive_move_test"
                drive.mkdir("", move_dir)

                if drive.move(files[1].fid, move_dir):
                    logger.success("✅ 文件移动成功")

                # 测试分享功能
                logger.info("🚀 测试文件分享...")
                share_result = drive.share(
                    files[0].fid, expire_days=1, description="测试分享"
                )
                if share_result and share_result.get("total", 0) > 0:
                    logger.success("✅ 文件分享成功")
                    logger.info(f"📎 分享链接: {share_result['links'][0]['url']}")

                # 测试获取下载链接
                logger.info("🚀 测试获取下载链接...")
                download_url = drive.get_download_url(files[0].fid)
                if download_url:
                    logger.success("✅ 获取下载链接成功")
                    logger.info(f"🔗 下载链接: {download_url}")

                # 清理测试数据
                drive.delete(test_dir)
                drive.delete(copy_dir)
                drive.delete(move_dir)

            else:
                logger.error("❌ 批量上传失败")
                return False

        finally:
            # 清理临时文件
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

        logger.success("🎉 所有高级功能测试通过！")
        return True

    except Exception as e:
        logger.error(f"❌ 高级功能测试过程中发生错误: {e}")
        return False


def quick_demo():
    """快速演示ossutil驱动的主要功能"""
    logger = getLogger("ossutil_demo")

    logger.info("=" * 60)
    logger.info("🎯 OSSUtil驱动快速演示")
    logger.info("=" * 60)

    # 创建驱动实例
    drive = OSSUtilDrive()

    # 登录
    logger.info("🔐 正在登录OSS服务...")
    if not drive.login():
        logger.error("❌ 登录失败，请检查配置信息")
        logger.info("💡 请确保已配置以下信息:")
        logger.info("   - fundrive.ossutil.access_key")
        logger.info("   - fundrive.ossutil.access_secret")
        logger.info("   - fundrive.ossutil.bucket_name")
        logger.info("   - fundrive.ossutil.endpoint")
        return

    logger.success("✅ 登录成功！")

    # 获取根目录文件列表
    logger.info("📁 获取根目录文件列表...")
    files = drive.get_file_list("")
    dirs = drive.get_dir_list("")

    logger.info(f"📊 根目录统计:")
    logger.info(f"   - 文件数量: {len(files)}")
    logger.info(f"   - 目录数量: {len(dirs)}")

    if files:
        logger.info("📄 最近的文件:")
        for i, file in enumerate(files[:5]):  # 显示前5个文件
            logger.info(f"   {i + 1}. {file.name} ({file.size} bytes)")

    if dirs:
        logger.info("📁 目录列表:")
        for i, dir in enumerate(dirs[:5]):  # 显示前5个目录
            logger.info(f"   {i + 1}. {dir.name}/")

    # 获取存储配额
    logger.info("💾 获取存储配额信息...")
    quota = drive.get_quota()
    if quota:
        logger.info(f"📊 存储空间使用情况:")
        logger.info(f"   - Bucket: {quota.get('bucket_name', 'N/A')}")
        logger.info(f"   - 已用空间: {quota.get('used_space', 0)} bytes")
        logger.info(f"   - 对象数量: {quota.get('object_count', 0)}")
        logger.info(f"   - 访问域名: {quota.get('endpoint', 'N/A')}")

    logger.info("=" * 60)
    logger.success("🎉 演示完成！ossutil驱动工作正常")
    logger.info("=" * 60)


def interactive_test():
    """交互式测试ossutil驱动功能"""
    logger = getLogger("ossutil_interactive")

    logger.info("🎮 OSSUtil驱动交互式测试")
    logger.info("=" * 50)

    drive = OSSUtilDrive()

    # 登录
    if not drive.login():
        logger.error("❌ 登录失败")
        return

    while True:
        print("\n" + "=" * 50)
        print("📋 可用操作:")
        print("1. 列出文件和目录")
        print("2. 创建目录")
        print("3. 上传文件")
        print("4. 下载文件")
        print("5. 搜索文件")
        print("6. 获取配额信息")
        print("7. 分享文件")
        print("8. 删除文件/目录")
        print("0. 退出")
        print("=" * 50)

        try:
            choice = input("请选择操作 (0-8): ").strip()

            if choice == "0":
                logger.info("👋 再见！")
                break
            elif choice == "1":
                path = input("请输入目录路径 (留空表示根目录): ").strip()
                files = drive.get_file_list(path)
                dirs = drive.get_dir_list(path)

                print(f"\n📁 目录: {path or '/'}")
                print(f"📊 统计: {len(dirs)} 个目录, {len(files)} 个文件")

                if dirs:
                    print("\n📁 目录:")
                    for i, dir in enumerate(dirs, 1):
                        print(f"  {i}. {dir.name}/")

                if files:
                    print("\n📄 文件:")
                    for i, file in enumerate(files, 1):
                        print(f"  {i}. {file.name} ({file.size} bytes)")

            elif choice == "2":
                parent = input("请输入父目录路径: ").strip()
                name = input("请输入目录名: ").strip()
                if name:
                    result = drive.mkdir(parent, name)
                    if result:
                        logger.success(f"✅ 目录创建成功: {result}")
                    else:
                        logger.error("❌ 目录创建失败")

            elif choice == "3":
                local_path = input("请输入本地文件路径: ").strip()
                remote_dir = input("请输入远程目录路径: ").strip()
                if local_path and os.path.exists(local_path):
                    if drive.upload_file(local_path, remote_dir):
                        logger.success("✅ 文件上传成功")
                    else:
                        logger.error("❌ 文件上传失败")
                else:
                    logger.error("❌ 本地文件不存在")

            elif choice == "4":
                file_id = input("请输入文件ID: ").strip()
                save_dir = input("请输入保存目录 (留空表示当前目录): ").strip() or "."
                if file_id:
                    if drive.download_file(file_id, save_dir=save_dir):
                        logger.success("✅ 文件下载成功")
                    else:
                        logger.error("❌ 文件下载失败")

            elif choice == "5":
                keyword = input("请输入搜索关键词: ").strip()
                search_dir = input("请输入搜索目录 (留空表示全局搜索): ").strip()
                if keyword:
                    results = drive.search(keyword, fid=search_dir or None)
                    print(f"\n🔍 搜索结果: 找到 {len(results)} 个匹配项")
                    for i, item in enumerate(results, 1):
                        print(
                            f"  {i}. {item.name} ({'文件' if item.isfile else '目录'})"
                        )

            elif choice == "6":
                quota = drive.get_quota()
                if quota:
                    print(f"\n💾 存储配额信息:")
                    print(f"  - Bucket: {quota.get('bucket_name', 'N/A')}")
                    print(f"  - 已用空间: {quota.get('used_space', 0)} bytes")
                    print(f"  - 对象数量: {quota.get('object_count', 0)}")
                    print(f"  - 访问域名: {quota.get('endpoint', 'N/A')}")

            elif choice == "7":
                file_id = input("请输入要分享的文件ID: ").strip()
                expire_days = input("请输入有效期(天，留空表示1小时): ").strip()
                if file_id:
                    expire = int(expire_days) if expire_days.isdigit() else 0
                    result = drive.share(file_id, expire_days=expire)
                    if result and result.get("total", 0) > 0:
                        print(f"\n📎 分享链接: {result['links'][0]['url']}")
                        logger.success("✅ 分享成功")
                    else:
                        logger.error("❌ 分享失败")

            elif choice == "8":
                file_id = input("请输入要删除的文件/目录ID: ").strip()
                if file_id:
                    confirm = input(f"确认删除 '{file_id}' 吗? (y/N): ").strip().lower()
                    if confirm == "y":
                        if drive.delete(file_id):
                            logger.success("✅ 删除成功")
                        else:
                            logger.error("❌ 删除失败")

            else:
                logger.warning("⚠️ 无效的选择，请重新输入")

        except KeyboardInterrupt:
            logger.info("\n👋 用户取消操作，退出程序")
            break
        except Exception as e:
            logger.error(f"❌ 操作失败: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "basic":
            test_ossutil_basic_operations()
        elif mode == "advanced":
            test_ossutil_advanced_features()
        elif mode == "demo":
            quick_demo()
        elif mode == "interactive":
            interactive_test()
        else:
            print("用法: python example.py [basic|advanced|demo|interactive]")
    else:
        # 默认运行快速演示
        quick_demo()
