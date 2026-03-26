from typing import List

from fundrive import DriveFile


def print_files(files: List[DriveFile], title: str = "文件列表"):
    """打印文件列表"""
    print(f"\n📁 {title} (共 {len(files)} 个):")
    if not files:
        print("  (空)")
        return

    for i, file in enumerate(files, 1):
        file_type = "📁" if file.ext.get("type") == "folder" else "📄"
        size_str = f"{file.size:,} bytes" if file.size > 0 else "-"
        print(f"  {i:2d}. {file_type} {file.name}")
        print(f"      路径: {file.fid}")
        print(f"      大小: {size_str}")
        if file.ext.get("modified"):
            print(f"      修改时间: {file.ext['modified']}")
