import argparse
import asyncio
import ipaddress
import logging
import os
from pathlib import Path

from aiohttp import web

from . import settings
from .core import Magnet2Torrent
from .dht.network import Server as DHTServer
from .server import routes
from .utils import FailedToFetchException


def main():
    parser = argparse.ArgumentParser(description="Turn a magnet link to torrent.")
    parser.add_argument("--debug", help="Enable debug", action="store_true")
    parser.add_argument("--use-dht", help="Enable DHT", action="store_true", dest="use_dht")
    parser.add_argument("--dht-state-file", help="Where to save DHT info", dest="dht_state_file", type=str, )
    parser.add_argument("--dht-port", help="Port to listen for DHT on", dest="dht_port", type=int,
                        default=settings.DHT_PORT, )
    parser.add_argument("--dht-ip", help="Host to listen for DHT on", dest="dht_ip", type=ipaddress.ip_address,
                        default=ipaddress.IPv4Address("0.0.0.0"), )
    parser.add_argument("--torrent-cache-folder", help="Folder to cache torrent metadata into",
                        dest="torrent_cache_folder", type=str, )
    subparsers = parser.add_subparsers(help="sub-command help", dest="command")

    # dht_test_subparser = subparsers.add_parser("dhttest")

    serve_subparser = subparsers.add_parser(
        "serve", help="Run an HTTP server that serves torrents via an API or directly")
    serve_subparser.add_argument("--ip", type=ipaddress.ip_address, default=ipaddress.IPv4Address("0.0.0.0"),
                                 help="Host to listen on", )
    serve_subparser.add_argument("--port", type=int, default=18667, help="Port to listen on")
    serve_subparser.add_argument("--apikey", type=str, default=None,
                                 help="Protect the endpoint with a simple apikey, add apikey=<apikey> to the url to access", )

    fetch_subparser = subparsers.add_parser("fetch", help="Fetch a torrent and save it locally")
    fetch_subparser.add_argument("magnet", help="Magnet link")

    args = parser.parse_args()

    if args.torrent_cache_folder:
        torrent_cache_folder = Path(args.torrent_cache_folder)

        if not torrent_cache_folder.exists():
            os.makedirs(args.torrent_cache_folder)

        if not torrent_cache_folder.is_dir():
            print("Path {} exists but is not a folder".format(args.torrent_cache_folder))
            quit(1)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)-15s:%(levelname)s:%(name)s:%(lineno)d:%(message)s")

    if args.use_dht:
        print("Bootstrapping DHT server")
        loop = asyncio.get_event_loop()
        dht_server = DHTServer()

        if args.dht_state_file and os.path.isfile(args.dht_state_file):
            dht_server = DHTServer.load_state(args.dht_state_file)
            loop.run_until_complete(dht_server.listen(args.dht_port, str(args.dht_ip)))
        else:
            dht_server = DHTServer()
            loop.run_until_complete(dht_server.listen(args.dht_port, str(args.dht_ip)))
            loop.run_until_complete(dht_server.bootstrap(settings.DHT_BOOTSTRAP_NODES))

        if args.dht_state_file:
            dht_server.save_state_regularly(args.dht_state_file)
        print("Done bootstrapping DHT server")
    else:
        dht_server = None

    if args.command == "serve":
        if not args.debug:
            stdio_handler = logging.StreamHandler()
            stdio_handler.setLevel(logging.INFO)
            logger = logging.getLogger("aiohttp.access")
            logger.setLevel(logging.INFO)
            logger.addHandler(stdio_handler)

        settings.SERVE_APIKEY = args.apikey
        settings.DHT_SERVER = dht_server
        settings.TORRENT_CACHE_FOLDER = args.torrent_cache_folder
        app = web.Application()
        app.add_routes(routes)
        web.run_app(app, host=str(args.ip), port=args.port)
    elif args.command == "fetch":
        loop = asyncio.get_event_loop()
        m2t = Magnet2Torrent(args.magnet, dht_server=dht_server, torrent_cache_folder=args.torrent_cache_folder, )
        try:
            torrent = loop.run_until_complete(m2t.retrieve_torrent())
        except FailedToFetchException:
            print("Unable to fetch magnet link")
            quit(1)
        else:
            with open(torrent.name, "wb") as f:
                f.write(torrent.data_encode())

            print("Downloaded magnet link into file: {}".format(torrent.name))

        if dht_server and args.dht_state_file:
            dht_server.save_state(args.dht_state_file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
