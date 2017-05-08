# $Id: http.py 59 2010-03-24 15:31:17Z jon.oberheide $

"""Hypertext Transfer Protocol.

This version is modified by Andrew Fleenor, on 2 October 2010, to temporarily
fix the bug where a body is parsed for a request that shouldn't have a body."""

import cStringIO
import dpkt
import logging
import settings

def parse_headers(f):
    """Return dict of HTTP headers parsed from a file object."""
    d = {}
    while 1:
        line = f.readline()
        # regular dpkt checks for premature end of headers
        # but that's too picky
        line = line.strip()
        if not line:
            break
        l = line.split(None, 1)
        if not l[0].endswith(':'):
            raise dpkt.UnpackError('invalid header: %r' % line)
        k = l[0][:-1].lower()
        v = len(l) != 1 and l[1] or ''
        if k in d:
            d[k] += ','+v
        else:
            d[k] = v
    return d


def parse_length(s, base=10):
    """Take a string and convert to int (not long), returning 0 if invalid"""
    try:
        n = int(s, base)
        # int() can actually return long, which can't be used in file.read()
        if isinstance(n, int):
            return n
    except ValueError:
        pass
    # if s was invalid or too big (that is, int returned long)...
    logging.warn('Invalid HTTP content/chunk length "%s", assuming 0' % s)
    return 0


def parse_body(f, version, headers):
    """Return HTTP body parsed from a file object, given HTTP header dict."""
    if headers.get('transfer-encoding', '').lower() == 'chunked':
        l = []
        found_end = False
        while 1:
            try:
                sz = f.readline().split(None, 1)[0]
            except IndexError:
                raise dpkt.UnpackError('missing chunk size')
            n = parse_length(sz, 16)
            if n == 0:  # may happen if sz is invalid
                found_end = True
            buf = f.read(n)
            if f.readline().strip():
                break
            if n and len(buf) == n:
                l.append(buf)
            else:
                break
        if settings.strict_http_parse_body and not found_end:
            raise dpkt.NeedData('premature end of chunked body')
        body = ''.join(l)
    elif 'content-length' in headers:
        # Ethan K B: Have observed malformed 0,0 content lengths
        n = parse_length(headers['content-length'])
        body = f.read(n)
        if len(body) != n:
            logging.warn('HTTP content-length mismatch: expected %d, got %d', n,
                         len(body))
            if settings.strict_http_parse_body:
                raise dpkt.NeedData('short body (missing %d bytes)' % (n - len(body)))
    else:
        # XXX - need to handle HTTP/0.9
        # BTW, this function is not called if status code is 204 or 304
        if version == '1.0':
            # we can assume that there are no further
            # responses on this stream, since 1.0 doesn't
            # support keepalive
            body = f.read()
        elif (version == '1.1' and
              headers.get('connection', None) == 'close'):
            # sender has said they won't send anything else.
            body = f.read()
        # there's also the case where other end sends connection: close,
        # but we don't have the architecture to handle that.
        else:
            # we don't really know what to do
            #print 'returning body as empty string:', version, headers
            body = ''
    return body

def parse_message(message, f):
    """
    Unpack headers and optionally body from the passed file-like object.

    Args:
      message: Request or Response to which to add data.
      f: file-like object, probably StringIO.
    """
    # Parse headers
    message.headers = parse_headers(f)
    # Parse body, unless we know there isn't one
    if not (getattr(message, 'status', None) in ('204', '304')):
        message.body = parse_body(f, message.version, message.headers)
    else:
        message.body = ''
    # Save the rest
    message.data = f.read()

class Message(dpkt.Packet):
    """Hypertext Transfer Protocol headers + body."""
    __metaclass__ = type
    __hdr_defaults__ = {}
    headers = None
    body = None

    def __init__(self, *args, **kwargs):
        if args:
            self.unpack(args[0])
        else:
            self.headers = {}
            self.body = ''
            for k, v in self.__hdr_defaults__.iteritems():
                setattr(self, k, v)
            for k, v in kwargs.iteritems():
                setattr(self, k, v)

    def unpack(self, buf):
        f = cStringIO.StringIO(buf)
        parse_message(self, f)

    def pack_hdr(self):
        return ''.join([ '%s: %s\r\n' % t for t in self.headers.iteritems() ])

    def __len__(self):
        return len(str(self))

    def __str__(self):
        return '%s\r\n%s' % (self.pack_hdr(), self.body)

class Request(Message):
    """Hypertext Transfer Protocol Request."""
    __hdr_defaults__ = {
        'method':'GET',
        'uri':'/',
        'version':'1.0',
        }
    __methods = dict.fromkeys((
        'GET', 'PUT', 'ICY',
        'COPY', 'HEAD', 'LOCK', 'MOVE', 'POLL', 'POST',
        'BCOPY', 'BMOVE', 'MKCOL', 'TRACE', 'LABEL', 'MERGE',
        'DELETE', 'SEARCH', 'UNLOCK', 'REPORT', 'UPDATE', 'NOTIFY',
        'BDELETE', 'CONNECT', 'OPTIONS', 'CHECKIN',
        'PROPFIND', 'CHECKOUT', 'CCM_POST',
        'SUBSCRIBE', 'PROPPATCH', 'BPROPFIND',
        'BPROPPATCH', 'UNCHECKOUT', 'MKACTIVITY',
        'MKWORKSPACE', 'UNSUBSCRIBE', 'RPC_CONNECT',
        'VERSION-CONTROL',
        'BASELINE-CONTROL'
        ))
    __proto = 'HTTP'

    def unpack(self, buf):
        f = cStringIO.StringIO(buf)
        line = f.readline()
        l = line.strip().split()
        if len(l) != 3 or l[0] not in self.__methods or \
           not l[2].startswith(self.__proto):
            raise dpkt.UnpackError('invalid request: %r' % line)
        self.method = l[0]
        self.uri = l[1]
        self.version = l[2][len(self.__proto)+1:]
        parse_message(self, f)

    def __str__(self):
        return '%s %s %s/%s\r\n' % (self.method, self.uri, self.__proto,
                                    self.version) + Message.__str__(self)

class Response(Message):
    """Hypertext Transfer Protocol Response."""
    __hdr_defaults__ = {
        'version':'1.0',
        'status':'200',
        'reason':'OK'
        }
    __proto = 'HTTP'

    def unpack(self, buf):
        f = cStringIO.StringIO(buf)
        line = f.readline()
        l = line.strip().split(None, 2)
        if len(l) < 3 or not l[0].startswith(self.__proto) or not l[1].isdigit():
            raise dpkt.UnpackError('invalid response: %r' % line)
        self.version = l[0][len(self.__proto)+1:]
        self.status = l[1]
        self.reason = l[2]
        parse_message(self, f)

    def __str__(self):
        return '%s/%s %s %s\r\n' % (self.__proto, self.version, self.status,
                                    self.reason) + Message.__str__(self)

if __name__ == '__main__':
    import unittest

    class HTTPTest(unittest.TestCase):
        def test_parse_request(self):
            s = """POST /main/redirect/ab/1,295,,00.html HTTP/1.0\r\nReferer: http://www.email.com/login/snap/login.jhtml\r\nConnection: Keep-Alive\r\nUser-Agent: Mozilla/4.75 [en] (X11; U; OpenBSD 2.8 i386; Nav)\r\nHost: ltd.snap.com\r\nAccept: image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, image/png, */*\r\nAccept-Encoding: gzip\r\nAccept-Language: en\r\nAccept-Charset: iso-8859-1,*,utf-8\r\nContent-type: application/x-www-form-urlencoded\r\nContent-length: 61\r\n\r\nsn=em&mn=dtest4&pw=this+is+atest&fr=true&login=Sign+in&od=www"""
            r = Request(s)
            assert r.method == 'POST'
            assert r.uri == '/main/redirect/ab/1,295,,00.html'
            assert r.body == 'sn=em&mn=dtest4&pw=this+is+atest&fr=true&login=Sign+in&od=www'
            assert r.headers['content-type'] == 'application/x-www-form-urlencoded'
            try:
                r = Request(s[:60])
                assert 'invalid headers parsed!'
            except dpkt.UnpackError:
                pass

        def test_format_request(self):
            r = Request()
            assert str(r) == 'GET / HTTP/1.0\r\n\r\n'
            r.method = 'POST'
            r.uri = '/foo/bar/baz.html'
            r.headers['content-type'] = 'text/plain'
            r.headers['content-length'] = '5'
            r.body = 'hello'
            assert str(r) == 'POST /foo/bar/baz.html HTTP/1.0\r\ncontent-length: 5\r\ncontent-type: text/plain\r\n\r\nhello'
            r = Request(str(r))
            assert str(r) == 'POST /foo/bar/baz.html HTTP/1.0\r\ncontent-length: 5\r\ncontent-type: text/plain\r\n\r\nhello'

        def test_chunked_response(self):
            s = """HTTP/1.1 200 OK\r\nCache-control: no-cache\r\nPragma: no-cache\r\nContent-Type: text/javascript; charset=utf-8\r\nContent-Encoding: gzip\r\nTransfer-Encoding: chunked\r\nSet-Cookie: S=gmail=agg:gmail_yj=v2s:gmproxy=JkU; Domain=.google.com; Path=/\r\nServer: GFE/1.3\r\nDate: Mon, 12 Dec 2005 22:33:23 GMT\r\n\r\na\r\n\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x00\r\n152\r\nm\x91MO\xc4 \x10\x86\xef\xfe\n\x82\xc9\x9eXJK\xe9\xb6\xee\xc1\xe8\x1e6\x9e4\xf1\xe0a5\x86R\xda\x12Yh\x80\xba\xfa\xef\x85\xee\x1a/\xf21\x99\x0c\xef0<\xc3\x81\xa0\xc3\x01\xe6\x10\xc1<\xa7eYT5\xa1\xa4\xac\xe1\xdb\x15:\xa4\x9d\x0c\xfa5K\x00\xf6.\xaa\xeb\x86\xd5y\xcdHY\x954\x8e\xbc*h\x8c\x8e!L7Y\xe6\'\xeb\x82WZ\xcf>8\x1ed\x87\x851X\xd8c\xe6\xbc\x17Z\x89\x8f\xac \x84e\xde\n!]\x96\x17i\xb5\x02{{\xc2z0\x1e\x0f#7\x9cw3v\x992\x9d\xfc\xc2c8\xea[/EP\xd6\xbc\xce\x84\xd0\xce\xab\xf7`\'\x1f\xacS\xd2\xc7\xd2\xfb\x94\x02N\xdc\x04\x0f\xee\xba\x19X\x03TtW\xd7\xb4\xd9\x92\n\xbcX\xa7;\xb0\x9b\'\x10$?F\xfd\xf3CzPt\x8aU\xef\xb8\xc8\x8b-\x18\xed\xec<\xe0\x83\x85\x08!\xf8"[\xb0\xd3j\x82h\x93\xb8\xcf\xd8\x9b\xba\xda\xd0\x92\x14\xa4a\rc\reM\xfd\x87=X;h\xd9j;\xe0db\x17\xc2\x02\xbd\xb0F\xc2in#\xfb:\xb6\xc4x\x15\xd6\x9f\x8a\xaf\xcf)\x0b^\xbc\xe7i\x11\x80\x8b\x00D\x01\xd8/\x82x\xf6\xd8\xf7J(\xae/\x11p\x1f+\xc4p\t:\xfe\xfd\xdf\xa3Y\xfa\xae4\x7f\x00\xc5\xa5\x95\xa1\xe2\x01\x00\x00\r\n0\r\n\r\n"""
            r = Response(s)
            assert r.version == '1.1'
            assert r.status == '200'
            assert r.reason == 'OK'

        def test_multicookie_response(self):
            s = """HTTP/1.x 200 OK\r\nSet-Cookie: first_cookie=cookie1; path=/; domain=.example.com\r\nSet-Cookie: second_cookie=cookie2; path=/; domain=.example.com\r\nContent-Length: 0\r\n\r\n"""
            r = Response(s)
            assert type(r.headers['set-cookie']) is list
            assert len(r.headers['set-cookie']) == 2

    unittest.main()
