from __future__ import print_function
import os
import sys
import webbrowser
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from twisted.python import log


def serve_brainy_project(brainy_project, port):
    log.startLogging(sys.stdout)
    serving_path = os.path.join(brainy_project.report_folder_path, 'html')
    root = File(serving_path)
    root.putChild("reports", File(brainy_project.report_folder_path))
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
