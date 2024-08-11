import base64
import binascii
from pathlib import Path
from urllib.parse import parse_qs, urlparse, quote

from notetool.tool.log import log
from .bencode import bdecode, bencode

logger = log(__name__)


class Magnet:
    """
    magnet: 协议名。
    xt: exact topic 的缩写，表示资源定位点。BTIH（BitTorrent Info Hash）表示哈希方法名，这里还可以使用 SHA1 和 MD5。
        这个值是文件的标识符，是不可缺少的。
        一般来讲，一个磁力链接只需要上面两个参数即可找到唯一对应的资源。也有其他的可选参数提供更加详细的信息。
    dn: display name 的缩写，表示向用户显示的文件名。
    tr: tracker 的缩写，表示 tracker 服务器的地址。
    kt: 关键字，更笼统的搜索，指定搜索关键字而不是特定文件。
    mt: 文件列表，链接到一个包含磁力链接的元文件 (MAGMA - MAGnet MAnifest）。
    """

    def __init__(self, magnet_link):
        self.name = None
        self.trackers = []
        self.infohash = None

        try:
            self._parse_url(magnet_link)
        except Exception as e:
            logger.error("parse error {}".format(e))

    def _parse_url(self, magnet_link):
        url = urlparse(magnet_link)
        url_query = parse_qs(url.query)
        infohash = url_query["xt"][0].split(":")[2]

        if len(infohash) == 40:
            self.infohash = binascii.unhexlify(infohash)
        elif len(infohash) == 32:
            self.infohash = base64.b32decode(infohash)
        else:
            raise Exception("Unable to parse infohash")

        self.trackers = url_query.get("tr", [])
        name = url_query.get("dn")
        if name:
            self.name = name[0]
        else:
            self.name = infohash  # binascii.hexlify(infohash).decode()

        # TODO: better stripping
        self.name = self.name.strip(".").replace("/", "").replace("\\", "").replace(":", "")


class Torrent:
    def __init__(self, magnet: Magnet = None, data=None, cache_folder=None):
        self.length = 0
        self.name = ''
        self.piece_length = 0
        self.pieces = []
        self.data = data

        self.magnet = magnet
        self._cache_folder = cache_folder
        if self.data:
            self._parse_data()

    def __str__(self):
        return "{}  {}  {}".format(self.name, self.length, self.piece_length)

    def _cache_path(self):
        if self._cache_folder and self.magnet is not None:
            filename = binascii.hexlify(self.magnet.infohash).decode("utf-8")
            return Path(self._cache_folder) / Path(filename[:2]) / Path(filename[2:4]) / Path(filename)

    def _parse_data(self):
        try:
            self.name = quote(self.data[b'info'][b'name'])
            self.length = self.data[b'info'][b'length']
            self.piece_length = self.data[b'info'][b'piece length']
        except Exception as e:
            logger.error("parse error {}".format(e))

    def update_date(self, data):
        self.from_data(data)
        return self

    def from_data(self, data, decode=False):
        if decode:
            self.data = bdecode(data)
        else:
            self.data = data

        self._parse_data()
        return self

    def from_file(self, path):
        path = Path(path)
        if path and path.exists():
            data = Path(path).read_bytes()
            self.from_data(data, decode=True)
        return self

    def to_file(self, path) -> bool:
        if path is None:
            return False
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bencode(self.data))

        return True

    def read_cache(self):
        path = self._cache_path()
        if path and path.exists():
            self.from_file(path)
        if self.not_empty():
            logger.info("We had a cache at {}!s".format(path))

    def save_cache(self) -> bool:
        return self.to_file(self._cache_path())

    def empty(self) -> bool:
        return self.data is None

    def not_empty(self) -> bool:
        return not self.empty()

    def data_encode(self):
        return bencode(self.data)
