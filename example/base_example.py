from fundrive.base import PyCurlDownLoad

downer = PyCurlDownLoad()
url = 'https://image.jiqizhixin.com/uploads/article/cover_image/a3f6d833-6dd0-483b-9df0-19321ebf7bbf/%E5%BE%AE%E4%BF%A1%E5%9B%BE%E7%89%87_20200630102712.png?imageView2/1/w/390/h/282'
downer.download(url=url, path='download/base/a.jpg', overwrite=True)
