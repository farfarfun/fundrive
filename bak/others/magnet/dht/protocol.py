import asyncio
import hashlib
import os
import random
import struct
from asyncio import DatagramProtocol
from base64 import b64encode
from ipaddress import IPv4Address

from expiringdict import ExpiringDict

from notetool.tool.log import log
from .bencode import BTFailure, bdecode, bencode
from .node import Node
from .routing import RoutingTable
from .utils import digest

"""
Some code taken from
https://github.com/bmuller/rpcudp/blob/master/rpcudp/protocol.py
Has same license as kademlia, see __init__.py

https://www.cnblogs.com/LittleHann/p/6180296.html

DHT网络的其中一种协议实现(Kademlia)
要加入一个DHT网络，需要首先知道这个网络中的任意一个节点。如何获得这个节点？在一些开源的P2P软件中，会提供一些节点地址
****************************************************************************************************************
* 1.ping           用于确定某个节点是否在线。这个请求主要用于辅助路由表的更新
* 2.find_node      用于查找某个节点，以获得其地址信息。
* 3.get_peer       通过资源的infohash获得资源对应的peer列表。
* 4.announce_peer  通知其他节点自己开始下载某个资源,announce_peer中会携带get_peer回应消息里的token。 
****************************************************************************************************************
"""

MIN_ID = 0
MAX_ID = 2 ** 160


class ForgetfulPeerStorage:
    logger = log(__name__)

    def __init__(self, ttl=3600):
        self._ttl = ttl
        self._data = ExpiringDict(max_age_seconds=ttl, max_len=2000)
        self.data = ExpiringDict(max_age_seconds=ttl, max_len=2000)

    def get_peers(self, info_hash):
        if info_hash not in self._data:
            return []
        return self._data[info_hash].keys()

    def insert_peer(self, info_hash, peer):
        self.data[info_hash][peer] = None
        self.data[info_hash] = self.data[info_hash]


class ForgetfulTokenStorage:
    def __init__(self, ttl=600):
        self._data = ExpiringDict(max_age_seconds=ttl, max_len=2000)

    def get_token(self, sender, id, info_hash):
        token = bytes([random.randint(0, 255) for _ in range(16)])
        self._data[token] = (sender[0], id, info_hash)
        return token

    def verify_token(self, sender, id, info_hash, token):
        if self._data.get(token) == (sender[0], id, info_hash):
            del self._data[token]
            return True
        return False


class KRPCProtocol(DatagramProtocol):
    logger = log(__name__)

    def __init__(self,
                 source_node: Node = None,
                 peer_storage: ForgetfulPeerStorage = None,
                 token_storage: ForgetfulTokenStorage = None,
                 ksize: int = 8,
                 wait_timeout=60,
                 buckets=None, ):
        self.router = RoutingTable(self, ksize, source_node, buckets=buckets)
        self.peer_storage = peer_storage or ForgetfulPeerStorage()
        self.token_storage = token_storage or ForgetfulTokenStorage()
        self.source_node = source_node or Node(digest(random.getrandbits(255)))
        self._wait_timeout = wait_timeout
        self._outstanding = {}
        self.transport = None

    def connection_made(self, transport):
        """Called when a connection is made.

        The argument is the transport representing the pipe connection.
        To receive data, wait for data_received() calls.
        When the connection is closed, connection_lost() is called.
        """
        self.transport = transport

    def datagram_received(self, data, addr):
        """Called when some datagram is received."""

        self.logger.debug("received datagram from %s", addr)
        try:
            data = bdecode(data)
        except (BTFailure, ValueError, KeyError):
            self.logger.info("Failed to decode message")
            return

        if not isinstance(data, dict):
            return

        query_type = data.get(b"y")
        transaction_id = data.get(b"t")
        if not transaction_id:
            return

        if query_type == b"q":  # query
            func_name, args = data.get(b"q"), data.get(b"a")
            if func_name and isinstance(args, dict):
                asyncio.ensure_future(self.handle_request(transaction_id, func_name, args, addr))
        elif query_type == b"r":  # response
            args = data.get(b"r")
            if isinstance(args, dict):
                asyncio.ensure_future(self.handle_response(transaction_id, args, addr))
        elif query_type == b"e":  # error
            args = data.get(b"e")
            if isinstance(args, list):
                self.handle_error(transaction_id, args, addr)
            return
        else:
            return

    async def handle_request(self, transaction_id, func_name, args, addr):
        """
        q 表示请求(请求Queries): q类型的消息它包含 2 个附加的关键字 q 和 a
            关键字 q: 是字符串类型，包含了请求的方法名字(get_peers/announce_peer/ping/find_node)
            关键字 a: 一个字典类型包含了请求所附加的参数(info_hash/id..)
        :param transaction_id:
        :param func_name: 对应关键词 q
        :param args:      对应关键词 a
        :param addr:
        :return:
        """
        func = getattr(self, "rpc_{}".format(func_name.decode('utf-8')), None)
        if func is None or not callable(func):
            msg_args = (self.__class__.__name__, func_name)
            self.logger.info("%s has no callable method " "rpc_%s; ignoring request", *msg_args)
            return

        if not asyncio.iscoroutinefunction(func):
            func = asyncio.coroutine(func)
        args = {k.decode("utf-8"): v for (k, v) in args.items()}
        response = await func(addr, **args)
        if response is not None:
            self.logger.debug("sending response %s for msg id %s to %s", response, b64encode(transaction_id), addr, )
            tx_data = bencode({b"y": b"r", b"r": response, })
            self.transport.sendto(tx_data, addr)

    async def handle_response(self, transaction_id, args, addr):
        """
        r 表示回复(回复 Responses): 包含了返回的值。发送回复消息是在正确解析了请求消息的基础上完成的，包含了一个附加的关键字 r。关键字 r 是字典类型
            id: peer节点id号或者下一跳DHT节点
            nodes": ""
            token: token
        :param transaction_id:
        :param args:
        :param addr:
        :return:
        """
        msg_args = (b64encode(transaction_id), addr)
        if transaction_id not in self._outstanding:
            self.logger.info("received unknown message %s " "from %s; ignoring", *msg_args)
            return
        self.logger.debug("received response %s for message " "id %s from %s", args, *msg_args)
        future, timeout = self._outstanding[transaction_id]
        timeout.cancel()
        if not future.cancelled():
            future.set_result((True, args))
        del self._outstanding[transaction_id]

    def handle_error(self, transaction_id, args, addr):
        """
        3) e 表示错误(错误 Errors): 包含一个附加的关键字 e，关键字 e 是列表类型
            3.1) 第一个元素是数字类型，表明了错误码，当一个请求不能解析或出错时，错误包将被发送。下表描述了可能出现的错误码
                201: 一般错误
                202: 服务错误
                203: 协议错误，比如不规范的包，无效的参数，或者错误的 toke
                204: 未知方法
            3.2) 第二个元素是字符串类型，表明了错误信息
        :return:
        """
        pass

    def _timeout(self, transaction_id):
        args = (b64encode(transaction_id), self._wait_timeout)
        self.logger.info("Did not received reply for msg " "id %s within %i seconds", *args)
        future = self._outstanding[transaction_id][0]
        if not future.cancelled():
            future.set_result((False, None))
        del self._outstanding[transaction_id]

    def get_refresh_ids(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.lonely_buckets():
            rid = random.randint(*bucket.range).to_bytes(20, byteorder="big")
            ids.append(rid)
        return ids

    @staticmethod
    def is_valid_node_id(node):
        return MIN_ID < node.long_id < MAX_ID

    def rpc_ping(self, sender, id):
        source = Node(id, sender[0], sender[1])
        if not self.is_valid_node_id(source):
            return
        self.welcome_if_new(source)
        return {b"id": id}

    def rpc_announce_peer(self, sender, id, info_hash, port, token, name=None, implied_port=None, seed=None, ):
        source = Node(id, sender[0], sender[1])
        if not self.is_valid_node_id(source):
            return

        self.welcome_if_new(source)
        if self.token_storage.verify_token(sender[0], id, info_hash, token):
            if implied_port:
                port = sender[1]
            self.logger.debug("got an announce_peer request from %s, storing '%s'", sender, info_hash.hex(), )
            self.peer_storage.insert_peer((sender[0], port))
        else:
            self.logger.debug("Invalid token from %s", sender)
        return {b"id": id}

    def rpc_find_node(self, sender, id, target, want="n4", token=None):
        self.logger.info("finding neighbors of %i in local table", int(id.hex(), 16))
        source = Node(id, sender[0], sender[1])
        if not self.is_valid_node_id(source):
            return

        self.welcome_if_new(source)
        node = Node(target)
        if not self.is_valid_node_id(node):
            return
        neighbors = self.router.find_neighbors(node, exclude=source)
        data = {b"id": id, b"nodes": b"".join([n.packed for n in neighbors])}
        if token:
            data[b"token"] = token
        return data

    def rpc_get_peers(self, sender, id, info_hash, want="n4", noseed=0, scrape=0, bs=None):
        source = Node(id, sender[0], sender[1])
        if not self.is_valid_node_id(source):
            return
        self.welcome_if_new(source)
        peers = self.peer_storage.get_peers(info_hash)
        token = self.token_storage.get_token(sender, id, info_hash)
        if not peers:
            return self.rpc_find_node(sender, id, info_hash, token=token)

        return {
            b"id": id,
            b"token": token,
            b"values": [
                IPv4Address(peer[0]).packed + struct.pack("!H", peer[1])
                for peer in peers
            ],
        }

    async def call_ping(self, node_to_ask):
        """
        ping: 检测节点是否可达，请求包含一个参数id，代表该节点的nodeID。对应的回复也应该包含回复者的nodeID
            Query = {"t":"aa", "y":"q", "q":"ping", "a":{"id":"abcdefghij0123456789"}}
            bencoded = d1:ad2:id20:abcdefghij0123456789e1:q4:ping1:t2:aa1:y1:qe

            Response = {"t":"aa", "y":"r", "r": {"id":"mnopqrstuvwxyz123456"}}
            bencoded = d1:rd2:id20:mnopqrstuvwxyz123456e1:t2:aa1:y1:re
        :param node_to_ask:
        :return:
        """
        address = (node_to_ask.ip, node_to_ask.port)
        result = await self.ping(address, {b"id": self.source_node.id})
        return self.handle_call_response(result, node_to_ask)

    async def call_find_node(self, node_to_ask, node_to_find):
        """
        2. find_node: find_node 被用来查找给定 ID 的DHT节点的联系信息，该请求包含两个参数id(代表该节点的nodeID)和target。回复中应该包含被请求节点的路由表中距离target最接近的K个nodeID以及对应的nodeINFO
            # "id" containing the node ID of the querying node, and "target" containing the ID of the node sought by the queryer.
            Query = {"t":"aa", "y":"q", "q":"find_node", "a": {"id":"abcdefghij0123456789", "target":"mnopqrstuvwxyz123456"}}
            bencoded = d1:ad2:id20:abcdefghij01234567896:target20:mnopqrstuvwxyz123456e1:q9:find_node1:t2:aa1:y1:qe

            Response = {"t":"aa", "y":"r", "r": {"id":"0123456789abcdefghij", "nodes": "def456..."}}
            bencoded = d1:rd2:id20:0123456789abcdefghij5:nodes9:def456...e1:t2:aa1:y1:re
        :param node_to_ask:
        :param node_to_find:
        :return:
        """
        address = (node_to_ask.ip, node_to_ask.port)
        result = await self.find_node(address, {b"id": self.source_node.id, b"target": node_to_find.id})
        return self.handle_call_response(result, node_to_ask)

    async def call_get_peers(self, node_to_ask: Node, node_to_find):
        """
        get_peers 请求包含 2 个参数
            1) id请求节点ID，
            2) info_hash代表torrent文件的infohash，infohash为种子文件的SHA1哈希值，也就是磁力链接的btih值
        2. response get_peer:
            1) 如果被请求的节点有对应 info_hash 的 peers，他将返回一个关键字 values，这是一个列表类型的字符串。
               每一个字符串包含了 "CompactIP-address/portinfo" 格式的 peers 信息(即对应的机器ip/port信息)(peer的info信息和DHT节点的info信息是一样的)
            2) 如果被请求的节点没有这个 infohash 的 peers，那么他将返回关键字 nodes
                (需要注意的是，如果该节点没有对应的infohash信息，而只是返回了nodes，则请求方会认为该节点是一个"可疑节点"，则会从自己的路由表K捅中删除该节点)，
               这个关键字包含了被请求节点的路由表中离 info_hash 最近的 K 个节点(我这里没有该节点，去别的节点试试运气)，使用 "Compactnodeinfo" 格式回复。
            在这两种情况下，关键字 token 都将被返回。token 关键字在今后的 annouce_peer 请求中必须要携带。token 是一个短的二进制字符串。

        get_peers Query = {"t":"aa", "y":"q", "q":"get_peers", "a": {"id":"abcdefghij0123456789", "info_hash":"mnopqrstuvwxyz123456"}}
        bencoded = d1:ad2:id20:abcdefghij01234567899:info_hash20:mnopqrstuvwxyz123456e1:q9:get_peers1:t2:aa1:y1:qe

        Response with peers = {"t":"aa", "y":"r", "r": {"id":"abcdefghij0123456789", "token":"aoeusnth", "values": ["axje.u", "idhtnm"]}}
        bencoded = d1:rd2:id20:abcdefghij01234567895:token8:aoeusnth6:valuesl6:axje.u6:idhtnmee1:t2:aa1:y1:re

        Response with closest nodes = {"t":"aa", "y":"r", "r": {"id":"abcdefghij0123456789", "token":"aoeusnth", "nodes": "def456..."}}
        bencoded = d1:rd2:id20:abcdefghij01234567895:nodes9:def456...5:token8:aoeusnthe1:t2:aa1:y1:re
        :param node_to_ask:
        :param node_to_find:
        :return:
        """
        address = (node_to_ask.ip, node_to_ask.port)
        result = await self.get_peers(address, {b"id": self.source_node.id, b"info_hash": node_to_find.id})
        return self.handle_call_response(result, node_to_ask)

    async def call_announce_peer(self, node_to_ask, key, value):  # TODO
        """
        announce_peer: 这个请求用来表明发出 announce_peer 请求的节点，正在某个端口下载 torrent 文件
        announce_peer 包含 4 个参数
            1) 第一个参数是 id: 包含了请求节点的 ID
            2) 第二个参数是 info_hash: 包含了 torrent 文件的 infohash
            3) 第三个参数是 port: 包含了整型的端口号，表明 peer 在哪个端口下载
            4) 第四个参数数是 token: 这是在之前的 get_peers 请求中收到的回复中包含的。
        收到 announce_peer 请求的节点必须检查这个 token 与之前我们回复给这个节点 get_peers 的 token 是否相同
        (也就说，所有下载者/发布者都要参与检测新加入的发布者是否伪造了该资源，但是这个机制有一个问题，如果最开始的那个发布者就伪造，则整条链路都是一个伪造的错的资源infohash信息了)
        如果相同，那么被请求的节点将记录发送 announce_peer 节点的 IP 和请求中包含的 port 端口号在 peer 联系信息中对应的 infohash 下，
        这意味着一个一个事实: 当前这个资源有一个新的peer提供者了，下一次有其他节点希望或者这个资源的时候，会把这个新的(前一次请求下载资源的节点)也当作一个peer返回给请求者，
        这样，资源的提供者就越来越多，资源共享速度就越来越快。
        一个peer正在下载某个资源，意味着该peer有能够访问到该资源的渠道，且该peer本地是有这份资源的全部或部分拷贝的，它需要向DHT网络广播announce消息，告诉其他节点这个资源的下载地址


        announce_peers Query = {"t":"aa", "y":"q", "q":"announce_peer", "a": {"id":"abcdefghij0123456789", "implied_port": 1, "info_hash":"mnopqrstuvwxyz123456", "port": 6881, "token": "aoeusnth"}}
        bencoded = d1:ad2:id20:abcdefghij01234567899:info_hash20:mnopqrstuvwxyz1234564:porti6881e5:token8:aoeusnthe1:q13:announce_peer1:t2:aa1:y1:qe

        Response = {"t":"aa", "y":"r", "r": {"id":"mnopqrstuvwxyz123456"}}
        bencoded = d1:rd2:id20:mnopqrstuvwxyz123456e1:t2:aa1:y1:re

        :param node_to_ask:
        :param key:
        :param value:
        :return:
        """
        address = (node_to_ask.ip, node_to_ask.port)
        result = await self.store(address, self.source_node.id, key, value)
        return self.handle_call_response(result, node_to_ask)

    def welcome_if_new(self, node):
        """
        Given a new node, send it all the keys/values it should be storing,
        then add it to the routing table.

        @param node: A new node that just joined (or that we just found out
        about).

        Process:
        For each key in storage, get k closest nodes.  If newnode is closer
        than the furtherst in that list, and the node for this server
        is closer than the closest in that list, then store the key/value
        on the new node (per section 2.5 of the paper)
        """
        if not self.router.is_new_node(node):
            return

        self.logger.info("never seen %s before, adding to router", node)
        self.router.add_contact(node)

    def handle_call_response(self, result, node):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if not result[0]:
            self.logger.info("no response from %s, removing from router", node)
            self.router.remove_contact(node)
            return result

        self.logger.info("got successful response from %s", node)
        self.welcome_if_new(node)
        return result

    @staticmethod
    def generate_token():
        return bytes([random.randint(0, 255) for _ in range(16)])

    def __getattr__(self, name):
        """
        If name begins with "_" or "rpc_", returns the value of
        the attribute in question as normal.
        Otherwise, returns the value as normal *if* the attribute
        exists, but does *not* raise AttributeError if it doesn't.
        Instead, returns a closure, func, which takes an argument
        "address" and additional arbitrary args (but not kwargs).
        func attempts to call a remote method "rpc_{name}",
        passing those args, on a node reachable at address.
        """
        if name.startswith("_") or name.startswith("rpc_"):
            return getattr(super(), name)

        try:
            return getattr(super(), name)
        except AttributeError:
            pass

        def func(address, args):
            transaction_id = hashlib.sha1(os.urandom(32)).digest()
            txdata = bencode({b"y": b"q", b"t": transaction_id, b"a": args, b"q": name.encode("utf-8"), })
            self.logger.debug("calling remote function %s on %s (msgid %s)", name, address, b64encode(transaction_id), )
            self.transport.sendto(txdata, address)

            loop = asyncio.get_event_loop()
            if hasattr(loop, "create_future"):
                future = loop.create_future()
            else:
                future = asyncio.Future()
            timeout = loop.call_later(self._wait_timeout, self._timeout, transaction_id)
            self._outstanding[transaction_id] = (future, timeout)
            return future

        return func
