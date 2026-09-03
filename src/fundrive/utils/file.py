from farlog import getLogger

from fundrive import DriveFile

logger = getLogger("fundrive.utils.file")


def print_files(files: list[DriveFile], title: str = "文件列表"):
    """打印文件列表（供 example.py 等 CLI 展示脚本调用，走统一日志出口而非裸 print）。"""
    logger.info(f"📁 {title} (共 {len(files)} 个):")
    if not files:
        logger.info("  (空)")
        return

    for i, file in enumerate(files, 1):
        file_type = "📁" if file.ext.get("type") == "folder" else "📄"
        size_str = f"{file.size:,} bytes" if file.size > 0 else "-"
        logger.info(f"  {i:2d}. {file_type} {file.name}")
        logger.info(f"      路径: {file.fid}")
        logger.info(f"      大小: {size_str}")
        if file.ext.get("modified"):
            logger.info(f"      修改时间: {file.ext['modified']}")
