# -*- coding: utf-8 -*-
# PEP8:OK, LINT:OK, PY3:??


#############################################################################
## This file may be used under the terms of the GNU General Public
## License version 2.0 or 3.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http:#www.fsf.org/licensing/licenses/info/GPLv2.html and
## http:#www.gnu.org/copyleft/gpl.html.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#############################################################################


import sys
from os import environ
try:  # py2
    from urllib2 import (Request, ProxyHandler, build_opener,
                         install_opener, CacheFTPHandler, urlopen)
    import xmlrpclib
except ImportError:  # py3
    from urllib import (Request, ProxyHandler, build_opener,  # lint:ok
                        install_opener, CacheFTPHandler, urlopen)
    import xmlrpc.client as xmlrpclib  # lint:ok


# install a proxy handler if required
_proxy = environ.get('http_proxy', None)
if _proxy:
    proxysupport = ProxyHandler({"http": _proxy})
    opener = build_opener(proxysupport, CacheFTPHandler)
    install_opener(opener)


class ProxyTransport(xmlrpclib.Transport):
    ' basic proxy-enabled and DoNotTrack-enabled PyPI API wrapper '
    def request(self, host, handler, request_body, verbose):
        ' make the request via proxy '
        self.verbose = verbose
        url = 'http://{}{}'.format(host, handler)
        request = Request(url)
        request.add_data(request_body)
        # Note: 'Host' and 'Content-Length' are added automatically
        request.add_header("User-Agent", self.user_agent)
        request.add_header("Content-Type", "text/xml")
        request.add_header("DNT", "1")
        f = urlopen(request)
        return(self.parse_response(f))

if __name__ == "__main__":
    pypiurl = 'http://pypi.python.org/pypi'
    transport = ProxyTransport()
    pypi = xmlrpclib.ServerProxy(pypiurl, transport=transport)
    packages = pypi.search({'name': sys.argv[1]})
    for pkg in packages:
        print((pkg['name']))
        print(('  ', pkg['summary'].splitlines()[0]))
