import argparse
import os.path
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from fundrive.aria2 import Aria2JsonRpc

# --------------------------------- Globals ---------------------------------- #

ID = 'a2jrg-scrape'


# -------------------------------- HTMLParser -------------------------------- #
class LinkScanner(HTMLParser):
    """
    HTML URI scraper.
    """

    def __init__(self, *args, ignore_links=False, ignore_images=False, **kwargs):
        self.links = set()
        self.ignore_links = ignore_links
        self.ignore_images = ignore_images
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        try:
            if tag == 'a':
                if not self.ignore_links:
                    self.links.add(attrs['href'])
            elif tag == 'img':
                if not self.ignore_images:
                    self.links.add(attrs['src'])
        except KeyError:
            pass


# ----------------------------- argument parsing ----------------------------- #
def parse_args(args=None):
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Scrape URIs from a web page and download them with Aria2.', )
    parser.add_argument('uri', help='The URI to scrape.',
                        )
    parser.add_argument(
        'out', metavar='<output dir>',
        help='The output directory.',
    )
    parser.add_argument(
        '-r', '--regex',
        help='Regular expresssion for filtering URIs.',
    )
    parser.add_argument(
        '--ignore-links', action='store_true',
        help='Ignore links.',
    )
    parser.add_argument(
        '--ignore-images', action='store_true',
        help='Ignore images.',
    )
    parser.add_argument(
        '--same',
        help='Indicate that all URIs point to the same file.',
    )

    group = parser.add_argument_group('server options')
    Aria2JsonRpc.add_server_arguments(group)

    group = parser.add_argument_group('download options')
    group.add_argument(
        '-o', '--options', nargs=argparse.REMAINDER,
        help='Aria2 options as key-value pairs separated by "=".'
    )

    return parser.parse_args(args)


# ------------------------------ miscellaneous ------------------------------- #

def get_uris(webpage_uri, **kwargs):
    """
    An iterator over the URIs found at the given HTML webpage.
    """
    scanner = LinkScanner(
        strict=False,
        **kwargs
    )
    with urllib.request.urlopen(webpage_uri) as handle:
        html = handle.read().decode()
    scanner.feed(html)
    for uri in scanner.links:
        uri = urllib.parse.urljoin(webpage_uri, uri)
        uri = urllib.parse.urldefrag(uri).url
        if uri != webpage_uri:
            yield uri


def queue_uris(a2jr, uris, args):
    """
    Queue the given URIs for download via the Aria2 RPC server.
    """
    options = dict()
    options['dir'] = os.path.abspath(args.out)
    if args.options:
        for option in args.options:
            key, value = option.split('=', 1)
            options[key] = value
    if args.same:
        a2jr.queue_uris(uris, options)
    else:
        for uri in uris:
            a2jr.queue_uris([uri], options)


# ----------------------------------- main ----------------------------------- #

def main(args=None):
    pargs = parse_args(args)

    webpage_uri = urllib.parse.urldefrag(pargs.uri).url
    print("collecting URIs...", end='')
    uris = set(get_uris(
        webpage_uri,
        ignore_links=pargs.ignore_links,
        ignore_images=pargs.ignore_images,
    ))
    print(" {:d}".format(len(uris)))

    if pargs.regex:
        regex = re.compile(pargs.regex)
        uris = set(u for u in uris if regex.search(u))
        print("filtered to {:d}".format(len(uris)))

    a2jr = Aria2JsonRpc.a2jr_from_args(ID, pargs)
    queue_uris(a2jr, uris, pargs)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    except urllib.error.HTTPError as err:
        sys.exit(str(err))
