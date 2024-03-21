from gevent import monkey

monkey.patch_all()

from gevent.server import DatagramServer
import gevent
from hashlib import sha1
from random import randint
from struct import unpack
from socket import inet_ntoa
from gevent import sleep
from collections import deque
from .bencode import bencode, bdecode

BOOTSTRAP_NODES = (
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881)
)
TID_LENGTH = 2
RE_JOIN_DHT_INTERVAL = 3
MONITOR_INTERVAL = 10
TOKEN_LENGTH = 2


def entropy(length):
    return "".join(chr(randint(0, 255)) for _ in xrange(length))


def random_id():
    h = sha1()
    h.update(entropy(20))
    return h.digest()


def decode_nodes(nodes):
    n = []
    length = len(nodes)
    if (length % 26) != 0:
        return n

    for i in range(0, length, 26):
        nid = nodes[i:i + 20]
        ip = inet_ntoa(nodes[i + 20:i + 24])
        port = unpack("!H", nodes[i + 24:i + 26])[0]
        n.append((nid, ip, port))

    return n


def get_neighbor(target, nid, end=10):
    return target[:end] + nid[end:]


class KNode(object):

    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port


class DHTServer(DatagramServer):
    def __init__(self, max_node_qsize, bind_ip):
        s = ':' + str(bind_ip)
        self.bind_ip = bind_ip
        DatagramServer.__init__(self, s)

        self.process_request_actions = {
            "get_peers": self.on_get_peers_request,
            "announce_peer": self.on_announce_peer_request,
        }
        self.max_node_qsize = max_node_qsize
        self.nid = random_id()
        self.nodes = deque(maxlen=max_node_qsize)

    def handle(self, data, address):  #
        try:
            msg = bdecode(data)
            self.on_message(msg, address)
        except Exception:
            pass

    def monitor(self):
        while True:
            # print 'len: ', len(self.nodes)
            sleep(MONITOR_INTERVAL)

    def send_krpc(self, msg, address):
        try:
            self.socket.sendto(bencode(msg), address)
        except Exception:
            pass

    def send_find_node(self, address, nid=None):
        nid = get_neighbor(nid, self.nid) if nid else self.nid
        tid = entropy(TID_LENGTH)
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {
                "id": nid,
                "target": random_id()
            }
        }
        self.send_krpc(msg, address)

    def join_DHT(self):
        for address in BOOTSTRAP_NODES:
            self.send_find_node(address)

    def re_join_DHT(self):

        while True:
            if len(self.nodes) == 0:
                self.join_DHT()
            sleep(RE_JOIN_DHT_INTERVAL)

    def auto_send_find_node(self):

        wait = 1.0 / self.max_node_qsize / 5.0
        while True:
            try:
                node = self.nodes.popleft()
                self.send_find_node((node.ip, node.port), node.nid)
            except IndexError:
                pass
            sleep(wait)

    def process_find_node_response(self, msg, address):
        # print 'find node' + str(msg)
        nodes = decode_nodes(msg["r"]["nodes"])
        for node in nodes:
            (nid, ip, port) = node
            if len(nid) != 20: continue
            if ip == self.bind_ip: continue
            if port < 1 or port > 65535: continue
            n = KNode(nid, ip, port)
            self.nodes.append(n)

    def on_message(self, msg, address):
        try:
            if msg["y"] == "r":
                if msg["r"].has_key("nodes"):
                    self.process_find_node_response(msg, address)
            elif msg["y"] == "q":
                try:
                    self.process_request_actions[msg["q"]](msg, address)
                except KeyError:
                    self.play_dead(msg, address)
        except KeyError:
            pass

    def on_get_peers_request(self, msg, address):
        try:
            infohash = msg["a"]["info_hash"]
            tid = msg["t"]
            nid = msg["a"]["id"]
            token = infohash[:TOKEN_LENGTH]
            info = infohash.encode("hex").upper() + '|' + address[0]
            print
            info + "\n",
            msg = {
                "t": tid,
                "y": "r",
                "r": {
                    "id": get_neighbor(infohash, self.nid),
                    "nodes": "",
                    "token": token
                }
            }
            self.send_krpc(msg, address)
        except KeyError:
            pass

    def on_announce_peer_request(self, msg, address):
        try:
            # print 'announce peer'
            infohash = msg["a"]["info_hash"]
            token = msg["a"]["token"]
            nid = msg["a"]["id"]
            tid = msg["t"]

            if infohash[:TOKEN_LENGTH] == token:
                if msg["a"].has_key("implied_port") and msg["a"]["implied_port"] != 0:
                    port = address[1]
                else:
                    port = msg["a"]["port"]
                    if port < 1 or port > 65535: return
                info = infohash.encode("hex").upper()
                print
                info + "\n",
        except Exception as e:
            print
            e
            pass
        finally:
            self.ok(msg, address)

    def play_dead(self, msg, address):
        try:
            tid = msg["t"]
            msg = {
                "t": tid,
                "y": "e",
                "e": [202, "Server Error"]
            }
            self.send_krpc(msg, address)
        except KeyError:
            print
            'error'
            pass

    def ok(self, msg, address):
        try:
            tid = msg["t"]
            nid = msg["a"]["id"]
            msg = {
                "t": tid,
                "y": "r",
                "r": {
                    "id": get_neighbor(nid, self.nid)
                }
            }
            self.send_krpc(msg, address)
        except KeyError:
            pass


if __name__ == '__main__':
    sniffer = DHTServer(50, 8080)
    gevent.spawn(sniffer.auto_send_find_node)
    gevent.spawn(sniffer.re_join_DHT)
    gevent.spawn(sniffer.monitor)

    print('Receiving datagrams on :6882')
    sniffer.serve_forever()
