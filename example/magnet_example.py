from fundrive.magnet.core import Magnet2Torrent

magnet = "magnet:?xt=urn:btih:e2467cbf021192c241367b892230dc1e05c0580e&dn=ubuntu-19.10-desktop-amd64.iso&tr=https%3A%2F%2Ftorrent.ubuntu.com%2Fannounce&tr=https%3A%2F%2Fipv6.torrent.ubuntu.com%2Fannounce"
magnet = "magnet:?xt=urn:btih:59e4b89b44a639aaa641113fc5a1c82c56fdc217&dn=愤怒的小鸟BD国粤英3语中英双字.电影天堂.www.dy2018.com.mp4"
mt = Magnet2Torrent(use_additional_trackers=True)
res = mt.get_magnet_info(magnet)
print(res)
