import socket
from datetime import datetime

import click
import requests

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application
from tornado.routing import PathMatches

MAIN_PYPI = 'https://pypi.org/simple/'
JSON_URL = 'https://pypi.org/pypi/{package}/json'

PACKAGE_HTML = """
<!DOCTYPE html>
<html>
  <head>
    <title>Links for {package}</title>
  </head>
  <body>
    <h1>Links for {package}</h1>
{links}
  </body>
</html>
"""


def parse_iso(dt):
    try:
        return datetime.strptime(dt, '%Y-%m-%d')
    except:
        return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')


@click.command()
@click.argument('cutoff_date')
@click.option('--port', default=None)
@click.option('--quiet', default=False, is_flag=True)
def main(cutoff_date, port, quiet):

    CUTOFF = parse_iso(cutoff_date)

    INDEX = requests.get(MAIN_PYPI).content

    class MainIndexHandler(RequestHandler):

        async def get(self):
            return self.write(INDEX)

    class PackageIndexHandler(RequestHandler):

        async def get(self, package):

            package_index = requests.get(JSON_URL.format(package=package)).json()
            release_links = ""
            for release in package_index['releases'].values():
                for file in release:
                    release_date = parse_iso(file['upload_time'])
                    if release_date < CUTOFF:
                        if file['requires_python'] is None:
                            release_links += '    <a href="{url}#sha256={sha256}">{filename}</a><br/>\n'.format(url=file['url'], sha256=file['digests']['sha256'], filename=file['filename'])
                        else:
                            rp = file['requires_python'].replace('>', '&gt;')
                            release_links += '    <a href="{url}#sha256={sha256}" data-requires-python="{rp}">{filename}</a><br/>\n'.format(url=file['url'], sha256=file['digests']['sha256'], rp=rp, filename=file['filename'])

            self.write(PACKAGE_HTML.format(package=package, links=release_links))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    if port is None:
        port = sock.getsockname()[1]
    sock.close()

    app = Application([(r"/", MainIndexHandler),
                       (PathMatches(r"/(?P<package>\S+)\//?"), PackageIndexHandler)])

    app.listen(port=port)

    if not quiet:
        print(f'Starting pypi-timemachine server at http://localhost:{port}')

    IOLoop.instance().start()
