# encoding: utf-8

import socket
from collections import deque
from hashlib import sha1
from random import randint
from socket import inet_ntoa
from struct import unpack
from threading import Timer, Thread, Lock
from time import sleep

from fundrive.magnet.dht.bencode import bencode, bdecode

# 一些公共节点地址，用来本地爬虫加入dht网络
BOOTSTRAP_NODES = {
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881)
}

# 一些全局变量
TID_LENGTH = 2
RE_JOIN_DHT_INTERVAL = 3
TOKEN_LENGTH = 2


# 用来生成随机字串
def entropy(length):
    return "".join(chr(randint(0, 255)) for _ in range(length))


# 根据随机字串生成nid，这样的话，自然很可能和其他的节点ID重复
def random_id():
    h = sha1()
    # h.update(entropy(20))
    return h.digest()


# 解析node，node长度为26，其中20位为nid，4位为ip，2位为port
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


# 定时器函数
def timer(t, f):
    Timer(t, f).start()


# 获取“邻居”nid
def get_neighbor(target, end=10):
    return target[:end] + random_id()[end:]


# 一个node的结构
class KNode():
    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port


# DHT类，继承自Thread类
class DHT(Thread):
    def __init__(self, master, port):
        Thread.__init__(self)

        # 用来输出和保存种子hash的对象
        self.master = master

        # 创建队列，相当于路由表的简单模拟
        # 根据原作者的注释来看，队列的最大长度越大，速度越快，耗费带宽越大
        self.nodes = deque(maxlen=2000)

        # 生成的自身的网络节点
        self.nid = random_id()

        # 创建socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.bind(("0.0.0.0", port))

        # 处理"get_peers"和"announce_peer"请求的函数
        self.process_request_actions = {
            "get_peers": self.on_get_peers_request,
            "announce_peer": self.on_announce_peer_request,
        }

    # 发包函数，发送的数据需要使用bencode编码
    def send_krpc(self, msg, address):
        try:
            self.socket.sendto(bencode(msg), address)
        except:
            pass

    # find node 方法，用来查找对应的node
    def find_nodes(self, address, nid=None):
        if not nid:
            nid = self.nid
        # 扩大寻找node的范围
        nid = get_neighbor(nid)
        tid = entropy(TID_LENGTH)
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {"id": nid, "target": random_id()}
        }

        self.send_krpc(msg, address)

    # 加入dht网络
    def joinDHT(self):
        for address in BOOTSTRAP_NODES:
            self.find_nodes(address)

    # 重新加入dht网络
    def re_join_DHT(self):
        if len(self.nodes) == 0:
            self.joinDHT()
        timer(RE_JOIN_DHT_INTERVAL, self.re_join_DHT)

    # 重写run方法
    def run(self):
        self.re_join_DHT()
        while 1:
            try:
                # 接收数据并解码
                (data, address) = self.socket.recvfrom(65536)
                msg = bdecode(data)
                self.on_message(msg, address)
            except:
                pass

    # 处理find node方法的请求
    def process_find_node_response(self, msg, address):
        # 将node解码
        nodes = decode_nodes(msg["r"]["nodes"])
        for node in nodes:
            (nid, ip, port) = node
            if len(nid) != 20:
                continue
            if ip == "0.0.0.0":
                continue
            n = KNode(nid, ip, port)
            # 添加到node队列里
            self.nodes.append(n)

    # 发送get peers 的请求，在msg参数中包含种子hash的信息
    def on_get_peers_request(self, msg, address):
        try:
            # 获取hash值
            infohash = msg["a"]["info_hash"]
            # 输出并保存
            self.master.log(infohash, "get_peers")
            tid = msg["t"]
            nid = msg["a"]["id"]
            token = infohash[:TOKEN_LENGTH]
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
        except:
            pass

    # 发送announce peer的请求，同样在msg参数中包含种子hash信息
    def on_announce_peer_request(self, msg, address):
        try:
            infohash = msg['a']['info_hash']
            self.master.log(infohash, "announce")
        except:
            print("error in on_announce_peer_request")

        finally:
            self.ok(msg, address)

    # 对announce peer请求的响应
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
        except:
            print("error in ok")

    # 处理接收到的消息
    def on_message(self, msg, address):
        try:
            # 处理response消息
            if msg["y"] == "r":
                if msg["r"].has_key("nodes"):
                    self.process_find_node_response(msg, address)
            # 处理request消息
            elif msg["y"] == "q":
                try:
                    self.process_request_actions[msg["q"]](msg, address)
                except:
                    self.play_dead(msg, address)
        except:
            print
            "error in on_message"

    # 发送错误消息
    def play_dead(self, msg, address):
        try:
            tid = msg["t"]
            msg = {
                "t": tid,
                "y": "e",
                "e": [202, "Server Error"]
            }
            self.send_krpc(msg, address)
        except:
            pass

    # 对队列里的node继续发送find node请求，获取更多的node
    def auto_send_find_node(self):
        wait = 1.0 / 2000
        while 1:
            try:
                node = self.nodes.popleft()
                self.find_nodes((node.ip, node.port), node.nid)
            except:
                pass
            sleep(wait)


# 用来输出及保存种子hash
class Master():
    def __init__(self):
        self.mutex = Lock()

    def log(self, infohash, source):
        global inum
        infohash = infohash.encode("hex")
        inum += 1
        print(inum, infohash, source)

        file = open("hash.log", "a")
        file.write(str(infohash) + "n")
        file.close()


inum = 0
t1 = DHT(Master(), 8006)
t1.start()
t1.auto_send_find_node()
