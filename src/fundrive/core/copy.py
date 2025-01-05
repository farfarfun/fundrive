from fundrive.core import BaseDrive


def copy_data(drive1: BaseDrive, drive2: BaseDrive, from_fid: str, to_fid: str):
    info = drive1.get_dir_info(from_fid)
    to_fid = drive2.mkdir(fid=to_fid, name=info["name"])
    local_dir = f"tmp/{info['name']}"
    drive1.download_dir(fid=from_fid, local_dir=local_dir)
    drive2.upload_dir(local_path=local_dir, fid=to_fid)
