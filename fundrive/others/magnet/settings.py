import random

import requests

METADATA_EXCHANGE = 1 << 20

PEER_ID = b"-MD100A-" + bytes([random.randint(0, 255) for _ in range(12)])

MAX_PACKET_SIZE = 2 ** 15

EXTENDED_ID_METADATA = 1

DEFAULT_TRACKERS = [
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://tracker.leechers-paradise.org:6969/announce",
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://p4p.arenabg.com:1337/announce",
    "udp://9.rarbg.to:2710/announce",
    "udp://9.rarbg.me:2710/announce",
    "udp://tracker.pomf.se:80/announce",
    "udp://tracker.openbittorrent.com:80/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.tiny-vps.com:6969/announce",
    "udp://tracker.moeking.me:6969/announce",
    "udp://retracker.lanta-net.ru:2710/announce",
    "udp://open.stealth.si:80/announce",
    "udp://denis.stalker.upeer.me:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://tracker.cyberia.is:6969/announce",
    "udp://open.demonii.si:1337/announce",
    "udp://ipv4.tracker.harry.lu:80/announce",
    "udp://tracker3.itzmx.com:6961/announce",
    "udp://zephir.monocul.us:6969/announce",
]
# DEFAULT_TRACKERS = [line for line in requests.get('https://trackerslist.com/all.txt').text.split('\n') if len(line) > 0 and '[' not in line]
DEFAULT_TRACKERS = [line for line in requests.get('https://trackerslist.com/best.txt').text.split('\n') if
                    len(line) > 0 and '[' not in line]

BITTORRENT_PORT = random.randint(10000, 60000)

SERVE_APIKEY = None

DHT_BOOTSTRAP_NODES = [  # TODO: make hostnames and resolve on demand
    ("82.221.103.244", 6881),
    ("67.215.246.10", 6881),
    ("212.129.33.59", 6881),
    ("87.98.162.88", 6881),
    ("174.129.43.152", 6881),
]
DHT_PORT = 6881
DHT_SERVER = None
TORRENT_CACHE_FOLDER = None
