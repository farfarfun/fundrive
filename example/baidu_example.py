import urllib

from fundrive.baidu.drive import BaiDuDrive

client = BaiDuDrive()


def test():
    for path in client.list_deep("/drive/example/api"):
        print(path['path'])


def test2():
    client.upload('test.txt', '/drive/example/api/test.txt', overwrite=False)
    client.download('/temp.txt', 'temp.txt')

    client.upload_dir('/Users/liangtaoniu/workspace/MyDiary/logs', '/drive/example/api/')


def test3():
    client.download('/drive/example/api/30个免费的信息图源文件.zip', '30个免费的信息图源文件.zip', overwrite=True)
    client.download('/drive/example/api/dirs2/jupyter-run-2019-09-16.log', 'jupyter-run-2019-09-16.log', overwrite=True)


def test4():
    source_url = 'ed2k://|file|%E8%A1%8C%E5%B0%B8%E8%B5%B0%E8%82%89.The.Walking.Dead.S02E01.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.BDrip.1080P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|910568992|ABFB39A113E173197D4AD2D21E5D2CB8|h=7BLB2TLX3KKQXLGO553D6BFKWKG5PYW7|/'
    print(client.offline_task_add(source_url=source_url))


def test5():
    urls = """
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E14.END.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|752289928|cf9f511befa95ae845d197c0d8282f79|h=u5f7z4f5jg5cjza4goa4uajqbpreluzu|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E13.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|555690110|08ca523ea148b3816035c9048d2545d3|h=j4b6m2hhvz2ujub72pbd3jfxp5cwf24x|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E12.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|529238351|09b31a8011617c9beb6834935d38f7bc|h=oanhmm6s7flbvfhs7hplpqjaxlruso6w|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E11.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|566749745|01e31b07b42ceb6a3f8f826123419ef4|h=nr555xrzv7qambwpn637q2nm6kmmwepz|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E10.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|552894824|c90f04796a85a85f7f091df72af803e0|h=frx3krkco6m7un3n7k6mmcxhzs5cxjne|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E09.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|606807457|75cca7710d50d879f6d5fb910197b4cc|h=wnguleyxj6moorpodwt6oz5fwkmwf2sv|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E08.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|630200934|de3fbc1da380d1fc574b1ec0f98c0c2c|h=4nqzdmw73qkcevmsgvwy3rn2yoj7w2ri|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E07.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|462306329|f3f748bde50c23902b0b04774e848973|h=4yw46s2y2elrbaly5rfddzhkok5cys7h|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E06.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|646947279|187be4a2663b8f7a5e33390a7f707238|h=6vkivvm3b45ldnnc5irqembqrmrknf64|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E05.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|602693853|a09bc74c876f2ce201a309240402c828|h=frpmpmwhn73amra7bjawevgdujgelzeh|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E04.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|595331644|237bd347ea8ca168a3dd5490ef81ea41|h=h343wetur7zwxclytgy7bkibtfflt7ol|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E03.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|573534855|b5bf373e12f3fdd9b7a32cfad9b9601d|h=4hatstwpph2jhheifs2gddoyykmbvtuz|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E02.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|507434909|632ebb589f485bbd7c222558e89f2a66|h=ycecv6t4s6yvmqcvjzao72w4bceabdwr|/
    ed2k://|file|%E6%98%9F%E9%99%85%E8%BF%B7%E8%88%AA%EF%BC%9A%E5%8F%91%E7%8E%B0%E5%8F%B7.Star.Trek.Discovery.S02E01.%E4%B8%AD%E8%8B%B1%E5%AD%97%E5%B9%95.WEB.720P-%E4%BA%BA%E4%BA%BA%E5%BD%B1%E8%A7%86.mp4|707140666|356bf275716cac19495c0ae15101d175|h=i33ovt3b33g3ulmh7sohfoy4odwbvdkc|/
    """.split("\n")
    for url in urls:
        if len(url) > 10:
            name = urllib.parse.unquote(url.split('|')[2])
            path = '/apps/temp/' + name
            print(client.offline_task_add(save_path=path, source_url=url))
