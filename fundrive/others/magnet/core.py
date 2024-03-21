import asyncio
from itertools import chain
from urllib.parse import urlparse

from notetool.tool.log import log
from .dht.bencode import bdecode
from .dht.torrent import Magnet, Torrent
from .peer import fetch_from_peer
from .peer_tracker import retrieve_peers_http_tracker
from .peer_tracker import retrieve_peers_udp_tracker
from .settings import DEFAULT_TRACKERS

logger = log(__name__)


class Magnet2Torrent:
    def __init__(self, use_trackers=True, use_additional_trackers=False, dht_server=None, torrent_cache_folder=None, ):
        self.use_trackers = use_trackers
        self.use_additional_trackers = use_additional_trackers
        self.dht_server = dht_server
        self.torrent_cache_folder = torrent_cache_folder

    def update_torrent(self, torrent: Torrent, trackers=None) -> Torrent:
        torrent_data = torrent.data
        if self.use_trackers:

            if self.use_additional_trackers:
                trackers += DEFAULT_TRACKERS

            torrent_data[b"announce-list"] = [[tracker.encode("utf-8")] for tracker in trackers]
            if torrent_data[b"announce-list"]:
                torrent_data[b"announce"] = torrent_data[b"announce-list"][0][0]

        return torrent.update_date(torrent_data)

    async def retrieve_torrent(self, magnet_link):
        magnet = Magnet(magnet_link)
        torrent = Torrent(magnet, cache_folder=self.torrent_cache_folder)

        torrent.read_cache()
        if torrent.not_empty():
            self.update_torrent(torrent)
            return torrent

        task_registry = set()
        infohash = magnet.infohash
        tasks = []
        if self.use_trackers:
            trackers = magnet.trackers
            if self.use_additional_trackers:
                trackers += DEFAULT_TRACKERS

            for tracker in trackers:
                try:
                    logger.debug("Trying to fetch peers from {}".format(tracker))
                    tracker_url = urlparse(tracker)
                    if tracker_url.scheme in ["http", "https"]:
                        task = retrieve_peers_http_tracker(task_registry, tracker, infohash)
                    elif tracker_url.scheme in ["udp"]:
                        host, port = tracker_url.netloc.split(":")
                        task = retrieve_peers_udp_tracker(task_registry, host, port, tracker, infohash)
                    else:
                        logger.warn("Unknown scheme, {} {}".format(tracker_url.scheme, tracker_url))
                        continue

                    task = asyncio.ensure_future(task)
                    task.task_type = "tracker"
                    tasks.append(task)
                except Exception as e:
                    logger.error("error {} {}".format(tracker, e))

        if self.dht_server:
            task = asyncio.ensure_future(self.dht_server.find_peers(task_registry, infohash))
            task.task_type = "tracker"
            tasks.append(task)

        handled_peers = set()
        while tasks:
            done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                result = task.result()
                if task.task_type == "tracker":
                    for peer in result[1]["peers"]:
                        if peer in handled_peers:
                            continue
                        handled_peers.add(peer)
                        peer_ip, peer_port = peer
                        logger.debug("Connecting to {}:{}".format(peer_ip, peer_port))
                        peer_task = asyncio.ensure_future(fetch_from_peer(task_registry, peer_ip, peer_port, infohash))
                        peer_task.task_type = "peer"
                        tasks.add(peer_task)
                    if len(result) > 2:
                        new_task = asyncio.ensure_future(result[2]())
                        new_task.task_type = task.task_type
                        tasks.add(new_task)
                elif task.task_type == "peer":
                    if result:
                        for task1 in chain(task_registry, tasks):
                            if not task1.done():
                                task1.cancel()

                        torrent.from_data({b"info": bdecode(result)}, decode=False)
                        self.update_torrent(torrent, trackers=magnet.trackers)
                        torrent.save_cache()
                        return torrent

        raise Exception('FailedToFetchException')

    def get_magnet_info(self, magnet_link: str):

        try:
            # torrent = asyncio.run(self.retrieve_torrent(magnet_link))
            # torrent = asyncio.run_coroutine_threadsafe(self.retrieve_torrent(magnet_link))
            torrent = asyncio.get_event_loop().run_until_complete(self.retrieve_torrent(magnet_link))
            return torrent
        except Exception as e:
            logger.error("Failed {}".format(e))
            return None
