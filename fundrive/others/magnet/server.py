import base64
from urllib.parse import quote

from aiohttp import web

from . import settings
from .core import Magnet2Torrent
from .utils import FailedToFetchException

routes = web.RouteTableDef()


@routes.get("/")
async def get_torrent(request):
    if settings.SERVE_APIKEY and request.query.getone("apikey", None) != settings.SERVE_APIKEY:
        raise web.HTTPUnauthorized()

    try:
        magnet = request.query["magnet"]
    except:
        return web.json_response({"status": "error", "message": "magnet argument missing from url"}, status=400, )

    m2t = Magnet2Torrent(magnet, dht_server=settings.DHT_SERVER, torrent_cache_folder=settings.TORRENT_CACHE_FOLDER, )
    try:
        torrent = await m2t.retrieve_torrent()
    except FailedToFetchException:
        return web.json_response({"status": "error", "message": "failed to retrieve magnet link"}, status=500)

    if request.query.getone("direct", None) is not None:
        return web.Response(body=torrent.data_encode(),
                            headers={"Content-Disposition": "attachment; filename*=UTF-8''{}".format(
                                quote(torrent.name))},
                            )
    else:
        return web.json_response(
            {"status": "success", "filename": torrent.name,
             "torrent_data": base64.b64encode(torrent.data_encode()).decode("utf-8")}
        )
