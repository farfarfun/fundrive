import asyncio
import logging

from fundrive.magnet.dht.node import Node
from notetool.tool.log import set_default_level

set_default_level(logging.DEBUG)
import random
from fundrive.magnet.dht.network import Server
from fundrive.magnet.dht.protocol import KRPCProtocol
from fundrive.magnet.dht.utils import digest

serve = Server()

protocol = KRPCProtocol(serve.node, serve.peer_storage, serve.token_storage, serve.ksize, buckets=serve.buckets, )

BOOTSTRAP_NODES = (
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881),
    ("router.utorrent.com", 6881),
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.bitcomet.com", 6881),
    ("dht.aelitis.com", 6881),

)


# torrent = asyncio.run(protocol.call_ping(node))


async def sayhi(protocol: KRPCProtocol, address):
    for boot in BOOTSTRAP_NODES:
        node = Node(digest(random.getrandbits(255)), ip=boot[0], port=boot[1])
        result = await protocol.call_ping(node)
        print(result)
        print(result[1] if result[0] else "No response received.")


logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()
loop.set_debug(True)

# Start local UDP server to be able to handle responses
listen = loop.create_datagram_endpoint(KRPCProtocol, local_addr=('127.0.0.1', 4567))
transport, protocol = loop.run_until_complete(listen)

# Call remote UDP server to say hi
# func = sayhi(protocol, ('127.0.0.1', 1234))
func = sayhi(protocol, ('127.0.0.1', 1234))
loop.run_until_complete(func)

print('done')
# try:
#     loop.run_forever()
# except KeyboardInterrupt:
#     pass

transport.close()
loop.close()
