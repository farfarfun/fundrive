import argparse
import os

from fundrive.aria2 import Aria2JsonRpc

ID = 'a2jrg'


def parse_args(args=None):
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Queue downloads via the Aria2 RPC interface.')
    parser.add_argument('uris', metavar='<URI>', nargs='*', help='File URIs. These must all point to the same file.')

    group = parser.add_argument_group('server options')
    Aria2JsonRpc.add_server_arguments(group)

    group = parser.add_argument_group('download options')
    group.add_argument('-o', '--options', nargs=argparse.REMAINDER,
                       help='Aria2 options as key-value pairs separated by "=".')

    group = parser.add_argument_group('commands')
    group.add_argument('--pause-all', action='store_true', help='Pause all downloads.')
    group.add_argument('--unpause-all', action='store_true', help='Unpause all downloads.')
    group.add_argument('--purge', action='store_true', help='Purge download results.')

    group = parser.add_argument_group('other options')
    group.add_argument('-w', '--wait', action='store_true', help='Wait for the download to finish')
    group.add_argument('-i', '--interval', type=int, default=1,
                       help='Status query interval while waiting, in seconds. Default: %(default)s.')
    group.add_argument('--status', action='store_true', help='Print global status report.')
    group.add_argument('--version', action='store_true', help='Print server version.')

    return parser.parse_args(args)


# --------------------------------- Actions ---------------------------------- #

def queue_uris(a2jr, args):
    """
    Queue URIs given an Aria2JsonRpc object and arguments. This will set the
    current directory to the download destination if one has not yet been given.
    """
    options = dict()
    if args.options:
        for option in args.options:
            key, value = option.split('=', 1)
            options[key] = value
    if 'dir' not in options:
        options['dir'] = os.getcwd()
    if args.wait:
        a2jr.queue_uris(args.uris, options, interval=args.interval)
    else:
        a2jr.queue_uris(args.uris, options)


# ----------------------------------- Main ----------------------------------- #

def main(args=None):
    """
    Parse command-line arguments and send the command to the RPC server.
    """
    pargs = parse_args(args)

    a2jr = Aria2JsonRpc.a2jr_from_args(ID, pargs)

    if pargs.pause_all:
        a2jr.pauseAll()

    elif pargs.unpause_all:
        a2jr.unpauseAll()

    if pargs.status:
        a2jr.print_global_status()

    if pargs.version:
        version = a2jr.getVersion()
        print('version: {}'.format(version['version']))
        print('enabled features:')
        for feature in version['enabledFeatures']:
            print(' ', feature)

    if pargs.uris:
        queue_uris(a2jr, pargs)

    if pargs.purge:
        a2jr.purgeDownloadResult()


if __name__ == '__main__':
    main()
