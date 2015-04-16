from __future__ import print_function
import os
import sys
import time
import logging
import webbrowser
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from twisted.python import log


logger = logging.getLogger(__name__)


class NoCacheWrapper(File):

    def render(self, request):
        request.setHeader('Cache-Control', 'no-cache, no-store, '
                          'must-revalidate')
        request.setHeader('Pragma', 'no-cache')
        request.setHeader('Expires', '0')
        request.setLastModified(time.time())
        return super(NoCacheWrapper, self).render(request)


def serve_brainy_project(brainy_project, port):
    log.startLogging(sys.stdout)
    serving_path = os.path.join(brainy_project.report_folder_path, 'html')
    logger.info('Going to serve path: %s' % serving_path)
    root = NoCacheWrapper(serving_path)
    root.putChild("reports", NoCacheWrapper(brainy_project.report_folder_path))
    factory = Site(root)
    url = 'http://localhost:%d/' % port
    # Launch web browser in a fork
    pid = os.fork()
    if pid == 0:
        webbrowser.open(url, new=0, autoraise=True)
    else:
        print('Start serving a brainy project at %s' % url)
        print('You should be able to see it in your browser in a moment..')
        reactor.listenTCP(port, factory)
        reactor.run()
