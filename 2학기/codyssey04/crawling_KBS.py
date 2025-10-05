import sys
import re
import getpass
import imaplib
import email
from email.header import decode_header, make_header
from html.parser import HTMLParser
from typing import List, Dict, Optional, Tuple
import requests


class HtmlLinkTextParser(HTMLParser):
    """간단한 링크/텍스트 수집기: <a>의 href와 텍스트, 주요 섹션 텍스트를 수집한다."""

    def __init__(self) -> None:
        super().__init__()
        self.in_a = False
        self.current_href = ''
        self.links: List[Tuple[str, str]] = []  # (text, href)
        self.texts: List[str] = []
        self._text_buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        if tag.lower() == 'a':
            self.in_a = True
            self.current_href = ''
            for k, v in attrs:
                if k.lower() == 'href':
                    self.current_href = v or ''

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == 'a':
            text = ''.join(self._text_buffer).strip()
            if text or self.current_href:
                self.links.append((self._normalize_space(text), self.current_href))
            self.in_a = False
            self._text_buffer.clear()

    def handle_data(self, data: str) -> None:
        if not data:
            return
        if self.in_a:
            self._text_buffer.append(data)
        else:
            cleaned = self._normalize_space(data)
            if cleaned:
                self.texts.append(cleaned)

    @staticmethod
    def _normalize_space(s: str) -> str:
        return re.sub(r'\s+', ' ', s).strip()


class NaverClient:
    """네이버 페이지를 가져오기 위한 간단한 클라이언트. 로그인 상태는 쿠키 문자열로 재현한다."""

    MAIN_URL = 'https://www.naver.com/'

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            )
        })

    def set_cookie_header(self, cookie_header: str) -> None:
        """브라우저에서 복사한 'cookie:' 헤더 값 전체를 세션에 주입한다."""
        if not cookie_header or 'NID_SES' not in cookie_header:
            # 로그인 쿠키에 자주 보이는 키를 간단히 검증 (완벽 검사는 아님)
            print('⚠️ 경고: 로그인 관련 쿠키가 아닐 수 있습니다. 계속 진행합니다.')
        self.session.headers.update({'Cookie': cookie_header})

    def fetch_main_html(self, use_session_cookies: bool = False) -> str:
        """네이버 메인 HTML을 반환. use_session_cookies=False면 쿠키 없이 요청."""
        if not use_session_cookies:
            # 쿠키 없이 요청하기 위해 임시 세션 사용
            temp = requests.Session()
            temp.headers.update(self.session.headers)
            if 'Cookie' in temp.headers:
                del temp.headers['Cookie']
            resp = temp.get(self.MAIN_URL, timeout=self.timeout)
        else:
            resp = self.session.get(self.MAIN_URL, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text


class ContentComparator:
    """로그인 전/후 HTML에서 링크/텍스트를 추출하고, 로그인 상태에서만 보이는 후보를 선별한다."""

    # 로그인 사용자에게 자주 보이는 키워드(휴리스틱)
    LOGIN_ONLY_HINTS = [
        '메일', '쪽지', '네이버페이', 'pay', '내정보', 'my', '구독', 'my구독',
        '알림', '내소식', 'calendar', '캘린더', '포인트', '쿠폰', '페이포인트'
    ]

    def parse(self, html: str) -> Dict[str, List[str]]:
        parser = HtmlLinkTextParser()
        parser.feed(html)
        # 링크 텍스트와 전체 텍스트 풀을 병합 후 중복 제거
        merged_texts = [t for t in parser.texts]
        for t, _href in parser.links:
            if t:
                merged_texts.append(t)
        unique_texts = self._unique_keep_order(merged_texts)
        link_texts = self._unique_keep_order([t for t, _ in parser.links if t])
        return {
            'all_texts': unique_texts,
            'link_texts': link_texts,
        }

    def diff_login_only(self, anon: Dict[str, List[str]], logged: Dict[str, List[str]]) -> List[str]:
        """로그인 상태에서만 나타나는 텍스트 후보를 반환."""
        anon_set = set(anon.get('all_texts', []))
        logged_texts = logged.get('all_texts', [])
        only_in_logged = [t for t in logged_texts if t not in anon_set]
        # 힌트 기반으로 가중 필터링
        strong_candidates: List[str] = []
        weak_candidates: List[str] = []
        for t in only_in_logged:
            if self._has_hint(t):
                strong_candidates.append(t)
            elif self._is_probably_personal(t):
                weak_candidates.append(t)
        # 우선 강한 후보, 그 다음 약한 후보(상위 일부) 반환
        result = self._unique_keep_order(strong_candidates + weak_candidates[:30])
        # 보기 좋게 상위 50개로 제한
        return result[:50]

    @classmethod
    def _unique_keep_order(cls, items: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for it in items:
            if it not in seen:
                seen.add(it)
                out.append(it)
        return out

    @classmethod
    def _has_hint(cls, text: str) -> bool:
        low = text.lower()
        for h in cls.LOGIN_ONLY_HINTS:
            if h.lower() in low:
                return True
        return False

    @staticmethod
    def _is_probably_personal(text: str) -> bool:
        """개인화 가능성이 있어 보이는 텍스트 간단 추정(숫자 포함, 길이 제한 등)."""
        if len(text) < 2:
            return False
        if re.search(r'\d', text):
            return True
        if '내 ' in text or '나의' in text:
            return True
        return False


class NaverMailFetcher:
    """
    보너스: IMAP으로 네이버 메일 제목을 가져온다.
    - 2단계 인증 중이면 '앱 비밀번호' 생성 후 사용 권장
    """

    IMAP_HOST = 'imap.naver.com'
    IMAP_PORT = 993

    def __init__(self, email_addr: str, password: str, ssl: bool = True) -> None:
        self.email_addr = email_addr
        self.password = password
        self.ssl = ssl
        self.conn: Optional[imaplib.IMAP4] = None

    def __enter__(self) -> 'NaverMailFetcher':
        if self.ssl:
            self.conn = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
        else:
            self.conn = imaplib.IMAP4(self.IMAP_HOST, 143)
        self.conn.login(self.email_addr, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.conn is not None:
            try:
                self.conn.logout()
            except Exception:
                pass

    def list_recent_subjects(self, limit: int = 10) -> List[str]:
        if self.conn is None:
            return []
        typ, _ = self.conn.select('INBOX')
        if typ != 'OK':
            return []

        typ, data = self.conn.search(None, 'ALL')
        if typ != 'OK' or not data or not data[0]:
            return []

        ids = data[0].split()
        ids = ids[-limit:]  # 최신 limit개
        subjects: List[str] = []

        for msg_id in reversed(ids):
            typ, msg_data = self.conn.fetch(msg_id, '(RFC822)')
            if typ != 'OK' or not msg_data:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            dh = decode_header(msg.get('Subject', ''))
            subject = str(make_header(dh))
            subjects.append(subject.strip())
        return subjects


def main() -> None:
    print('[NAVER 로그인 전/후 콘텐츠 비교 | 표준 라이브러리 + requests 버전]')
    client = NaverClient(timeout=10)
    comparator = ContentComparator()

    # 1) 로그인 전 HTML
    try:
        anon_html = client.fetch_main_html(use_session_cookies=False)
    except Exception as exc:
        print(f'실패: 비로그인 HTML 수집 중 오류: {exc}')
        sys.exit(1)

    # 2) 쿠키 입력받아 로그인 상태 재현
    print('\n브라우저에서 복사한 네이버 cookie 헤더 전체를 붙여넣으세요.')
    print('예: NID_AUT=...; NID_SES=...; ...')
    cookie_header = input('cookie> ').strip()
    if not cookie_header:
        print('쿠키가 비어 있어 로그인 상태 비교를 건너뜁니다.')
        cookie_html = ''
    else:
        client.set_cookie_header(cookie_header)
        try:
            cookie_html = client.fetch_main_html(use_session_cookies=True)
        except Exception as exc:
            print(f'실패: 로그인(쿠키) HTML 수집 중 오류: {exc}')
            cookie_html = ''

    # 3) 파싱 및 비교
    anon_parsed = comparator.parse(anon_html)
    if cookie_html:
        logged_parsed = comparator.parse(cookie_html)
        login_only = comparator.diff_login_only(anon_parsed, logged_parsed)
    else:
        login_only = []

    # 4) 결과 출력
    print('\n=== 로그인 상태에서만 보일 가능성이 높은 텍스트 후보(최대 50개) ===')
    if not login_only:
        print('(없음 또는 쿠키 미설정/유효하지 않음)')
    else:
        for i, t in enumerate(login_only, start=1):
            print(f'{i:02d}. {t}')

    # 5) 보너스: 네이버 메일 제목 가져오기(IMAP)
    ans = input('\n보너스) 네이버 메일(INBOX) 제목을 가져올까요? (y/N) ').strip().lower()
    if ans == 'y':
        email_addr = input('네이버 이메일 주소(예: user@naver.com): ').strip()
        print('비밀번호(또는 앱 비밀번호)는 화면에 표시되지 않습니다.')
        password = getpass.getpass('비밀번호 입력: ')
        try:
            limit = _safe_int(input('가져올 개수(기본 10): ').strip(), default=10)
            with NaverMailFetcher(email_addr, password) as mf:
                subjects = mf.list_recent_subjects(limit=limit)
            print('\n=== INBOX 최신 제목 ===')
            if not subjects:
                print('(가져온 제목이 없습니다. IMAP/보안 설정을 확인하세요.)')
            else:
                for i, s in enumerate(subjects, start=1):
                    print(f'{i:02d}. {s}')
        except imaplib.IMAP4.error as exc:
            print(f'IMAP 인증/접속 오류: {exc}')
        except Exception as exc:
            print(f'예상치 못한 오류: {exc}')

    print('\n작업 완료.')


def _safe_int(s: str, default: int = 10) -> int:
    try:
        return int(s)
    except Exception:
        return default


if __name__ == '__main__':
    main()