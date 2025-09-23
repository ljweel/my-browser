import socket, ssl, urllib.parse
class URL:
    def __init__(self, url):

        urlinfo = urllib.parse.urlparse(url)
        
        self.scheme = urlinfo.scheme
        self.host = urlinfo.hostname
        self.path = urlinfo.path
        if self.scheme == 'file':
            self.host = None
            self.path = urlinfo.netloc + urlinfo.path
            self.path = self.path.lstrip()

        if self.scheme in ['http', 'https'] and urlinfo.port: 
            self.port = urlinfo.port
        elif self.scheme == 'http': 
            self.port = 80
        elif self.scheme == 'https': 
            self.port = 443
        else:
            self.port = None
    
    def request(self, headers={}):
        if self.scheme == 'file':

            with open(self.path, 'r') as file:
                body = file.read()
            return body

        
        elif self.scheme in  ['http', 'https']:

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
    import sys
    load(URL(sys.argv[1]))