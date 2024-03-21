import asyncio
import struct
from ipaddress import IPv4Address

from notetool.tool.log import log
from .node import Node, NodeHeap
from .protocol import KRPCProtocol

logger = log(__name__)


class SpiderCrawl:
    """
    Crawl the network and look for given 160-bit keys.
    """

    def __init__(self, protocol: KRPCProtocol, node: Node, peers, ksize=8, alpha=100):
        """
        Create a new C{SpiderCrawl}er.

        Args:
            protocol: A :class:`KRPCProtocol` instance.
            node: A :class:`Node` representing the key we're looking for
            peers: A list of :class:`Node` instances that provide the entry point for the network
            ksize: The value for k based on the paper
            alpha: The value for alpha based on the paper
        """
        self.protocol = protocol
        self.ksize = ksize
        self.alpha = alpha
        self.node = node
        self.nearest = NodeHeap(self.node, self.ksize)
        self.last_ids_crawled = []
        self.cancel_crawl = False
        self.crawl_finished = False
        logger.info("creating spider with peers: %s", peers)
        self.nearest.push(peers)

    async def _find(self, rpcmethod):
        logger.info("crawling network with nearest: %s", str(tuple(self.nearest)))

        tasks = set()
        task_mapping = {}
        while not self.cancel_crawl and (not self.nearest.have_contacted_all() or tasks):
            count = self.alpha - len(tasks)
            for peer in self.nearest.get_uncontacted()[:count]:
                self.nearest.mark_contacted(peer)
                task = asyncio.ensure_future(rpcmethod(peer, self.node))
                task_mapping[task] = peer.id
                tasks.add(task)

            done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            done_mapping = {}
            for task in done:
                done_mapping[task_mapping.pop(task)] = task.result()
            await self._nodes_found(done_mapping)

        self.crawl_finished = True

        for task in tasks:
            task.cancel()

        return await self._return_value()

    async def _return_value(self):
        raise NotImplementedError

    async def _nodes_found(self, responses):
        raise NotImplementedError


class PeerSpiderCrawl(SpiderCrawl):
    def __init__(self, protocol, node, peers, ksize, alpha, queue):
        SpiderCrawl.__init__(self, protocol, node, peers, ksize, alpha)
        self._queue = queue

    async def find(self):
        """
        Find either the closest nodes or the value requested.
        """
        return await self._find(self.protocol.call_get_peers)

    async def _nodes_found(self, responses):
        """
        Handle the result of an iteration in _find.
        """
        if self.cancel_crawl:
            return

        toremove = []
        for peerid, response in responses.items():
            response = RPCFindResponse(response)
            if not response.happened():
                toremove.append(peerid)
            elif response.has_value():
                await self._queue.put(response.get_values())
            else:
                self.nearest.push(response.get_node_list())
        self.nearest.remove(toremove)

    async def _return_value(self):
        await self._queue.put([])
        return


class NodeSpiderCrawl(SpiderCrawl):
    async def find(self):
        """
        Find the closest nodes.
        """
        return await self._find(self.protocol.call_find_node)

    async def _nodes_found(self, responses):
        """
        Handle the result of an iteration in _find.
        """
        toremove = []
        for peerid, response in responses.items():
            response = RPCFindResponse(response)
            if not response.happened():
                toremove.append(peerid)
            else:
                self.nearest.push(response.get_node_list())
        self.nearest.remove(toremove)

    async def _return_value(self):
        return list(self.nearest)


class RPCFindResponse:
    def __init__(self, response):
        """
        A wrapper for the result of a RPC find.
        """
        self.response = response

    def happened(self):
        """
        Did the other host actually respond?
        """
        return self.response[0]

    def has_value(self):
        return b"values" in self.response[1]

    def get_values(self):
        peers = []
        for value in self.response[1].get(b"values", []):
            peer_ip, peer_port = struct.unpack("!IH", value)
            peers.append((IPv4Address(peer_ip), peer_port))
        return peers

    def get_node_list(self):
        """
        Get the node list in the response.  If there's no value, this should
        be set.
        """
        response = self.response[1].get(b"nodes")
        nodelist = []
        while response and len(response) >= 26:
            peer_id = response[:20]
            peer_ip, peer_port = struct.unpack("!IH", response[20:26])
            node = Node(peer_id, str(IPv4Address(peer_ip)), peer_port)
            nodelist.append(node)
            response = response[26:]
        return nodelist
