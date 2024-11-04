import asyncio
import ipaddress
import logging
import os
from pathlib import Path

from aiohttp import web

from fundrive.magnet import settings
from fundrive.magnet.core import Magnet2Torrent
from fundrive.magnet.dht.network import Server as DHTServer
from fundrive.magnet.server import routes
from fundrive.magnet.utils import FailedToFetchException


def start_serve(dht_server, torrent_cache_folder=None, debug=False, apikey=None, ip=ipaddress.IPv4Address("0.0.0.0"),
                port=18667, ):
    if not debug:
        stdio_handler = logging.StreamHandler()
        stdio_handler.setLevel(logging.INFO)
        logger = logging.getLogger("aiohttp.access")
        logger.addHandler(stdio_handler)

    settings.SERVE_APIKEY = apikey
    settings.DHT_SERVER = dht_server
    settings.TORRENT_CACHE_FOLDER = torrent_cache_folder
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host=str(ip), port=port)


def start_fetch(dht_server, torrent_cache_folder=None, dht_state_file=None, magnet=None, ):
    loop = asyncio.get_event_loop()
    m2t = Magnet2Torrent(dht_server=dht_server, torrent_cache_folder=torrent_cache_folder, use_additional_trackers=True)
    try:
        torrent = loop.run_until_complete(m2t.retrieve_torrent(magnet_link=magnet))
    except FailedToFetchException:
        print("Unable to fetch magnet link")
        quit(1)
    else:
        with open(torrent.name, "wb") as f:
            f.write(torrent.data_encode())

        print("Downloaded magnet link into file: {}".format(torrent.name))

    if dht_server and dht_state_file:
        dht_server.save_state(dht_state_file)


def start(torrent_cache_folder=None, debug=False, use_dht=False, dht_state_file=None, dht_port=settings.DHT_PORT,
          dht_ip=ipaddress.IPv4Address("0.0.0.0"), command='serve', apikey=None, ip=ipaddress.IPv4Address("0.0.0.0"),
          port=18667, magnet=None, ):
    if torrent_cache_folder:
        torrent_cache_folder = Path(torrent_cache_folder)

        if not torrent_cache_folder.exists():
            os.makedirs(torrent_cache_folder)

        if not torrent_cache_folder.is_dir():
            print("Path {} exists but is not a folder".format(torrent_cache_folder))
            quit(1)

    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)-15s:%(levelname)s:%(name)s:%(lineno)d:%(message)s")

    if use_dht:
        print("Bootstrapping DHT server")
        loop = asyncio.get_event_loop()
        dht_server = DHTServer()

        if dht_state_file and os.path.isfile(dht_state_file):
            dht_server = DHTServer.load_state(dht_state_file)
            loop.run_until_complete(dht_server.listen(dht_port, str(dht_ip)))
        else:
            dht_server = DHTServer()
            loop.run_until_complete(dht_server.listen(dht_port, str(dht_ip)))
            loop.run_until_complete(dht_server.bootstrap(settings.DHT_BOOTSTRAP_NODES))

        if dht_state_file:
            dht_server.save_state_regularly(dht_state_file)
        print("Done bootstrapping DHT server")
    else:
        dht_server = None

    if command == "serve":
        start_serve(dht_server, torrent_cache_folder=torrent_cache_folder, debug=debug, apikey=apikey, ip=ip, port=port)
    elif command == "fetch":
        start_fetch(dht_server, torrent_cache_folder=torrent_cache_folder, dht_state_file=dht_state_file, magnet=magnet)
