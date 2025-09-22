"""
ossutil驱动模块

基于阿里云OSS官方命令行工具ossutil的云存储驱动
"""

from .drive import OSSUtilDrive

__all__ = ["OSSUtilDrive"]
