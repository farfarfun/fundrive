import base64
import getpass
import http.client
import itertools
import json
import logging
import math
import os
import ssl
import string
import subprocess
import sys
import time
import urllib
import urllib.parse
import urllib.request

# -------------------------------- Constants --------------------------------- #

DEFAULT_PORT = 6800
SERVER_URI_FORMAT = '{}://{}:{:d}/jsonrpc'

# Status values for unfinished downloads.
TEMPORARY_STATUS = ('active', 'waiting', 'paused')
# Status values for finished downloads.
FINAL_STATUS = ('complete', 'error')

ARIA2_CONTROL_FILE_EXT = '.aria2'

# Encoding to use when inserting bytes objects into JSON.
JSON_ENCODING = 'utf-8'

# Module logger.
LOGGER = logging.getLogger(name=__name__)


# -------------------------- Convenience Functions --------------------------- #

def to_json_list(objs):
    """
    Wrap strings in lists. Other iterables are converted to lists directly.
    """
    if isinstance(objs, str):
        return [objs]
    if not isinstance(objs, list):
        return list(objs)
    return objs


def add_options_and_position(params, options=None, position=None):
    """
    Convenience method for adding options and position to parameters.
    """
    if options:
        params.append(options)
    if position:
        if not isinstance(position, int):
            try:
                position = int(position)
            except ValueError:
                position = -1
        if position >= 0:
            params.append(position)
    return params


def get_status(response):
    """
    Process a status response.
    """
    if response:
        try:
            return response['status']
        except KeyError:
            LOGGER.error('no status returned from Aria2 RPC server')
            return 'error'
    else:
        LOGGER.error('no response from server')
        return 'error'


def random_token(length, valid_chars=None):
    """
    Get a random secret token for the Aria2 RPC server.

    length:
      The length of the token

    valid_chars:
      A list or other ordered and indexable iterable of valid characters. If not
      given of None, asciinumberic characters with some punctuation characters
      will be used.
    """
    if not valid_chars:
        valid_chars = string.ascii_letters + string.digits + '!@#$%^&*()-_=+'
    number_of_chars = len(valid_chars)
    bytes_to_read = math.ceil(math.log(number_of_chars) / math.log(0x100))
    max_value = 0x100 ** bytes_to_read
    max_index = number_of_chars - 1
    token = ''
    for _ in range(length):
        value = int.from_bytes(os.urandom(bytes_to_read), byteorder='little')
        index = round((value * max_index) / max_value)
        token += valid_chars[index]
    return token


# ---------------- From python3-aur's ThreadedServers.common ----------------- #

def format_bytes(size):
    """
    Convert bytes to a human-friendly units..
    """
    if size < 0x400:
        return '{:d} B'.format(size)
    size = float(size) / 0x400
    for prefix in ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB'):
        if size < 0x400:
            return '{:0.02f} {}'.format(size, prefix)
        size /= 0x400
    return '{:0.02f} YiB'.format(size)


def format_seconds(seconds):
    """
    Convert seconds to hours, minutes and seconds.
    """
    time_str = ''
    for base, char in (
            (60, 's'),
            (60, 'm'),
            (24, 'h')
    ):
        seconds, remainder = divmod(seconds, base)
        if seconds == 0:
            return '{:d}{}{}'.format(remainder, char, time_str)
        if remainder != 0:
            time_str = '{:02d}{}{}'.format(remainder, char, time_str)
    return '{:d}d{}'.format(seconds, string)


# --------------------------------- FakeLock --------------------------------- #

class FakeLock:
    """
    Dummy context manager to be used as a lock placeholder.
    """

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_value, traceback):
        return


# ---------------------------- Aria2JsonRpcError ----------------------------- #

class Aria2JsonRpcError(Exception):
    """
    Base exception raised by this module.
    """

    def __init__(self, msg, connection_error=False):
        super(Aria2JsonRpcError, self).__init__(self, msg)
        self.msg = msg
        self.connection_error = connection_error

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, self.msg)


# ------------------------------ ServerInstance ------------------------------ #

class Aria2RpcServer(object):
    """
    Wrapper to manage starting and stopping an Aria2 RPC server within a context
    manager.
    """

    def __init__(self, cmd, token, port, identity, a2jr_kwargs=None, timeout=10, scheme='http', host='localhost',
                 nice=True, lock=None, quiet=True):
        """
        cmd:
          A list representing the aria2c command to be run along with additional
          arguments, eg.

              ['aria2c', '--rpc-listen-all=false', '--continue']

          or

              ['sudo', 'aria2c', '--rpc-listen-all=false', '--continue']

          This MUST NOT contain any of the following options:

              --enable-rpc
              --rpc-secret
              --rpc-listen-port

          For local use it is recommended to include "--rpc-listen-all=false".

        token:
          The RPC token to pass to aria2c's --rpc-secret option.

        port:
          The RPC listen port to pass to aria2c's --rpc-listen-port option.

        identity:
          The identity to use in the Aria2JsonRpc returned by __enter__.

        args:
          Additional arguments to aria2c. These must not include --rpc-secret or
          --rpc-listen-port.

        a2jr_kwargs:
          Keyword arguments to pass to Aria2JsonRpc.

        timeout:
          The timeout when waiting for the server to shut down.

        nice:
          Default value of "nice" argument to kill() method.

        lock:
          An optional threading/multiprocessing lock object that can be used as a
          context manager to lock the launch method when starting and stopping the
          server.

        quiet:
          If True, suppress output from the RPC server if one is launched.
        """
        self.cmd = cmd
        self.cmd.append('--stop-with-process={:d}'.format(os.getpid()))
        self.token = token
        self.port = port
        self.identity = identity

        if a2jr_kwargs is None:
            a2jr_kwargs = dict()
        a2jr_kwargs['token'] = token
        a2jr_kwargs['setup_function'] = self.launch

        self.a2jr_kwargs = a2jr_kwargs

        self.timeout = timeout
        self.scheme = scheme
        self.host = host

        self.cmd.extend((
            '--enable-rpc',
            '--rpc-secret', token,
            '--rpc-listen-port', str(port)
        ))

        self.process = None
        self.a2jr = None
        self.nice = nice
        if lock is None:
            lock = FakeLock()
        self.lock = lock
        self.quiet = quiet

    def get_a2jr(self, new=False):
        """
        Get an instance of Aria2JsonRpc to interface with the server. This instance
        will have its setup_function attribute set so that it can launch the server
        dynamically before the first request is sent.
        """
        if self.a2jr is None or new:
            uri = SERVER_URI_FORMAT.format(self.scheme, self.host, self.port)
            self.a2jr = Aria2JsonRpc(self.identity, uri, **self.a2jr_kwargs)
        return self.a2jr

    def kill(self, nice=None):
        """
        Stop the Aria2c RPC server launched by this object if there is one.

        nice:
          If True, use the RPC "shutdown" method before trying the "forceShutdown"
          method. This waits up to 3 seconds even if there are no current downloads.
        """
        if self.process is None:
            return True

        with self.lock:
            LOGGER.debug('{}: attempting to stop PID {:d}'.format(
                self.__class__.__name__,
                self.process.pid
            ))

            # Try to kill the server with increasing insistence:
            # * RPC shutdown method
            # * RPC forceShutdown method
            # * SIGTERM
            # * SIGKILL
            a2jr = self.get_a2jr()
            if nice is None:
                nice = self.nice
            if nice:
                methods = (
                    a2jr.shutdown,
                    a2jr.forceShutdown,
                    self.process.terminate,
                    self.process.kill
                )
            else:
                methods = (
                    self.process.terminate,
                    self.process.kill
                )
            for schwarzenegger in methods:
                try:
                    schwarzenegger()
                except Aria2JsonRpcError:
                    pass
                try:
                    exit_code = self.process.wait(self.timeout)
                except subprocess.TimeoutExpired:
                    exit_code = None
                if exit_code is not None:
                    LOGGER.debug('{}: PID {:d} exit code: {:d}'.format(
                        self.__class__.__name__,
                        self.process.pid,
                        exit_code
                    ))
                    self.process = None
                    return True

        LOGGER.error('{}: failed to kill PID {:d}'.format(
            self.__class__.__name__,
            self.process.pid
        ))
        return False

    def launch(self):
        """
        Launch an instance of the server if necessary and return an Aria2JsonRpc
        object to interface with it.
        """
        with self.lock:
            a2jr = self.get_a2jr(new=True)
            a2jr.setup_function = None
            # Check if the server is already running.
            try:
                a2jr.getVersion()
            except Aria2JsonRpcError as err:
                if not err.connection_error:
                    raise err
                launch = True
            else:
                launch = False

            if launch:
                LOGGER.debug(
                    '%s: no response to version request from server: %s',
                    self.__class__.__name__,
                    self.cmd
                )
                self.kill()
                LOGGER.debug(
                    '%s: attempting to launch Aria2 RPC server: %s',
                    self.__class__.__name__,
                    self.cmd
                )
                if self.quiet:
                    self.process = subprocess.Popen(
                        self.cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    self.process = subprocess.Popen(
                        self.cmd,
                        stdout=sys.stderr
                    )
            timeout = time.time() + self.timeout
            # Wait for the server to start listening.
            while True:
                try:
                    self.a2jr.getVersion()
                except Aria2JsonRpcError as err:
                    if err.connection_error:
                        time.sleep(0.25)
                        if time.time() > timeout:
                            break
                    else:
                        raise err
                else:
                    break
        return self.a2jr

    def __enter__(self):
        """
        Same as launch().
        """
        return self.launch()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Invokes kill()
        """
        self.kill()


# ---------------------------- Aria2JsonRpc Class ---------------------------- #

class Aria2JsonRpc(object):
    """
    Interface class for interacting with an Aria2 RPC server.
    """

    # TODO: certificate options, etc.

    def __init__(self, identity, uri,
                 mode='normal',
                 token=None,
                 http_user=None, http_passwd=None,
                 server_cert=None, client_cert=None, client_cert_password=None,
                 ssl_protocol=None,
                 setup_function=None
                 ):
        """
        identity: the identity to send to the RPC interface

        uri: the URI of the RPC interface

        mode:
          normal - process requests immediately
          batch - queue requests (run with "process_queue")
          format - return RPC request objects

        token:
          RPC method-level authorization token (set using `--rpc-secret`)

        http_user, http_password:
          HTTP Basic authentication credentials (deprecated)

        server_cert:
          server certificate for HTTPS connections

        client_cert:
          client certificate for HTTPS connections

        client_cert_password:
          prompt for client certificate password

        ssl_protocol:
          SSL protocol from the ssl module

        setup_function:
          A function to invoke prior to the first server call. This could be the
          launch() method of an Aria2RpcServer instance, for example. This attribute
          is set automatically in instances returned from Aria2RpcServer.get_a2jr()
        """
        self.identity = identity
        self.uri = uri
        self.mode = mode
        self.queue = []
        self.handlers = dict()
        self.token = token
        self.setup_function = setup_function

        if None not in (http_user, http_passwd):
            self.add_HTTPBasicAuthHandler(http_user, http_passwd)

        if server_cert or client_cert:
            self.add_HTTPSHandler(
                server_cert=server_cert,
                client_cert=client_cert,
                client_cert_password=client_cert_password,
                protocol=ssl_protocol
            )

        self.update_opener()

    def iter_handlers(self):
        """
        Iterate over handlers.
        """
        for name in ('HTTPS', 'HTTPBasicAuth'):
            try:
                yield self.handlers[name]
            except KeyError:
                pass

    def update_opener(self):
        """
        Build an opener from the current handlers.
        """
        self.opener = urllib.request.build_opener(*self.iter_handlers())

    def remove_handler(self, name):
        """
        Remove a handler.
        """
        try:
            del self.handlers[name]
        except KeyError:
            pass

    def add_HTTPBasicAuthHandler(self, user, passwd):
        """
        Add a handler for HTTP Basic authentication.

        If either user or passwd are None, the handler is removed.
        """
        handler = urllib.request.HTTPBasicAuthHandler()
        handler.add_password(
            realm='aria2',
            uri=self.uri,
            user=user,
            passwd=passwd,
        )
        self.handlers['HTTPBasicAuth'] = handler

    def remove_HTTPBasicAuthHandler(self):
        """
        Remove the HTTP Basic authentication handler.
        """
        self.remove_handler('HTTPBasicAuth')

    def add_HTTPSHandler(self,
                         server_cert=None,
                         client_cert=None,
                         client_cert_password=None,
                         protocol=None,
                         ):
        """
        Add a handler for HTTPS connections with optional server and client
        certificates.
        """
        if not protocol:
            protocol = ssl.PROTOCOL_TLSv1
        #       protocol = ssl.PROTOCOL_TLSv1_1 # openssl 1.0.1+
        #       protocol = ssl.PROTOCOL_TLSv1_2 # Python 3.4+
        context = ssl.SSLContext(protocol)

        if server_cert:
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(cafile=server_cert)
        else:
            context.verify_mode = ssl.CERT_OPTIONAL

        if client_cert:
            context.load_cert_chain(client_cert, password=client_cert_password)

        self.handlers['HTTPS'] = urllib.request.HTTPSHandler(
            context=context,
            check_hostname=False
        )

    def remove_HTTPSHandler(self):
        """
        Remove the HTTPS handler.
        """
        self.remove_handler('HTTPS')

    def send_request(self, req_obj):
        """
        Send the request and return the response.
        """
        if self.setup_function:
            self.setup_function()
            self.setup_function = None
        LOGGER.debug(json.dumps(req_obj, indent='  ', sort_keys=True))
        req = json.dumps(req_obj).encode('UTF-8')
        try:
            with self.opener.open(self.uri, req) as handle:
                obj = json.loads(handle.read().decode())
                try:
                    return obj['result']
                except KeyError:
                    raise Aria2JsonRpcError('unexpected result: {}'.format(obj))
        except (urllib.error.URLError, ConnectionResetError) as err:
            # This should work but URLError does not set the errno attribute:
            # e.errno == errno.ECONNREFUSED
            err_str = str(err)
            raise Aria2JsonRpcError(
                err_str,
                connection_error=(
                        '111' in err_str or isinstance(err, ConnectionResetError)
                )
            )
        except http.client.BadStatusLine as err:
            raise Aria2JsonRpcError('{}: BadStatusLine: {} (HTTPS error?)'.format(
                self.__class__.__name__, err
            ))

    def jsonrpc(self, method, params=None, prefix='aria2.'):
        """
        POST a request to the RPC interface.
        """
        if not params:
            params = []

        if self.token is not None:
            token_str = 'token:{}'.format(self.token)
            if method == 'multicall':
                for param in params[0]:
                    try:
                        param['params'].insert(0, token_str)
                    except KeyError:
                        param['params'] = [token_str]
            else:
                params.insert(0, token_str)

        req_obj = {
            'jsonrpc': '2.0',
            'id': self.identity,
            'method': prefix + method,
            'params': params,
        }
        if self.mode == 'batch':
            self.queue.append(req_obj)
            return None
        if self.mode == 'format':
            return req_obj
        return self.send_request(req_obj)

    def process_queue(self):
        """
        Processed queued requests.
        """
        req_obj = self.queue
        self.queue = []
        return self.send_request(req_obj)

    # ----------------------------- Standard Methods ----------------------------- #

    def addUri(self, uris, options=None, position=None):
        """
        aria2.addUri method

        uris: list of URIs

        options: dictionary of additional options

        position: position in queue

        Returns a GID
        """
        params = [uris]
        params = add_options_and_position(params, options, position)
        return self.jsonrpc('addUri', params)

    def addTorrent(self, torrent, uris=None, options=None, position=None):
        """
        aria2.addTorrent method

        torrent: base64-encoded torrent file

        uris: list of webseed URIs

        options: dictionary of additional options

        position: position in queue

        Returns a GID.
        """
        params = [torrent]
        if uris:
            params.append(uris)
        params = add_options_and_position(params, options, position)
        return self.jsonrpc('addTorrent', params)

    def addMetalink(self, metalink, options=None, position=None):
        """
        aria2.addMetalink method

        metalink: base64-encoded metalink file

        options: dictionary of additional options

        position: position in queue

        Returns an array of GIDs.
        """
        params = [metalink]
        params = add_options_and_position(params, options, position)
        return self.jsonrpc('addTorrent', params)

    def remove(self, gid):
        """
        aria2.remove method

        gid: GID to remove
        """
        params = [gid]
        return self.jsonrpc('remove', params)

    def forceRemove(self, gid):
        """
        aria2.forceRemove method

        gid: GID to remove
        """
        params = [gid]
        return self.jsonrpc('forceRemove', params)

    def pause(self, gid):
        """
        aria2.pause method

        gid: GID to pause
        """
        params = [gid]
        return self.jsonrpc('pause', params)

    def pauseAll(self):
        """
        aria2.pauseAll method
        """
        return self.jsonrpc('pauseAll')

    def forcePause(self, gid):
        """
        aria2.forcePause method

        gid: GID to pause
        """
        params = [gid]
        return self.jsonrpc('forcePause', params)

    def forcePauseAll(self):
        """
        aria2.forcePauseAll method
        """
        return self.jsonrpc('forcePauseAll')

    def unpause(self, gid):
        """
        aria2.unpause method

        gid: GID to unpause
        """
        params = [gid]
        return self.jsonrpc('unpause', params)

    def unpauseAll(self):
        """
        aria2.unpauseAll method
        """
        return self.jsonrpc('unpauseAll')

    def tellStatus(self, gid, keys=None):
        """
        aria2.tellStatus method

        gid: GID to query

        keys: subset of status keys to return (all keys are returned otherwise)

        Returns a dictionary.
        """
        params = [gid]
        if keys:
            params.append(keys)
        return self.jsonrpc('tellStatus', params)

    def getUris(self, gid):
        """
        aria2.getUris method

        gid: GID to query

        Returns a list of dictionaries.
        """
        params = [gid]
        return self.jsonrpc('getUris', params)

    def getFiles(self, gid):
        """
        aria2.getFiles method

        gid: GID to query

        Returns a list of dictionaries.
        """
        params = [gid]
        return self.jsonrpc('getFiles', params)

    def getPeers(self, gid):
        """
        aria2.getPeers method

        gid: GID to query

        Returns a list of dictionaries.
        """
        params = [gid]
        return self.jsonrpc('getPeers', params)

    def getServers(self, gid):
        """
        aria2.getServers method

        gid: GID to query

        Returns a list of dictionaries.
        """
        params = [gid]
        return self.jsonrpc('getServers', params)

    def tellActive(self, keys=None):
        """
        aria2.tellActive method

        keys: same as tellStatus

        Returns a list of dictionaries. The dictionaries are the same as those
        returned by tellStatus.
        """
        if keys:
            params = [keys]
        else:
            params = None
        return self.jsonrpc('tellActive', params)

    def tellWaiting(self, offset, num, keys=None):
        """
        aria2.tellWaiting method

        offset: offset from start of waiting download queue
                (negative values are counted from the end of the queue)

        num: number of downloads to return

        keys: same as tellStatus

        Returns a list of dictionaries. The dictionaries are the same as those
        returned by tellStatus.
        """
        params = [offset, num]
        if keys:
            params.append(keys)
        return self.jsonrpc('tellWaiting', params)

    def tellStopped(self, offset, num, keys=None):
        """
        aria2.tellStopped method

        offset: offset from oldest download (same semantics as tellWaiting)

        num: same as tellWaiting

        keys: same as tellStatus

        Returns a list of dictionaries. The dictionaries are the same as those
        returned by tellStatus.
        """
        params = [offset, num]
        if keys:
            params.append(keys)
        return self.jsonrpc('tellStopped', params)

    def changePosition(self, gid, pos, how):
        """
        aria2.changePosition method

        gid: GID to change

        pos: the position

        how: "POS_SET", "POS_CUR" or "POS_END"
        """
        params = [gid, pos, how]
        return self.jsonrpc('changePosition', params)

    def changeUri(self, gid, fileIndex, delUris, addUris, position=None):
        """
        aria2.changePosition method

        gid: GID to change

        fileIndex: file to affect (1-based)

        delUris: URIs to remove

        addUris: URIs to add

        position: where URIs are inserted, after URIs have been removed
        """
        params = [gid, fileIndex, delUris, addUris]
        if position:
            params.append(position)
        return self.jsonrpc('changePosition', params)

    def getOption(self, gid):
        """
        aria2.getOption method

        gid: GID to query

        Returns a dictionary of options.
        """
        params = [gid]
        return self.jsonrpc('getOption', params)

    def changeOption(self, gid, options):
        """
        aria2.changeOption method

        gid: GID to change

        options: dictionary of new options
                 (not all options can be changed for active downloads)
        """
        params = [gid, options]
        return self.jsonrpc('changeOption', params)

    def getGlobalOption(self):
        """
        aria2.getGlobalOption method

        Returns a dictionary.
        """
        return self.jsonrpc('getGlobalOption')

    def changeGlobalOption(self, options):
        """
        aria2.changeGlobalOption method

        options: dictionary of new options
        """
        params = [options]
        return self.jsonrpc('changeGlobalOption', params)

    def getGlobalStat(self):
        """
        aria2.getGlobalStat method

        Returns a dictionary.
        """
        return self.jsonrpc('getGlobalStat')

    def purgeDownloadResult(self):
        """
        aria2.purgeDownloadResult method
        """
        self.jsonrpc('purgeDownloadResult')

    def removeDownloadResult(self, gid):
        """
        aria2.removeDownloadResult method

        gid: GID to remove
        """
        params = [gid]
        return self.jsonrpc('removeDownloadResult', params)

    def getVersion(self):
        """
        aria2.getVersion method

        Returns a dictionary.
        """
        return self.jsonrpc('getVersion')

    def getSessionInfo(self):
        """
        aria2.getSessionInfo method

        Returns a dictionary.
        """
        return self.jsonrpc('getSessionInfo')

    def shutdown(self):
        """
        aria2.shutdown method
        """
        return self.jsonrpc('shutdown')

    def forceShutdown(self):
        """
        aria2.forceShutdown method
        """
        return self.jsonrpc('forceShutdown')

    def multicall(self, methods):
        """
        aria2.multicall method

        methods: list of dictionaries (keys: methodName, params)

        The method names must be those used by Aria2c, e.g. "aria2.tellStatus".
        """
        return self.jsonrpc('multicall', [methods], prefix='system.')

    # --------------------------- Convenience Methods ---------------------------- #
    @staticmethod
    def b64encode_file(path):
        """
        Read a file into a base64-encoded string.
        """
        with open(path, 'rb') as handle:
            return base64.b64encode(handle.read()).encode(JSON_ENCODING)

    def add_torrent(self, path, uris=None, options=None, position=None):
        """
        A wrapper around addTorrent for loading files.
        """
        torrent = self.b64encode_file(path)
        return self.addTorrent(torrent, uris, options, position)

    def add_metalink(self, path, options=None, position=None):
        """
        A wrapper around addMetalink for loading files.
        """
        metalink = self.b64encode_file(path)
        return self.addMetalink(metalink, options, position)

    def get_status(self, gid):
        """
        Get the status of a single GID.
        """
        response = self.tellStatus(gid, ['status'])
        return get_status(response)

    def wait_for_final_status(self, gid, interval=1):
        """
        Wait for a GID to complete or fail and return its status.
        """
        if not interval or interval < 0:
            interval = 1
        while True:
            status = self.get_status(gid)
            if status in TEMPORARY_STATUS:
                time.sleep(interval)
            else:
                return status

    def get_statuses(self, gids):
        """
        Get the status of multiple GIDs. The status of each is yielded in order.
        """
        methods = [
            {
                'methodName': 'aria2.tellStatus',
                'params': [gid, ['gid', 'status']]
            }
            for gid in gids
        ]
        results = self.multicall(methods)
        if results:
            status = dict((r[0]['gid'], r[0]['status']) for r in results)
            for gid in gids:
                try:
                    yield status[gid]
                except KeyError:
                    LOGGER.error(
                        'Aria2 RPC server returned no status for GID %s',
                        gid
                    )
                    yield 'error'
        else:
            LOGGER.error('no response from Aria2 RPC server')
            for gid in gids:
                yield 'error'

    def wait_for_final_statuses(self, gids, interval=1):
        """
        Wait for multiple GIDs to complete or fail and return their statuses in
        order.

        gids:
          A flat list of GIDs.
        """
        if not interval or interval < 0:
            interval = 1
        statusmap = dict((gid, None) for gid in gids)
        remaining = list(
            gid for gid, s in statusmap.items() if s is None
        )
        while remaining:
            for gid, status in zip(remaining, self.get_statuses(remaining)):
                if status in TEMPORARY_STATUS:
                    continue
                statusmap[gid] = status
            remaining = list(
                gid for gid, status in statusmap.items() if status is None
            )
            if remaining:
                time.sleep(interval)
        for gid in gids:
            yield statusmap[gid]

    def print_global_status(self):
        """
        Print global status of the RPC server.
        """
        status = self.getGlobalStat()
        if status:
            numWaiting = int(status['numWaiting'])
            numStopped = int(status['numStopped'])
            keys = ['totalLength', 'completedLength']
            total = self.tellActive(keys)
            waiting = self.tellWaiting(0, numWaiting, keys)
            if waiting:
                total += waiting
            stopped = self.tellStopped(0, numStopped, keys)
            if stopped:
                total += stopped

            downloadSpeed = int(status['downloadSpeed'])
            uploadSpeed = int(status['uploadSpeed'])
            totalLength = sum(int(x['totalLength']) for x in total)
            completedLength = sum(int(x['completedLength']) for x in total)
            remaining = totalLength - completedLength

            status['downloadSpeed'] = format_bytes(downloadSpeed) + '/s'
            status['uploadSpeed'] = format_bytes(uploadSpeed) + '/s'

            preordered = ('downloadSpeed', 'uploadSpeed')

            rows = list(
                (k, v)
                for (k, v) in sorted(status.items())
                if k not in preordered
            )
            rows.extend((x, status[x]) for x in preordered)

            if totalLength > 0:
                rows.append(('total', format(format_bytes(totalLength))))
                rows.append(('completed', format(format_bytes(completedLength))))
                rows.append(('remaining', format(format_bytes(remaining))))
                if completedLength == totalLength:
                    eta = 'finished'
                else:
                    try:
                        eta = format_seconds(remaining // downloadSpeed)
                    except ZeroDivisionError:
                        eta = 'never'
                rows.append(('ETA', eta))

            width_l = max(len(r[0]) for r in rows)
            width_r = max(len(r[1]) for r in rows)
            width_r = max(width_r, len(self.uri) - (width_l + 2))
            fmt = '{{:<{:d}s}}  {{:>{:d}s}}'.format(width_l, width_r)

            print(self.uri)
            for row in rows:
                print(fmt.format(*row))

    def queue_uris(self, uris, options, interval=None):
        """
        Enqueue URIs and wait for download to finish while printing status at
        regular intervals.
        """
        gid = self.addUri(uris, options)
        print('GID: {}'.format(gid))

        if gid and interval is not None:
            blanker = ''
            while True:
                response = self.tellStatus(gid, ['status'])
                if response:
                    try:
                        status = response['status']
                    except KeyError:
                        print('error: no status returned from Aria2 RPC server')
                        break
                    print('{}\rstatus: {}'.format(blanker, status), end='')
                    blanker = ' ' * len(status)
                    if status in TEMPORARY_STATUS:
                        time.sleep(interval)
                    else:
                        break
                else:
                    print('error: no response from server')
                    break

    # ----------------------- Polymethod download handlers ----------------------- #

    def polymethod_enqueue_many(self, downloads):
        """
        Enqueue downloads.

        downloads: Same as polymethod_download().
        """
        methods = list(
            {
                'methodName': 'aria2.{}'.format(d[0]),
                'params': list(d[1:])
            } for d in downloads
        )
        return self.multicall(methods)

    def polymethod_wait_many(self, gid_lists, interval=1):
        """
        Wait for the GIDs to complete or fail and return their statuses.

        gids:
          A list of lists of GIDs.
        """
        # The flattened list of GIDs
        pending_gids = list(itertools.chain.from_iterable(gid_lists))
        statusmap = dict(zip(pending_gids, self.wait_for_final_statuses(pending_gids, interval=interval)))
        # Return the grouped statuses in order.
        for gids in gid_lists:
            yield list(statusmap.get(gid, 'error') for gid in gids)

    def polymethod_enqueue_one(self, download):
        """
        Same as polymethod_enqueue_many but for one element.
        """
        return getattr(self, download[0])(*download[1:])

    def polymethod_download(self, downloads, interval=1):
        """
        Enqueue a series of downloads and wait for them to finish. Iterate over the
        status of each, in order.

        downloads:
          An iterable over (<type>, <args>, ...) where <type> indicates the "add"
          method to use ('addUri', 'addTorrent', 'addMetalink') and everything that
          follows are arguments to pass to that method.

        interval:
          The status check interval while waiting.

        Iterates over the download status of finished downloads. "complete"
        indicates success. Lists of statuses will be returned for downloads that
        create multiple GIDs (e.g. metalinks).
        """
        gids = self.polymethod_enqueue_many(downloads)
        return self.polymethod_wait_many(gids, interval=interval)

    def polymethod_download_bool(self, *args, **kwargs):
        """
        A wrapper around polymethod_download() which returns a boolean for each
        download to indicate success (True) or failure (False).
        """
        #     for status in self.polymethod_download(*args, **kwargs):
        #       yield all(s == 'complete' for s in status)
        return list(all(s == 'complete' for s in status) for status in self.polymethod_download(*args, **kwargs))


# --------------------------------- argparse --------------------------------- #

def add_server_arguments(parser):
    """
    Common command-line arguments for the server.

    Accepts an argparse ArgumentParser or group.
    """
    parser.add_argument('-a', '--address', default='localhost', help='The server host. Default: %(default)s.')
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT, help='The server port. Default: %(default)s.')
    parser.add_argument('-s', '--scheme', default='http', help='The server scheme. Default: %(default)s.')

    # parser.add_argument('--auth', nargs=2, help='HTTP Basic authentication user and password.')

    parser.add_argument('--token', help='Secret RPC token.')

    parser.add_argument('--server-cert', help='HTTPS server certificate file, in PEM format.')
    parser.add_argument('--client-cert', help='HTTPS client certificate file, in PEM format.')
    parser.add_argument('--client-cert-password', help='Prompt for a client certificate password.')


def a2jr_from_args(identity, args):
    """
    Return a new Aria2JsonRpc object using the provided arguments.

    See `add_server_arguments`.
    """
    uri = SERVER_URI_FORMAT.format(args.scheme, args.address, args.port)

    #   if args.auth:
    #     http_user, http_passwd = args.auth
    #   else:
    #     http_user = None
    #     http_passwd = None

    token = args.token

    if args.client_cert and args.client_cert_password:
        client_cert_password = getpass.getpass('password for {}: '.format(args.client_cert))
    else:
        client_cert_password = None

    return Aria2JsonRpc(identity, uri, token=token,
                        #     http_user=http_user, http_passwd=http_passwd,
                        server_cert=args.server_cert,
                        client_cert=args.client_cert,
                        client_cert_password=client_cert_password,
                        )
