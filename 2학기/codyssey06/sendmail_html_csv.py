from __future__ import annotations

import os
import ssl
import smtplib
import socket
import mimetypes
import csv
from dataclasses import dataclass
from getpass import getpass
from typing import List, Optional, Tuple, Iterable, Sequence
from email.message import EmailMessage
from email.utils import formataddr


# =========================
# 설정 및 유틸
# =========================

@dataclass
class SmtpConfig:
    """
    SMTP 접속 설정을 담는 데이터 클래스.
    - server: SMTP 서버 주소 (Gmail: 'smtp.gmail.com', Naver: 'smtp.naver.com')
    - port  : 465(SSL) 또는 587(STARTTLS)
    - use_ssl: True면 465(SSL), False면 587(STARTTLS)
    - username/password: 로그인 계정/앱 비밀번호
    """
    server: str = 'smtp.gmail.com'
    port: int = 465
    use_ssl: bool = True
    username: str = ''
    password: str = ''


def guess_mime_type(file_path: str) -> Tuple[str, str]:
    """
    첨부 파일의 MIME 타입을 추정하여 (main_type, sub_type) 형태로 반환.
    실패하면 ('application', 'octet-stream')을 반환.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        return 'application', 'octet-stream'
    main_type, sub_type = mime_type.split('/', 1)
    return main_type, sub_type


def load_recipients_from_csv(file_path: str) -> List[Tuple[str, str]]:
    """
    CSV 파일에서 수신자 목록을 로드한다.
    형식: 이름, 이메일
    헤더는 필수이며 '이름','이메일' 이어야 한다.
    """
    recipients: List[Tuple[str, str]] = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # 컬럼 검증
        required = ['이름', '이메일']
        for key in required:
            if key not in reader.fieldnames:
                raise ValueError('CSV 헤더에 반드시 ‘이름, 이메일’이 포함되어야 합니다.')
        # 데이터 로드
        for row in reader:
            name = (row.get('이름') or '').strip()
            email = (row.get('이메일') or '').strip()
            if not name or not email:
                continue
            recipients.append((name, email))
    if not recipients:
        raise ValueError('CSV에서 유효한 수신자를 찾지 못했습니다.')
    return recipients


# =========================
# 메일 발송기
# =========================

class EmailSender:
    """
    SMTP 서버에 연결해 메일을 발송하는 역할의 클래스.
    - 465(SSL) 및 587(STARTTLS) 지원
    - 텍스트/HTML 멀티파트 구성 및 첨부파일 지원
    - 개별/일괄 발송 시 세션 재사용을 위한 connect()/close() 제공
    """

    def __init__(self, config: SmtpConfig) -> None:
        self.config = config
        self._server: Optional[smtplib.SMTP] = None

    # ---------- 연결/종료 ----------

    def connect(self) -> None:
        """
        SMTP 서버에 연결하고 로그인한다.
        개별 발송 루프에서 재사용할 수 있도록 연결을 유지한다.
        """
        if self._server is not None:
            return
        try:
            if self.config.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.config.server,
                    self.config.port,
                    context=context,
                    timeout=30
                )
            else:
                server = smtplib.SMTP(self.config.server, self.config.port, timeout=30)
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()

            server.login(self.config.username, self.config.password)
            self._server = server
        except smtplib.SMTPAuthenticationError as exc:
            self._server = None
            print('❌ 인증 실패: 앱 비밀번호/외부메일 허용 설정을 확인하세요.')
            print(f'   코드={exc.smtp_code}, 응답={exc.smtp_error}')
            raise
        except Exception:
            self._server = None
            raise

    def close(self) -> None:
        """SMTP 연결을 종료한다."""
        if self._server is not None:
            try:
                self._server.quit()
            except Exception:
                try:
                    self._server.close()
                except Exception:
                    pass
            finally:
                self._server = None

    # ---------- 메시지 구성 ----------

    def build_message(
        self,
        subject: str,
        text_body: Optional[str],
        html_body: Optional[str],
        sender_addr: str,
        to_addrs: Sequence[str],
        cc_addrs: Optional[Sequence[str]] = None,
        attachments: Optional[Sequence[str]] = None
    ) -> EmailMessage:
        """
        멀티파트/대체(plain+html) 메시지를 구성한다.
        - text_body 또는 html_body 중 하나는 반드시 존재해야 한다.
        - Bcc는 보안상 헤더에 넣지 않으므로 여기서는 받지 않는다.
        """
        if not text_body and not html_body:
            raise ValueError('텍스트 또는 HTML 본문 중 하나는 반드시 입력해야 합니다.')

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_addr
        msg['To'] = ', '.join(to_addrs)

        if cc_addrs:
            msg['Cc'] = ', '.join(cc_addrs)

        # 멀티파트/대체 구성
        if text_body:
            msg.set_content(text_body)
        else:
            # HTML만 제공된 경우 호환용 텍스트 대체 생성
            msg.set_content('이 메일은 HTML 형식입니다. HTML 보기를 지원하지 않으면 웹메일/클라이언트 설정을 확인하세요.')

        if html_body:
            msg.add_alternative(html_body, subtype='html')

        # 첨부파일
        if attachments:
            for path in attachments:
                p = (path or '').strip()
                if not p:
                    continue
                try:
                    main_type, sub_type = guess_mime_type(p)
                    with open(p, 'rb') as f:
                        data = f.read()
                    filename = os.path.basename(p)
                    msg.add_attachment(
                        data,
                        maintype=main_type,
                        subtype=sub_type,
                        filename=filename
                    )
                except FileNotFoundError:
                    print(f'⚠ 첨부 파일을 찾을 수 없습니다: {p}')
                except PermissionError:
                    print(f'⚠ 첨부 파일 접근 권한이 없습니다: {p}')
                except OSError as exc:
                    print(f'⚠ 첨부 파일 처리 중 OS 오류: {p} ({exc})')

        return msg

    # ---------- 발송 ----------

    def _send_with_current_connection(self, message: EmailMessage, recipients: Iterable[str]) -> None:
        """현재 연결을 사용해 메시지를 전송한다."""
        if self._server is None:
            raise RuntimeError('SMTP 연결이 설정되지 않았습니다. connect()를 먼저 호출하세요.')
        try:
            self._server.send_message(
                message,
                from_addr=message['From'],
                to_addrs=list(recipients)
            )
        except smtplib.SMTPRecipientsRefused as exc:
            print(f'❌ 수신자 거부: {exc.recipients}')
            raise
        except smtplib.SMTPDataError as exc:
            print(f'❌ 데이터 전송 오류: 코드={exc.smtp_code}, 응답={exc.smtp_error}')
            raise

    def send_once(self, message: EmailMessage) -> None:
        """
        단일 메시지를 자체 연결-로그인-종료까지 포함하여 전송한다.
        (소규모 발송에 적합)
        """
        try:
            self.connect()
            all_recipients = self._extract_all_recipients(message)
            self._send_with_current_connection(message, all_recipients)
            print('✅ 메일 발송 완료.')
        finally:
            self.close()

    def send_many(self, messages: Sequence[EmailMessage]) -> None:
        """
        여러 메시지를 한 번의 SMTP 세션으로 전송한다.
        (개별 수신자 맞춤발송 시 효율적)
        """
        try:
            self.connect()
            for idx, msg in enumerate(messages, start=1):
                all_recipients = self._extract_all_recipients(msg)
                self._send_with_current_connection(msg, all_recipients)
                print(f'✅ {idx}건 발송 완료.')
        finally:
            self.close()

    @staticmethod
    def _extract_all_recipients(message: EmailMessage) -> List[str]:
        """
        헤더의 To/Cc를 실제 전송 대상 리스트로 만든다.
        Bcc는 헤더에 존재하지 않으므로, 메시지 외부에서 처리하는 설계를 권장한다.
        """
        collected: List[str] = []
        for key in ('To', 'Cc'):
            values = message.get_all(key, [])
            if not values:
                continue
            # 'a@b, c@d' 형태를 쉼표 기준으로 분리
            for part in ','.join(values).split(','):
                addr = part.strip()
                if addr:
                    collected.append(addr)
        return collected


# =========================
# 콘솔 입출력(편의 함수)
# =========================

def choose_port_mode() -> Tuple[int, bool]:
    """
    사용할 SMTP 포트/모드를 선택.
    1) 465(SSL), 2) 587(STARTTLS)
    """
    print('\n[SMTP 포트 선택]')
    print('1) 465 (SSL/TLS, 권장)')
    print('2) 587 (STARTTLS)')
    choice = input('번호 선택(기본: 1): ').strip()
    if choice == '2':
        return 587, False
    return 465, True


def prompt_body_multiline(prompt: str) -> str:
    """
    멀티라인 입력을 받아 하나의 문자열로 합친다.
    빈 줄에서 종료.
    """
    print(prompt)
    lines: List[str] = []
    while True:
        line = input()
        if line.strip() == '' and len(lines) > 0:
            break
        lines.append(line)
    return '\n'.join(lines)


def build_html_template(recipient_name: Optional[str], html_user_input: str) -> str:
    """
    간단한 HTML 래퍼 템플릿.
    - recipient_name 이 있으면 인사말에 반영한다.
    - html_user_input 은 본문 영역에 삽입한다.
    """
    safe_name = recipient_name or '고객님'
    return (
        '<!doctype html>'
        '<html lang="ko">'
        '<meta charset="utf-8">'
        '<body style="font-family:Arial,Helvetica,Apple SD Gothic Neo,sans-serif; line-height:1.6;">'
        '<img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_160x56dp.png" '
        'alt="Google Logo" style="display:block; width:160px; height:auto;">'
        f'<p style="margin:0 0 16px 0;">{safe_name} 안녕하세요,</p>'
        f'<div>{html_user_input}</div>'
        '<hr style="margin:24px 0;">'
        '<p style="color:#666; font-size:12px;">'
        '본 메일은 HTML 형식으로 발송되었습니다.'
        '</p>'
        '</body>'
        '</html>'
    )


# =========================
# 메인 실행부
# =========================

def main() -> None:
    """
    실행 진입점.
    - HTML/텍스트 본문을 입력받아 멀티파트로 발송
    - CSV 수신자 목록을 로드하여
      (A) 한 통에 여러 명, 또는 (B) 1명씩 개별 발송(권장) 중 선택
    """
    print('=== SMTP HTML 메일 발송기 (CSV) ===')

    # 계정/비밀번호/서버
    username = os.getenv('MAIL_ADDRESS') or input('보내는 사람 주소(예: your@gmail.com): ').strip()
    password = os.getenv('MAIL_PASSWORD') or getpass('앱 비밀번호/계정 비밀번호: ').strip()
    server = os.getenv('SMTP_SERVER') or input('SMTP 서버 (기본: smtp.gmail.com): ').strip() or 'smtp.gmail.com'

    # 포트/모드
    env_port = os.getenv('SMTP_PORT')
    if env_port and env_port.isdigit():
        port = int(env_port)
        use_ssl = (port == 465)
    else:
        port, use_ssl = choose_port_mode()

    config = SmtpConfig(
        server=server,
        port=port,
        use_ssl=use_ssl,
        username=username,
        password=password
    )

    # 제목/본문
    subject = input('제목: ').strip()
    text_body = prompt_body_multiline('텍스트 본문(선택, 비우고 Enter 두 번으로 종료 가능):')
    html_input = prompt_body_multiline('HTML 본문(필수, 비우지 말고 작성 후 빈 줄로 종료):').strip()
    if not html_input:
        print('❌ HTML 본문은 필수입니다.')
        return

    # 첨부 (선택)
    raw_attach = input('첨부 파일 경로(선택, 여러 개는 쉼표): ').strip()
    attachments = [p.strip() for p in raw_attach.split(',')] if raw_attach else []

    # CSV 로드
    csv_path = input('수신자 CSV 경로(기본: mail_target_list.csv): ').strip() or 'mail_target_list.csv'
    try:
        recipients = load_recipients_from_csv(csv_path)
    except Exception as exc:
        print(f'❌ CSV 로드 실패: {exc}')
        return

    # 발송 방식 선택
    print('\n[발송 방식 선택]')
    print('1) 한 통에 여러 명(모두를 To/Cc에 노출)')
    print('2) 1명씩 개별 발송(권장, 수신자 노출 방지/스팸 점수 유리)')
    mode = input('번호 선택(기본: 2): ').strip() or '2'

    sender = EmailSender(config=config)

    if mode == '1':
        # (A) 한 통에 여러 명
        # 받는 사람 표시(이름 <이메일>)로 포매팅
        to_header_list = [formataddr((name, email)) for name, email in recipients]
        html_body = build_html_template(None, html_input)
        try:
            msg = sender.build_message(
                subject=subject,
                text_body=text_body if text_body else None,
                html_body=html_body,
                sender_addr=username,
                to_addrs=to_header_list,
                cc_addrs=None,
                attachments=attachments
            )
            sender.send_once(msg)
        except Exception as exc:
            print(f'❌ 발송 실패: {exc}')
        return

    # (B) 1명씩 개별 발송(세션 재사용)
    messages: List[EmailMessage] = []
    for name, email in recipients:
        to_header_list = [formataddr((name, email))]
        per_html = build_html_template(name, html_input)
        try:
            msg = sender.build_message(
                subject=subject,
                text_body=text_body if text_body else None,
                html_body=per_html,
                sender_addr=username,
                to_addrs=to_header_list,
                cc_addrs=None,
                attachments=attachments
            )
            messages.append(msg)
        except Exception as exc:
            print(f'⚠ 메시지 구성 건너뜀({name}): {exc}')

    if not messages:
        print('❌ 전송할 메시지가 없습니다.')
        return

    try:
        sender.send_many(messages)
        print(f'✅ 총 {len(messages)}건 개별 발송 완료.')
    except smtplib.SMTPException as exc:
        print(f'❌ SMTP 오류: {exc}')
    except socket.timeout:
        print('❌ 네트워크 타임아웃: 연결을 확인하세요.')
    except ssl.SSLError as exc:
        print(f'❌ SSL 오류: {exc}')
    except Exception as exc:
        print(f'❌ 알 수 없는 오류: {exc}')


if __name__ == '__main__':
    main()