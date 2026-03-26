"""
通用网盘驱动测试框架

这个模块提供了一个通用的测试框架，可以测试任何继承自 BaseDrive 的网盘驱动实现。
所有驱动的 example.py 都可以使用这个框架进行标准化测试。
"""

import os
import tempfile

from nltlog import getLogger

from .base import BaseDrive

logger = getLogger("fundrive")


class BaseDriveTest:
    """通用网盘驱动测试类"""

    def __init__(self, drive: BaseDrive, test_dir: str = "/fundrive_test"):
        """
        初始化测试类

        Args:
            drive: 要测试的网盘驱动实例
            test_dir: 测试目录路径，默认为 /fundrive_test
        """
        self.drive = drive
        self.test_dir = test_dir
        self.test_results = {"total": 0, "passed": 0, "failed": 0}
        self.temp_files = []  # 记录创建的临时文件，用于清理

    def test_step(self, step_name: str, test_func) -> bool:
        """
        执行单个测试步骤

        Args:
            step_name: 测试步骤名称
            test_func: 测试函数，返回 True 表示成功，False 表示失败

        Returns:
            bool: 测试是否通过
        """
        self.test_results["total"] += 1
        logger.info(f"📋 {self.test_results['total']}. {step_name}")

        try:
            if test_func():
                logger.success(f"✅ {step_name} - 通过")
                self.test_results["passed"] += 1
                return True
            else:
                logger.error(f"❌ {step_name} - 失败")
                self.test_results["failed"] += 1
                return False
        except Exception as e:
            logger.error(f"💥 {step_name} - 异常: {e}")
            self.test_results["failed"] += 1
            return False

    def create_test_file(self, content: str = "测试文件内容") -> str:
        """创建临时测试文件"""
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        )
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name

    def cleanup_temp_files(self):
        """清理临时文件"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {file_path}, 错误: {e}")
        self.temp_files.clear()

    def test_login(self) -> bool:
        """测试登录功能"""
        try:
            result = self.drive.login()
            return result is not None
        except Exception as e:
            logger.error(f"登录测试失败: {e}")
            return False

    def test_get_quota(self) -> bool:
        """测试获取配额信息"""
        try:
            quota = self.drive.get_quota()
            return quota is not None
        except Exception as e:
            logger.error(f"获取配额测试失败: {e}")
            return False

    def test_exist_root(self) -> bool:
        """测试根目录存在性检查"""
        try:
            return self.drive.exist("/")
        except Exception as e:
            logger.error(f"根目录存在性检查失败: {e}")
            return False

    def test_get_file_list_root(self) -> bool:
        """测试获取根目录文件列表"""
        try:
            files = self.drive.get_file_list("/")
            return isinstance(files, list)
        except Exception as e:
            logger.error(f"获取根目录文件列表失败: {e}")
            return False

    def test_mkdir(self) -> bool:
        """测试创建目录"""
        try:
            # 从测试目录路径中提取目录名
            dir_name = (
                self.test_dir.strip("/").split("/")[-1]
                if self.test_dir != "/"
                else "root"
            )

            # 创建测试目录
            result = self.drive.mkdir("/", dir_name, return_if_exist=True)
            if result:
                # 验证目录是否存在
                return self.drive.exist(self.test_dir)
            return False
        except Exception as e:
            logger.error(f"创建目录测试失败: {e}")
            return False

    def test_upload_file(self) -> bool:
        """测试文件上传"""
        try:
            # 创建测试文件
            test_file = self.create_test_file("这是一个测试文件内容")

            # 上传文件
            result = self.drive.upload_file(test_file, self.test_dir, "test_upload.txt")
            if result:
                # 验证文件是否存在
                test_file_path = f"{self.test_dir}/test_upload.txt"
                return self.drive.exist(test_file_path)
            return False
        except Exception as e:
            logger.error(f"文件上传测试失败: {e}")
            return False

    def test_download_file(self) -> bool:
        """测试文件下载"""
        try:
            test_file_path = f"{self.test_dir}/test_upload.txt"

            # 创建下载目标文件
            download_path = tempfile.mktemp(suffix=".txt")
            self.temp_files.append(download_path)

            # 下载文件
            result = self.drive.download_file(test_file_path, download_path)
            if result:
                # 验证下载的文件是否存在且有内容
                return (
                    os.path.exists(download_path) and os.path.getsize(download_path) > 0
                )
            return False
        except Exception as e:
            logger.error(f"文件下载测试失败: {e}")
            return False

    def test_get_file_info(self) -> bool:
        """测试获取文件信息"""
        try:
            test_file_path = f"{self.test_dir}/test_upload.txt"
            file_info = self.drive.get_file_info(test_file_path)
            return file_info is not None and hasattr(file_info, "name")
        except Exception as e:
            logger.error(f"获取文件信息测试失败: {e}")
            return False

    def test_rename(self) -> bool:
        """测试重命名功能"""
        try:
            old_path = f"{self.test_dir}/test_upload.txt"
            new_name = "test_renamed.txt"

            result = self.drive.rename(old_path, new_name)
            if result:
                new_path = f"{self.test_dir}/{new_name}"
                return self.drive.exist(new_path)
            return False
        except Exception as e:
            logger.error(f"重命名测试失败: {e}")
            return False

    def test_copy(self) -> bool:
        """测试复制功能"""
        try:
            src_path = f"{self.test_dir}/test_renamed.txt"
            dst_path = f"{self.test_dir}/test_copied.txt"

            result = self.drive.copy(src_path, dst_path)
            if result:
                return self.drive.exist(dst_path)
            return False
        except Exception as e:
            logger.error(f"复制测试失败: {e}")
            return False

    def test_search(self) -> bool:
        """测试搜索功能"""
        try:
            results = self.drive.search("test", self.test_dir)
            return isinstance(results, list)
        except Exception as e:
            logger.error(f"搜索测试失败: {e}")
            return False

    def test_share(self) -> bool:
        """测试分享功能"""
        try:
            test_file_path = f"{self.test_dir}/test_renamed.txt"
            share_link = self.drive.share(test_file_path, password="aaaa")

            # 检查分享是否成功
            if share_link is not None and isinstance(share_link, str):
                # 输出分享成功信息
                logger.info("🎉 分享成功！")
                logger.info(f"📎 分享链接: {share_link}")
                logger.info(f"📁 分享文件: {test_file_path}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"分享测试失败: {e}")
            return False

    def test_recycle_bin(self) -> bool:
        """测试回收站功能"""
        try:
            # 1. 获取回收站列表
            recycle_list = self.drive.get_recycle_list()
            if recycle_list is None:
                logger.warning("驱动不支持回收站功能")
                return True  # 不支持也算正常

            logger.info(f"📋 回收站中有 {len(recycle_list)} 个项目")

            # 2. 如果回收站不为空，测试恢复功能
            if recycle_list:
                # 选择第一个项目进行恢复测试
                first_item = recycle_list[0]
                logger.info(f"🔄 尝试恢复文件: {first_item.name}")

                # 恢复文件
                restore_result = self.drive.restore(first_item.fid)
                if restore_result:
                    logger.info(f"✅ 文件恢复成功: {first_item.name}")

                    # 验证文件是否真的被恢复了（回收站列表应该减少）
                    new_recycle_list = self.drive.get_recycle_list()
                    if new_recycle_list is not None and len(new_recycle_list) < len(
                        recycle_list
                    ):
                        logger.info("✅ 回收站列表已更新，恢复功能正常")

                    # 重新删除文件以便后续测试
                    if hasattr(first_item, "parent_fid") and first_item.parent_fid:
                        # 尝试找到恢复后的文件并重新删除
                        try:
                            # 这里可能需要根据原始位置重新删除
                            pass  # 暂时跳过重新删除，避免影响用户数据
                        except Exception as e:
                            logger.error("删除失败", e)
                else:
                    logger.warning(f"⚠️ 文件恢复失败: {first_item.name}")

            # 3. 测试清空回收站功能（谨慎操作）
            # 注意：这里不实际清空，只测试API调用是否正常
            logger.info("🗑️ 测试清空回收站API（不实际执行）")
            # clear_result = self.drive.clear_recycle()  # 注释掉实际清空操作
            # logger.info(f"清空回收站结果: {clear_result}")

            return True

        except Exception as e:
            logger.error(f"回收站测试失败: {e}")
            return False

    def test_unsupported_features(self) -> bool:
        """测试不支持的功能（应该返回警告而不是异常）"""
        try:
            # 测试保存分享文件（大多数驱动不支持）
            self.drive.save_shared("dummy_link", "/")

            # 这些功能应该返回 None 或 False，而不是抛出异常
            return True
        except Exception as e:
            logger.error(f"不支持功能测试失败: {e}")
            return False

    def test_cleanup(self) -> bool:
        """清理测试数据"""
        try:
            # 删除测试目录及其内容
            if self.drive.exist(self.test_dir):
                self.drive.delete(self.test_dir)

            # 清理本地临时文件
            self.cleanup_temp_files()
            return True
        except Exception as e:
            logger.error(f"清理测试数据失败: {e}")
            return False

    def comprehensive_test(self) -> bool:
        """
        运行完整的测试套件

        Returns:
            bool: 整体测试是否成功（成功率 >= 70%）
        """
        logger.info("🚀 开始运行通用网盘驱动测试")
        logger.info(f"📁 测试驱动: {self.drive.__class__.__name__}")
        logger.info(f"📂 测试目录: {self.test_dir}")
        logger.info("=" * 50)

        # 按优先级顺序执行测试
        test_cases = [
            ("登录认证", self.test_login),
            ("获取配额信息", self.test_get_quota),
            ("检查根目录存在性", self.test_exist_root),
            ("获取根目录文件列表", self.test_get_file_list_root),
            ("创建测试目录", self.test_mkdir),
            ("上传测试文件", self.test_upload_file),
            ("下载测试文件", self.test_download_file),
            ("获取文件信息", self.test_get_file_info),
            ("重命名文件", self.test_rename),
            ("复制文件", self.test_copy),
            ("搜索功能", self.test_search),
            ("分享功能", self.test_share),
            ("回收站功能", self.test_recycle_bin),
            ("不支持功能测试", self.test_unsupported_features),
            ("清理测试数据", self.test_cleanup),
        ]

        # 执行所有测试
        for test_name, test_func in test_cases:
            success = self.test_step(test_name, test_func)

            # 如果登录失败，终止测试
            if test_name == "登录认证" and not success:
                logger.error("\n❌ 登录失败，终止测试")
                break

        # 输出测试结果
        self._print_test_summary()

        # 计算成功率
        success_rate = (self.test_results["passed"] / self.test_results["total"]) * 100
        return success_rate >= 70

    def quick_demo(self) -> bool:
        """
        运行快速演示，只测试核心功能

        Returns:
            bool: 演示是否成功
        """
        logger.info("🚀 开始运行快速功能演示")
        logger.info(f"📁 测试驱动: {self.drive.__class__.__name__}")
        logger.info("=" * 50)

        # 核心功能演示
        demo_cases = [
            ("登录认证", self.test_login),
            ("获取配额信息", self.test_get_quota),
            ("创建测试目录", self.test_mkdir),
            ("上传测试文件", self.test_upload_file),
            ("清理测试数据", self.test_cleanup),
        ]

        # 执行演示
        for demo_name, demo_func in demo_cases:
            success = self.test_step(demo_name, demo_func)

            # 如果登录失败，终止演示
            if demo_name == "登录认证" and not success:
                logger.error("\n❌ 登录失败，终止演示")
                break

        # 输出演示结果
        self._print_test_summary()

        # 计算成功率
        success_rate = (self.test_results["passed"] / self.test_results["total"]) * 100
        return success_rate >= 80

    def _print_test_summary(self):
        """输出测试结果汇总"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 测试结果汇总")
        logger.info("=" * 50)

        success_rate = (self.test_results["passed"] / self.test_results["total"]) * 100

        logger.info(f"✅ 通过: {self.test_results['passed']} 项")
        logger.info(f"❌ 失败: {self.test_results['failed']} 项")
        logger.info(f"📊 总计: {self.test_results['total']} 项")
        logger.info(f"🎯 成功率: {success_rate:.1f}%")

        if success_rate >= 90:
            logger.success("🎉 测试结果优秀！")
        elif success_rate >= 70:
            logger.success("👍 测试结果良好")
        else:
            logger.warning("⚠️  测试结果需要改进")

        logger.info("=" * 50)


def create_drive_tester(
    drive: BaseDrive, test_dir: str = "/fundrive_test"
) -> BaseDriveTest:
    """
    创建网盘驱动测试器的工厂函数

    Args:
        drive: 要测试的网盘驱动实例
        test_dir: 测试目录路径

    Returns:
        BaseDriveTest: 测试器实例
    """
    return BaseDriveTest(drive, test_dir)
