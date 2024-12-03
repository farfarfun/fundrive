from fundrive.drives import ZenodoDrive
from funsecret import read_secret

drive = ZenodoDrive()
drive.login(access_token=read_secret("fundrive", "zenodo", "access_token"))
drive.check_token()

for file in drive.get_file_list("13293150"):
    print(file)
# 下载一个record下的所有文件
drive.download_file(record_id="13293150", local_dir="./resource/songs")
