import asyncio
import pickle
import random

from notetool.tool.log import log
from .crawling import NodeSpiderCrawl, PeerSpiderCrawl
from .node import Node
from .protocol import KRPCProtocol, ForgetfulPeerStorage, ForgetfulTokenStorage
from .utils import digest

logger = log(__name__)
"""
Package for interacting on the network at a high level.
"""


class Server:
    """
    High level view of a node instance.  This is the object that should be
    created to start listening as an active node on the network.
    """

    protocol_class = KRPCProtocol

    def __init__(self, ksize=8, alpha=100, node_id=None, peer_storage=None, token_storage=None, buckets=None, ):
        """
        Create a server instance.  This will start listening on the given port.

        Args:
            ksize (int): The k parameter from the paper
            alpha (int): The alpha parameter from the paper
            node_id: The id for this node on the network.
            peer_storage  : An instance that implements
            token_storage :interface:`~kademlia.storage.IStorage`
        """
        self.ksize = ksize
        self.alpha = alpha
        self.peer_storage = peer_storage or ForgetfulPeerStorage()
        self.token_storage = token_storage or ForgetfulTokenStorage()
        self.node = Node(node_id or digest(random.getrandbits(255)))
        self.buckets = buckets
        self.transport = None
        self.protocol = None
        self.refresh_loop = None
        self.save_state_loop = None

    def stop(self):
        if self.transport is not None:
            self.transport.close()

        if self.refresh_loop:
            self.refresh_loop.cancel()

        if self.save_state_loop:
            self.save_state_loop.cancel()

    def _create_protocol(self):
        return self.protocol_class(self.node, self.peer_storage, self.token_storage, self.ksize, buckets=self.buckets, )

    async def listen(self, port, interface="0.0.0.0"):
        """
        Start listening on the given port.

        Provide interface="::" to accept ipv6 address
        """
        loop = asyncio.get_event_loop()
        listen = loop.create_datagram_endpoint(
            self._create_protocol, local_addr=(interface, port)
        )
        logger.info("Node %i listening on %s:%i", self.node.long_id, interface, port)
        self.transport, self.protocol = await listen
        # finally, schedule refreshing table
        self.refresh_table()

    def refresh_table(self):
        logger.debug("Refreshing routing table")
        asyncio.ensure_future(self._refresh_table())
        loop = asyncio.get_event_loop()
        self.refresh_loop = loop.call_later(900, self.refresh_table)

    async def _refresh_table(self):
        """
        Refresh buckets that haven't had any lookups in the last hour
        (per section 2.3 of the paper).
        """
        results = []
        for node_id in self.protocol.get_refresh_ids():
            node = Node(node_id)
            nearest = self.protocol.router.find_neighbors(node, self.alpha)
            spider = NodeSpiderCrawl(
                self.protocol, node, nearest, self.ksize, self.alpha
            )
            results.append(spider.find())

        # do our crawling
        await asyncio.gather(*results)

    def bootstrappable_neighbors(self):
        """
        Get a :class:`list` of (ip, port) :class:`tuple` pairs suitable for
        use as an argument to the bootstrap method.

        The server should have been bootstrapped
        already - this is just a utility for getting some neighbors and then
        storing them if this server is going down for a while.  When it comes
        back up, the list of nodes can be used to bootstrap.
        """
        neighbors = self.protocol.router.find_neighbors(self.node)
        return [tuple(n)[-2:] for n in neighbors]

    async def bootstrap(self, addrs):
        """
        Bootstrap the server by connecting to other known nodes in the network.

        Args:
            addrs: A `list` of (ip, port) `tuple` pairs.  Note that only IP
                   addresses are acceptable - hostnames will cause an error.
        """
        logger.debug("Attempting to bootstrap node with %i initial contacts", len(addrs))
        cos = list(map(self.bootstrap_node, addrs))
        gathered = await asyncio.gather(*cos)
        nodes = [node for node in gathered if node is not None]
        spider = NodeSpiderCrawl(
            self.protocol, self.node, nodes, self.ksize, self.alpha
        )
        return await spider.find()

    async def bootstrap_node(self, addr):
        result = await self.protocol.ping(addr, {b"id": self.node.id})
        return Node(result[1][b"id"], addr[0], addr[1]) if result[0] else None

    def find_peers(self, task_registry, info_hash):
        logger.info("Looking for peers for %s", info_hash)
        node = Node(info_hash)
        nearest = self.protocol.router.find_neighbors(node, k=self.ksize * 4)
        if not nearest:
            logger.info("There are no known neighbors to get key %s", info_hash)
            future = asyncio.Future()
            future.set_result(("dht://", {"seeders": 0, "leechers": 0, "peers": []}))
            return future

        spider_queue = asyncio.Queue()
        spider = PeerSpiderCrawl(self.protocol, node, nearest, self.ksize * 4, self.alpha, spider_queue)
        asyncio.create_task(spider.find())

        loop = asyncio.get_running_loop()
        cancel_task = loop.create_future()
        task_registry.add(cancel_task)

        result_queue = asyncio.Queue()

        async def found_peers():
            task = None
            while not spider.crawl_finished:
                try:
                    task = asyncio.ensure_future(spider_queue.get())
                    done, pending = await asyncio.wait(
                        {task, cancel_task}, return_when=asyncio.FIRST_COMPLETED
                    )
                    for peers in done:
                        peers = peers.result()
                        await result_queue.put(
                            (
                                "dht://",
                                {"seeders": 0, "leechers": 0, "peers": peers},
                                lambda: result_queue.get(),
                            )
                        )
                except asyncio.CancelledError:
                    spider.cancel_crawl = True
                    if task and not task.done():
                        task.cancel()
                    break

            await result_queue.put(
                ("dht://", {"seeders": 0, "leechers": 0, "peers": []})
            )
            task_registry.remove(cancel_task)

        asyncio.create_task(found_peers())
        return result_queue.get()

    def dumps_state(self):
        return {
            "ksize": self.ksize,
            "alpha": self.alpha,
            "id": self.node.id,
            "buckets": self.protocol.router.buckets,
        }

    @classmethod
    def loads_state(cls, data):
        return cls(data["ksize"], data["alpha"], data["id"], buckets=data["buckets"])

    def save_state(self, fname):
        """
        Save the state of this node (the alpha/ksize/id/immediate neighbors)
        to a cache file with the given fname.
        """
        logger.info("Saving state to %s", fname)
        data = self.dumps_state()
        with open(fname, "wb") as file:
            pickle.dump(data, file)

    @classmethod
    def load_state(cls, fname):
        """
        Load the state of this node (the alpha/ksize/id/immediate neighbors)
        from a cache file with the given fname.
        """
        logger.info("Loading state from %s", fname)
        with open(fname, "rb") as file:
            data = pickle.load(file)
        svr = cls.loads_state(data)
        return svr

    def save_state_regularly(self, fname, frequency=600):
        """
        Save the state of node with a given regularity to the given
        filename.

        Args:
            fname: File name to save retularly to
            frequency: Frequency in seconds that the state should be saved.
                        By default, 10 minutes.
        """
        self.save_state(fname)
        loop = asyncio.get_event_loop()
        self.save_state_loop = loop.call_later(frequency, self.save_state_regularly, fname, frequency)


def check_dht_value_type(value):
    """
    Checks to see if the type of the value is a valid type for
    placing in the dht.
    """
    typeset = [int, float, bool, str, bytes]
    return type(value) in typeset
