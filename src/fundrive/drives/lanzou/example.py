from fundrive.drives import LanZouDrive

downer = LanZouDrive()
downer.ignore_limit()
# 第一次必须输入`ylogin`和`phpdisk_info`，会存入本地缓存；后续可不再输入
downer.login()


def example1():
    print(downer.login_by_cookie())


def example2():
    downer.upload_file(file_path=".file_csv.csv")


def example3():
    # download("https://wwe.lanzoui.com/ig56tpia6rg", dir_pwd="./download/lanzou")
    # download('https://wws.lanzous.com/b01hh63kf', dir_pwd='./download/lanzou')
    # downer.download_file(fid=133463386)
    downer.download_dir(fid="6073427", local_dir="cache")


def example4():
    print("upload")
    # res = downer.upload_file('/tmp/models/yolo/configs/yolov3.h5', folder_id=2129808)
    # res = downer.upload_file("./download/file_csv.zip", folder_id=8577360)
    res = downer.upload_file("./download", folder_id=8577360)

    print(res)


def example5():
    print(downer.get_file_list(path=6073427))


# example1()
# example2()
example3()
# example4()
# example5()
