import socket, ssl, urllib.parse, time, tkinter

CACHE = {}
WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class RedirectLoopError(Exception):
    pass

class URL:
    def __init__(self, url):
        self.url = url
        urlinfo = urllib.parse.urlparse(self.url)
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
    
    def request(self, headers={}, redirectionCnt = 0):
        # 캐시 체크
        if self.url in CACHE:
            data, cache_t, max_age = CACHE[self.url]
            expire_t = time.time() - cache_t
                        
            if expire_t < max_age: # 캐시 히트
                return data
            else: # 캐시 만료
                pass
        

        if redirectionCnt >= 300:
            raise RedirectLoopError('Infinite redirect loop')
        
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

            if 300 <= int(status) < 400:
                new_url = response_header['location']
                new_url = urllib.parse.urljoin(self.url, new_url)
                return URL(new_url).request(headers={} , redirectionCnt= redirectionCnt + 1)
            else:
                body = response.read()
                s.close()
                #캐싱
                if 'cache-control' in response_header:
                    c = response_header['cache-control'] 
                    if c == 'no store':
                        pass
                    if 'max-age' in c:
                        max_age = int(c.split('=', 1)[1])
                        CACHE[self.url] = (body, time.time(), max_age)
                    
                return body

    def __repr__(self):
        return "URL(scheme={}, host={}, port={}, path={!r})".format(
            self.scheme, self.host, self.port, self.path)

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )
        self.canvas.pack(
            expand=True,
            fill='both',
        )
        self.scroll = 0
        self.window.bind('<Down>', self.scrolldown)
        self.window.bind('<Configure>', self.resize)

    def draw(self):
        self.canvas.delete('all')
        
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
        
        max_h = max(self.display_list, key=lambda x:x[1])[1]
        if max_h > HEIGHT:
            bar_h = (HEIGHT)**2 / max_h
            x0 = WIDTH - 8
            y0 = self.scroll * HEIGHT / max_h
            self.canvas.create_rectangle(x0, y0, x0 + 8, y0 + bar_h, width=0, fill='blue')

    def load(self, url):
        body = url.request()
        self.text = lex(body)
        self.display_list = layout(self.text)
        self.draw()

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def resize(self, e):
        set_parameters(WIDTH=e.width, HEIGHT=e.height)
        self.display_list = layout(self.text)
        self.draw()


def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP

    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        if c == '\n':
            cursor_y += 2*VSTEP
            cursor_x = HSTEP
        else:
            cursor_x += HSTEP
            if cursor_x >= WIDTH - HSTEP:
                cursor_y += VSTEP
                cursor_x = HSTEP
    
    return display_list


def set_parameters(**params):
	global WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP
	if "WIDTH" in params: WIDTH = params["WIDTH"]
	if "HEIGHT" in params: HEIGHT = params["HEIGHT"]
	if "HSTEP" in params: HSTEP = params["HSTEP"]
	if "VSTEP" in params: VSTEP = params["VSTEP"]
	if "SCROLL_STEP" in params: SCROLL_STEP = params["SCROLL_STEP"]

def lex(body):
    text = ''
    in_tag = False
    for c in body:
        if c == '<':
            in_tag = True
        elif c == '>':
            in_tag = False
        elif not in_tag:
            text += c
    return text



if __name__ == '__main__':
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()