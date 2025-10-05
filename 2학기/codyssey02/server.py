from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime
import json
import os
import sys


INDEX_FILE = 'index.html'
HOST = ''          # 모든 인터페이스 바인딩
PORT = 8080        # 요구사항: 8080 포트


def ensure_index_html() -> None: 
    """index.html 파일이 없으면 기본 파일을 생성한다."""
    if os.path.exists(INDEX_FILE):
        return

    html = (
        '<!doctype html>\n'
        '<html lang=\'ko\'>\n'
        '<head>\n'
        "  <meta charset='utf-8'>\n"
        '  <meta name=\'viewport\' content=\'width=device-width, initial-scale=1\'>\n'
        '  <title>우주 해적 소개</title>\n'
        '  <style>\n'
        '    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Apple SD Gothic Neo,Noto Sans KR,sans-serif;'
        '         margin:0;padding:40px;line-height:1.6;background:#0b1020;color:#e8eaf6}\n'
        '    .card{max-width:840px;margin:0 auto;background:#111735;border:1px solid #2c335a;'
        '          border-radius:12px;padding:28px;box-shadow:0 10px 30px rgba(0,0,0,.35)}\n'
        '    h1{margin-top:0;color:#90caf9}\n'
        '    h2{color:#80cbc4}\n'
        '    p{margin:.6em 0}\n'
        '    .small{opacity:.8;font-size:.9em}\n'
        '  </style>\n'
        '</head>\n'
        '<body>\n'
        '  <div class=\'card\'>\n'
        '    <h1>우주 해적(Space Pirates)</h1>\n'
        '    <p>광활한 은하를 무대로 활동하는 자유로운 항해자이자, 때로는 법의 경계를 넘나드는 모험가들입니다.</p>\n'
        '    <h2>특징</h2>\n'
        '    <ul>\n'
        '      <li>은하 간 항로와 밀수 루트에 대한 방대한 정보력</li>\n'
        '      <li>소수 정예로 구성된 승무원과 커스텀 개조 함선</li>\n'
        '      <li>변칙, 교란, 기만 전술에 최적화된 전투 방식</li>\n'
        '    </ul>\n'
        '    <h2>대표 전술</h2>\n'
        '    <p>스텔스 필드를 활용한 급습, 교란 비컨으로 적 레이더 무력화,'
        '       그리고 나노 드론을 통한 선내 침투 작전을 즐겨 사용합니다.</p>\n'
        '    <p class=\'small\'>이 페이지는 내장 HTTP 서버가 제공하는 정적 문서 예시입니다.</p>\n'
        '  </div>\n'
        '</body>\n'
        '</html>\n'
    )
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(html)


def is_private_ip(ip: str) -> bool:
    """사설/루프백/링크로컬 IP 여부를 대략 판별한다."""
    return (
        ip.startswith('10.') or
        ip.startswith('127.') or
        ip.startswith('192.168.') or
        ip.startswith('169.254.') or
        ip.startswith('::1') or
        ip.startswith('fc') or
        ip.startswith('fd') or
        ip.startswith('fe80:')
    )


def lookup_geo(ip: str) -> str:
    """
    보너스: 공개 API(ip-api.com)로 대략적인 위치를 조회한다.
    표준 라이브러리(urllib)만 사용. 실패하거나 사설 IP면 'N/A' 반환.
    """
    if not ip or is_private_ip(ip): # ip가 없거나 사설/로컬 IP면 위치 조회를 하지 않음.
        return 'N/A'

    url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,query' # ip-api.com에서 필요한 필드만 요청
    try:
        with urlopen(url, timeout=3) as resp:
            data = resp.read().decode('utf-8', errors='ignore')
            payload = json.loads(data)
            if payload.get('status') == 'success':
                country = payload.get('country') or ''
                region = payload.get('regionName') or ''
                city = payload.get('city') or ''
                loc = ', '.join([p for p in (city, region, country) if p])
                return loc if loc else 'N/A'
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return 'N/A'

    return 'N/A'


class SpacePirateHandler(SimpleHTTPRequestHandler):
    """index.html을 제공하고, 접속 시간/IP/위치(가능 시)를 서버 콘솔에 출력한다."""

    server_version = 'SpacePirateHTTP/1.0'

    def _log_client_info(self) -> None:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip = self.client_address[0] if self.client_address else 'unknown'
        geo = lookup_geo(ip)
        print(f'[접속 시간] {now}  [IP] {ip}  [대략 위치] {geo}')

    def do_GET(self) -> None:
        """GET 요청 처리: 루트(/)는 index.html을 응답한다."""
        self._log_client_info()

        # 루트 또는 /index.html 요청은 index.html 제공
        if self.path in ('/', '/index.html'):
            try:
                with open(INDEX_FILE, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                # 파일이 없다면 404가 아니라, 친절히 기본 파일 생성 후 재시도
                ensure_index_html()
                with open(INDEX_FILE, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            return

        # 기타 정적 파일은 상위 동작으로 처리
        super().do_GET()

    def log_message(self, format: str, *args) -> None:
        """
        기본 접근 로그(127.0.0.1 - - ... "GET / ... 200 -")는
        과도할 수 있어 조용히 한다. 필요 시 주석 해제해서 사용.
        """
        return


def run_server() -> None:
    """서버를 실행한다."""
    ensure_index_html()

    address = (HOST, PORT)
    httpd = ThreadingHTTPServer(address, SpacePirateHandler)

    print('===============================================')
    print(f' HTTP 서버 시작: http://localhost:{PORT}/')
    print(' 포트: 8080 (브라우저에서 접속하세요)')
    print(' 접속 시 서버 콘솔에 [접속 시간], [IP], [대략 위치]가 출력됩니다.')
    print(' 종료: Ctrl + C')
    print('===============================================')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n서버를 종료합니다.')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    run_server()