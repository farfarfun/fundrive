from fundrive.drives.pan115 import Pan115Drive


drive = Pan115Drive()
drive.login()


def add(fid):
    for f in drive.get_dir_list(fid):
        print(f)
        add(f["fid"])
    for f in drive.get_file_list(fid):
        print(f)


add("3383167882122639641")
