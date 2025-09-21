#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunDrive 集成示例代码

本文件展示了如何在实际应用中集成和使用FunDrive框架
包含常见的使用场景和最佳实践
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

from fundrive import (
    get_drive,
    list_available_drives,
    BaseDrive,
    DriveFile,
    AuthenticationError,
    NetworkError,
    UploadError,
    DownloadError,
    format_size,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CloudStorageManager:
    """云存储管理器 - 统一管理多个云存储服务"""

    def __init__(self, config_file: str = "cloud_config.json"):
        """
        初始化云存储管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.drives: Dict[str, BaseDrive] = {}
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            logger.warning(f"配置文件不存在: {self.config_file}")
            return {}

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def add_drive(self, name: str, drive_type: str, **kwargs) -> bool:
        """
        添加云存储驱动

        Args:
            name: 驱动名称（用于标识）
            drive_type: 驱动类型
            **kwargs: 驱动配置参数

        Returns:
            bool: 是否添加成功
        """
        try:
            # 从配置文件获取参数
            config_params = self.config.get(name, {})
            config_params.update(kwargs)

            # 创建驱动实例
            drive = get_drive(drive_type, **config_params)

            # 尝试登录
            if drive.login():
                self.drives[name] = drive
                logger.info(f"成功添加驱动: {name} ({drive_type})")
                return True
            else:
                logger.error(f"驱动登录失败: {name}")
                return False

        except Exception as e:
            logger.error(f"添加驱动失败 {name}: {e}")
            return False

    def get_drive(self, name: str) -> Optional[BaseDrive]:
        """获取指定的驱动实例"""
        return self.drives.get(name)

    def list_drives(self) -> List[str]:
        """列出所有已添加的驱动"""
        return list(self.drives.keys())

    def sync_file(
        self,
        source_drive: str,
        source_fid: str,
        target_drive: str,
        target_fid: str,
        filename: str,
    ) -> bool:
        """
        在两个云存储之间同步文件

        Args:
            source_drive: 源驱动名称
            source_fid: 源文件ID
            target_drive: 目标驱动名称
            target_fid: 目标目录ID
            filename: 文件名

        Returns:
            bool: 同步是否成功
        """
        source = self.get_drive(source_drive)
        target = self.get_drive(target_drive)

        if not source or not target:
            logger.error("源或目标驱动不存在")
            return False

        try:
            # 创建临时文件路径
            temp_path = f"/tmp/fundrive_sync_{filename}"

            # 从源驱动下载文件
            logger.info(f"从 {source_drive} 下载文件: {filename}")
            if not source.download_file(source_fid, filepath=temp_path):
                logger.error("下载文件失败")
                return False

            # 上传到目标驱动
            logger.info(f"上传文件到 {target_drive}: {filename}")
            success = target.upload_file(temp_path, target_fid)

            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if success:
                logger.info(f"文件同步成功: {filename}")
            else:
                logger.error("上传文件失败")

            return success

        except Exception as e:
            logger.error(f"文件同步失败: {e}")
            return False


class FileBackupService:
    """文件备份服务 - 自动备份本地文件到云存储"""

    def __init__(self, storage_manager: CloudStorageManager):
        """
        初始化备份服务

        Args:
            storage_manager: 云存储管理器实例
        """
        self.storage_manager = storage_manager

    def backup_directory(
        self,
        local_path: str,
        drive_name: str,
        remote_path: str = None,
        exclude_patterns: List[str] = None,
    ) -> bool:
        """
        备份本地目录到云存储

        Args:
            local_path: 本地目录路径
            drive_name: 目标驱动名称
            remote_path: 远程目录路径（可选）
            exclude_patterns: 排除的文件模式列表

        Returns:
            bool: 备份是否成功
        """
        drive = self.storage_manager.get_drive(drive_name)
        if not drive:
            logger.error(f"驱动不存在: {drive_name}")
            return False

        try:
            # 创建远程备份目录
            if not remote_path:
                remote_path = f"backup_{os.path.basename(local_path)}"

            backup_dir_id = drive.mkdir(drive.root_fid, remote_path)
            logger.info(f"创建备份目录: {remote_path}")

            # 递归备份文件
            return self._backup_recursive(
                drive, local_path, backup_dir_id, exclude_patterns
            )

        except Exception as e:
            logger.error(f"备份失败: {e}")
            return False

    def _backup_recursive(
        self,
        drive: BaseDrive,
        local_path: str,
        remote_dir_id: str,
        exclude_patterns: List[str] = None,
    ) -> bool:
        """递归备份目录"""
        exclude_patterns = exclude_patterns or []

        try:
            for item in os.listdir(local_path):
                # 检查是否需要排除
                if any(pattern in item for pattern in exclude_patterns):
                    continue

                item_path = os.path.join(local_path, item)

                if os.path.isfile(item_path):
                    # 备份文件
                    logger.info(f"备份文件: {item}")
                    if not drive.upload_file(item_path, remote_dir_id):
                        logger.warning(f"文件备份失败: {item}")

                elif os.path.isdir(item_path):
                    # 创建远程目录并递归备份
                    sub_dir_id = drive.mkdir(remote_dir_id, item)
                    self._backup_recursive(
                        drive, item_path, sub_dir_id, exclude_patterns
                    )

            return True

        except Exception as e:
            logger.error(f"递归备份失败: {e}")
            return False


class CloudFileSearcher:
    """云文件搜索器 - 跨多个云存储搜索文件"""

    def __init__(self, storage_manager: CloudStorageManager):
        """
        初始化搜索器

        Args:
            storage_manager: 云存储管理器实例
        """
        self.storage_manager = storage_manager

    def search_across_drives(
        self, keyword: str, file_type: str = None
    ) -> Dict[str, List[DriveFile]]:
        """
        跨多个云存储搜索文件

        Args:
            keyword: 搜索关键词
            file_type: 文件类型过滤

        Returns:
            Dict[str, List[DriveFile]]: 按驱动名称分组的搜索结果
        """
        results = {}

        for drive_name in self.storage_manager.list_drives():
            drive = self.storage_manager.get_drive(drive_name)

            try:
                # 在当前驱动中搜索
                files = drive.search(keyword, file_type=file_type)
                if files:
                    results[drive_name] = files
                    logger.info(f"在 {drive_name} 中找到 {len(files)} 个文件")

            except Exception as e:
                logger.warning(f"在 {drive_name} 中搜索失败: {e}")

        return results

    def find_duplicates(self) -> Dict[str, List[tuple]]:
        """
        查找跨云存储的重复文件

        Returns:
            Dict[str, List[tuple]]: 重复文件列表，格式为 {filename: [(drive_name, file_info), ...]}
        """
        all_files = {}
        duplicates = {}

        # 收集所有驱动中的文件信息
        for drive_name in self.storage_manager.list_drives():
            drive = self.storage_manager.get_drive(drive_name)

            try:
                # 获取根目录下的所有文件
                files = self._get_all_files_recursive(drive, drive.root_fid)

                for file in files:
                    filename = file.name
                    file_size = file.size

                    # 使用文件名和大小作为重复检测的键
                    key = f"{filename}_{file_size}"

                    if key not in all_files:
                        all_files[key] = []

                    all_files[key].append((drive_name, file))

            except Exception as e:
                logger.warning(f"获取 {drive_name} 文件列表失败: {e}")

        # 找出重复文件
        for key, file_list in all_files.items():
            if len(file_list) > 1:
                filename = file_list[0][1].name
                duplicates[filename] = file_list

        return duplicates

    def _get_all_files_recursive(
        self, drive: BaseDrive, dir_id: str
    ) -> List[DriveFile]:
        """递归获取目录下的所有文件"""
        all_files = []

        try:
            # 获取当前目录的文件
            files = drive.get_file_list(dir_id)
            all_files.extend(files)

            # 递归处理子目录
            dirs = drive.get_dir_list(dir_id)
            for dir_info in dirs:
                sub_files = self._get_all_files_recursive(drive, dir_info.fid)
                all_files.extend(sub_files)

        except Exception as e:
            logger.warning(f"递归获取文件失败: {e}")

        return all_files


def main():
    """主函数 - 演示FunDrive的集成使用"""

    # 1. 创建云存储管理器
    logger.info("=== FunDrive 集成示例 ===")
    manager = CloudStorageManager()

    # 2. 添加多个云存储驱动
    logger.info("添加云存储驱动...")

    # 添加本地文件系统（用于测试）
    manager.add_drive("local", "local")

    # 如果有配置，可以添加其他驱动
    # manager.add_drive("google", "google", credentials_file="creds.json")
    # manager.add_drive("dropbox", "dropbox", access_token="your_token")

    # 3. 列出可用驱动
    logger.info(f"可用驱动: {manager.list_drives()}")

    # 4. 创建备份服务
    backup_service = FileBackupService(manager)

    # 5. 创建搜索服务
    searcher = CloudFileSearcher(manager)

    # 6. 演示功能
    if "local" in manager.list_drives():
        local_drive = manager.get_drive("local")

        # 创建测试目录和文件
        test_dir = "/tmp/fundrive_test"
        os.makedirs(test_dir, exist_ok=True)

        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("这是一个测试文件")

        logger.info("创建测试文件完成")

        # 演示文件操作
        try:
            # 上传文件
            root_id = local_drive.root_fid or "/tmp"
            success = local_drive.upload_file(test_file, root_id)
            logger.info(f"文件上传结果: {success}")

            # 列出文件
            files = local_drive.get_file_list(root_id)
            logger.info(f"找到 {len(files)} 个文件")

            for file in files[:5]:  # 只显示前5个
                size_str = format_size(file.size) if file.size else "未知"
                logger.info(f"  - {file.name} ({size_str})")

        except Exception as e:
            logger.error(f"演示操作失败: {e}")

    logger.info("=== 演示完成 ===")


if __name__ == "__main__":
    main()
