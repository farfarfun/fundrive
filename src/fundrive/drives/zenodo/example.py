from funsecret import read_secret

from fundrive.drives import ZenodoDrive

drive = ZenodoDrive()
drive.login(access_token=read_secret("fundrive", "zenodo", "access_token"))
drive.check_token()

for file in drive.get_file_list("13293150"):
    print(file)
# 下载一个record下的所有文件
drive.download_file(record_id="13293150", local_dir="./resource/songs")

record_id = drive.mkdir()["metadata"]["prereserve_doi"]["recid"]

drive.upload_dir(local_path="./resource/songs", record_id=record_id)

drive.publish(
    record_id=record_id,
    title="funmaterial-audio",
    description="funmaterial-audio",
    names="funmaterial-audio",
)
