import socket, ssl
class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == 'https':
            self.port = 443

        if '/' not in url:
            url += '/'
        self.host, url = url.split('/', 1)
        if ':' in self.host:
            self.host, port = self.host.split(':', 1)
            self.port = int(port)
        self.path = '/' + url
    
    def request(self, headers={}):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))
        if self.scheme == 'https':
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        req_headers = {}
        req_headers['host'] = self.host
        req_headers['connection'] = 'close'
        req_headers['user-agent'] = 'mybrowser/1.0'

        for key, values in headers.items():
            req_headers[key.casefold()] = values
        req =  f"GET {self.path} HTTP/1.1\r\n"
        
        for key, value in req_headers.items():
            req += f'{key}: {value}\r\n'
        req +=  "\r\n"
        s.send(req.encode('utf8'))

        response = s.makefile('r', encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(' ', 2)
        response_header = {}
        while True:
            line = response.readline()
            if line == '\r\n': break
            header, value = line.split(':', 1)
            response_header[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_header
        assert "content-encoding" not in response_header

        body = response.read()
        s.close()
        return body
    def __repr__(self):
        return "URL(scheme={}, host={}, port={}, path={!r})".format(
            self.scheme, self.host, self.port, self.path)
    
def show(body):
    in_tag = False
    for c in body:
        if c == '<':
            in_tag = True
        elif c == '>':
            in_tag = False
        elif not in_tag:
            print(c, end='')

def load(url):
    body = url.request()
    show(body)

if __name__ == '__main__':
    url = 'http://example.org/'
    import sys
    load(URL(sys.argv[1]))