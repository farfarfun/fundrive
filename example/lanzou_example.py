from fundrive.lanzou import LanZouDrive, download

downer = LanZouDrive()
downer.ignore_limits()
# 第一次必须输入`ylogin`和`phpdisk_info`，会存入本地缓存；后续可不再输入
downer.login_by_cookie()


def example1():
    print(downer.login_by_cookie())


def example2():
    downer.upload_file(file_path=".file_csv.csv")


def example3():
    # download("https://wwe.lanzoui.com/ig56tpia6rg", dir_pwd="./download/lanzou")
    # download('https://wws.lanzous.com/b01hh63kf', dir_pwd='./download/lanzou')
    downer.down_file_by_url("https://wwib.lanzoul.com/idDkH16xa5ef", path="./download/lanzou")


def example4():
    print("upload")
    # res = downer.upload_file('/tmp/models/yolo/configs/yolov3.h5', folder_id=2129808)
    # res = downer.upload_file("./download/file_csv.zip", folder_id=8577360)
    res = downer.upload_file("./download/lanzou/orientation1.zip", folder_id=8577360)

    print(res)


def example5():
    print(downer.get_dir_list(folder_id=2184164))


# example1()
# example2()
# example3()
example4()
# example5()
