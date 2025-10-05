from typing import List, Set, Optional
import re
import requests
from bs4 import BeautifulSoup


class KbsHeadlineCrawlerBs:
    """KBS 뉴스 메인에서 주요 헤드라인을 수집하는 크롤러(BS4)."""

    # PC 전용 페이지 후보들을 우선 시도
    BASE_CANDIDATES = [
        'https://news.kbs.co.kr/news/pc/main/main.html',
        'https://news.kbs.co.kr/news/pc/index.html',
        'https://news.kbs.co.kr/news/pc/',
        'https://news.kbs.co.kr/',  # 최후 보루
    ]

    # 사용자가 제공한 구조 기반 선택자
    CONTAINER_SELECTOR = 'div.box.head-line.main-head-line.main-page-head-line'
    MAIN_TITLE_SELECTOR = '.main-news-wrapper a.main-news.box-content'
    SUB_TITLE_SELECTOR = '.small-sub-news-wrapper a.box-content'

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout
        self._seen: Set[str] = set()
        self._last_url: Optional[str] = None

    def _headers(self) -> dict:
        return {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://news.kbs.co.kr/'
        }

    def _fetch(self, url: str) -> str:
        cookies = {'platform': 'pc'}  # PC 뷰 힌트
        resp = requests.get(url, headers=self._headers(), cookies=cookies, timeout=self.timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or resp.encoding
        return resp.text or ''

    def fetch_html(self) -> str:
        last_html = ''
        for url in self.BASE_CANDIDATES:
            try:
                html = self._fetch(url)
                # 컨테이너 클래스 키워드가 포함되어 있으면 일단 채택
                if 'main-head-line' in html or 'main-page-head-line' in html:
                    self._last_url = url
                    return html
                last_html = html
            except Exception:
                continue
        # 그래도 못 찾으면 마지막 성공 응답 반환(아래에서 덤프)
        self._last_url = self.BASE_CANDIDATES[-1]
        return last_html

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace('\xa0', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def _extract_title_from_card(a_tag: BeautifulSoup) -> Optional[str]:
        """
        카드(anchor) 안에서 제목을 찾는다.
        우선순위: p.title → img.alt → anchor 자체 텍스트
        """
        # 1) p.title
        p = a_tag.select_one('p.title')
        if p:
            t = p.get_text(' ', strip=True)
            t = t.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
            t = KbsHeadlineCrawlerBs._clean_text(t)
            if t:
                return t

        # 2) img.alt
        img = a_tag.select_one('img[alt]')
        if img:
            alt = img.get('alt') or ''
            # HTML 엔티티 & <br> 정리
            alt = alt.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
            alt = KbsHeadlineCrawlerBs._clean_text(alt)
            if alt:
                return alt

        # 3) anchor 텍스트
        t = a_tag.get_text(' ', strip=True)
        t = KbsHeadlineCrawlerBs._clean_text(t)
        return t or None

    def extract_headlines(self, html: str, limit: int = 20) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        results: List[str] = []

        container = soup.select_one(self.CONTAINER_SELECTOR)
        if not container:
            # 진단용 덤프
            with open('kbs_dump.html', 'w', encoding='utf-8') as f:
                f.write(html)
            return results

        # 메인 톱 카드들
        for a in container.select(self.MAIN_TITLE_SELECTOR):
            title = self._extract_title_from_card(a)
            if title and title not in self._seen:
                self._seen.add(title)
                results.append(title)
                if 0 < limit <= len(results):
                    return results

        # 서브 카드들
        for a in container.select(self.SUB_TITLE_SELECTOR):
            title = self._extract_title_from_card(a)
            if title and title not in self._seen:
                self._seen.add(title)
                results.append(title)
                if 0 < limit <= len(results):
                    return results

        # 컨테이너는 잡혔는데 구조가 약간 다를 때: aria-label 백업
        if not results:
            for a in container.select('a[aria-label="헤드라인 링크"]'):
                title = self._extract_title_from_card(a)
                if title and title not in self._seen:
                    self._seen.add(title)
                    results.append(title)
                    if 0 < limit <= len(results):
                        break

        if not results:
            with open('kbs_dump.html', 'w', encoding='utf-8') as f:
                f.write(html)

        return results

    def run(self, limit: int = 20) -> List[str]:
        html = self.fetch_html()
        return self.extract_headlines(html, limit=limit)


class KospiCrawlerBs:
    """(보너스) KOSPI 지수 간단 수집 예시 (네이버 금융)."""

    BASE_URL = 'https://finance.naver.com/sise/'

    def __init__(self, url: str = BASE_URL, timeout: int = 10) -> None:
        self.url = url
        self.timeout = timeout

    def fetch_html(self) -> str:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://finance.naver.com/'
        }
        resp = requests.get(self.url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or resp.encoding
        return resp.text

    def get_kospi_now(self) -> Optional[str]:
        html = self.fetch_html()
        soup = BeautifulSoup(html, 'html.parser')

        node = soup.select_one('#KOSPI_now') or soup.select_one('#now_value')
        if node:
            return (node.get_text(strip=True) or '').replace(',', '')
        return None


def print_list(title: str, items: List[str]) -> None:
    print(f'\n[{title}] (총 {len(items)}건)')
    for i, s in enumerate(items, 1):
        print(f'{i:02d}. {s}')


def main() -> None:
    # 1) KBS 주요 헤드라인
    kbs = KbsHeadlineCrawlerBs()
    try:
        headlines = kbs.run(limit=20)
        print_list('KBS 주요 헤드라인', headlines)
        if not headlines:
            print('⚠️ 0건입니다. 같은 폴더의 kbs_dump.html을 열어 실제 내려온 HTML 구조를 확인하세요.')
    except Exception as e:
        print('[오류] KBS 헤드라인 수집 중 문제가 발생했습니다:', str(e))

    # 2) (보너스) KOSPI 지수 예시
    kospi = KospiCrawlerBs()
    try:
        now = kospi.get_kospi_now()
        if now:
            print(f'\n[KOSPI 지수(보너스)] 현재가: {now}')
        else:
            print('\n[KOSPI 지수(보너스)] 값을 찾지 못했습니다. 선택자를 점검하세요.')
    except Exception as e:
        print('[오류] KOSPI 수집 중 문제가 발생했습니다:', str(e))


if __name__ == '__main__':
    main()