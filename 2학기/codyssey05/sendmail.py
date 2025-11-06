from __future__ import annotations  # 앞으로의 타입힌트 호환성을 위해 선언(선택)

import os               # 환경변수에서 계정/비밀번호를 읽을 수 있게 하기 위함
import ssl              # SSL/TLS 보안 연결(465 또는 starttls용 컨텍스트)
import smtplib          # SMTP 클라이언트(표준 라이브러리)
import socket           # 네트워크 타임아웃 등 예외 처리용
import mimetypes        # 첨부파일 MIME 타입 추정
from dataclasses import dataclass           # 간단한 설정 객체를 만들기 위해 사용
from getpass import getpass                 # 터미널에서 비밀번호를 안전하게 입력받기
from typing import List, Optional, Tuple    # 타입 힌트
from email.message import EmailMessage      # 이메일 생성/첨부를 위한 표준 객체



#SMTP의 기본 특징
#전체 이름	Simple Mail Transfer Protocol
#기본 포트	25 (기본), 465 (SSL), 587 (STARTTLS)
#전송 방향	클라이언트 → 메일 서버 (또는 서버 → 서버)
#전송 단위	텍스트 기반 명령(command) 으로 통신
#사용 프로토콜	TCP (신뢰성 있는 연결 보장)
#클라이언트가 SMTP 서버에 연결 -> 서버가 220코드로 서비스 응답됨을 보냄 -> 클라이언트가 서버에 로그인 -> 송신자 설정 -> 수신자 설정 ->메일 본문 작성 및 전송

# =========================
# 설정 및 유틸
# =========================
# mwdh aoyn emcs thdu
@dataclass
class SmtpConfig:
    """
    SMTP 접속 설정을 담는 간단한 데이터 클래스.
    - server: SMTP 서버 주소 (Gmail: 'smtp.gmail.com')
    - port  : 465(SSL) 또는 587(STARTTLS) 사용 권장
    - use_ssl: True면 465(SSL), False면 587(STARTTLS)로 처리
    - username/password: 로그인 계정/앱 비밀번호
    """
    server: str = 'smtp.gmail.com'
    port: int = 465
    use_ssl: bool = True # True면 SMTP_SSL, False면 SMTP+STARTTLS
    username: str = ''
    password: str = ''


def guess_mime_type(file_path: str) -> Tuple[str, str]:
    """
    첨부 파일의 MIME 타입을 추정하여 (main_type, sub_type) 형태로 반환.
    - mimetypes.guess_type()이 실패하면 'application/octet-stream'으로 기본 지정.
    예: ('image', 'png'), ('application', 'pdf')
    """
    mime_type, _ = mimetypes.guess_type(file_path)  # 확장자 기반으로 MIME 타입 추정
    if not mime_type:  # 추정 실패 시일반 바이너리로 처리
        return 'application', 'octet-stream'
    main_type, sub_type = mime_type.split('/', 1) #image/png' → ('image', 'png')
    return main_type, sub_type


# =========================
# 메일 발송기 (핵심 로직)
# =========================

class EmailSender:
    """
    SMTP 서버에 연결해 메일을 발송하는 역할의 클래스.
    - 465(SSL) 방식과 587(STARTTLS) 방식을 모두 지원
    - EmailMessage를 생성(build)하고 send()로 실제 발송
    """

    def __init__(self, config: SmtpConfig) -> None:
        self.config = config

    def build_message(
        self,
        subject: str,                               # 메일 제목
        body: str,                                  # 메일 본문(텍스트)
        sender: str,                                # 보낸 사람 주소
        to_addrs: List[str],                        # 받는 사람 목록
        cc_addrs: Optional[List[str]] = None,       # 참조 목록
        bcc_addrs: Optional[List[str]] = None,      # 숨은참조 목록(헤더에는 넣지 않음)
        attachments: Optional[List[str]] = None     # 첨부파일 경로 목록
    ) -> EmailMessage:
        """
        이메일(제목/본문/수신자/첨부)을 구성하여 EmailMessage 객체를 반환.
        - To, Cc는 헤더에 기록됨
        - Bcc는 헤더에 남기지 않는 것이 일반적이므로, 발송 시 수신자 목록에만 포함
        """
        msg = EmailMessage()                        # 표준 이메일 메시지 객체 생성
        msg['Subject'] = subject                    # 제목 헤더 설정
        msg['From'] = sender                        # 발신자 헤더 설정
        msg['To'] = ', '.join(to_addrs)             # 수신자 헤더를 쉼표로 연결

        if cc_addrs:                                # Cc가 있으면
            msg['Cc'] = ', '.join(cc_addrs)         # Cc 헤더에 기록

        msg.set_content(body)                       # 텍스트 본문 설정

        if attachments:                             # 첨부파일이 있다면
            for path in attachments:                # 각 경로에 대해
                path = path.strip()                 # 공백 제거(가벼운 정규화)
                if not path:                        # 빈 문자열은 건너뛰기
                    continue
                try:
                    main_type, sub_type = guess_mime_type(path)  # MIME 타입 추정
                    with open(path, 'rb') as f:     # 바이너리 모드로 파일 열기
                        data = f.read()             # 파일 내용 읽기
                    filename = os.path.basename(path)  # 파일명만 추출
                    msg.add_attachment(             # 첨부파일로 메시지에 추가
                        data,
                        maintype=main_type,
                        subtype=sub_type,
                        filename=filename
                    )
                except FileNotFoundError:
                    # 파일 경로가 잘못되었거나 파일이 없을 때
                    print(f'⚠ 첨부 파일을 찾을 수 없습니다: {path}')
                except PermissionError:
                    # 파일 권한 문제
                    print(f'⚠ 첨부 파일 접근 권한이 없습니다: {path}')
                except OSError as exc:
                    # 기타 OS 관련 예외
                    print(f'⚠ 첨부 파일 처리 중 OS 오류: {path} ({exc})')

        # 구성된 메시지 반환
        return msg

    def send(self, message: EmailMessage, to_addrs: List[str]) -> None:
        """
        실제 메일 발송 단계.
        - SMTP 서버에 접속(SSL 또는 STARTTLS)
        - 로그인 후 send_message() 호출
        - 다양한 예외 상황을 분기 처리하여 원인 파악이 쉽도록 메시지 출력
        """
        # 최종 수신자 목록 만들기: To + Cc + (필요시 Bcc)
        # Bcc는 헤더에 기록하지 않으므로, 호출자가 to_addrs에 포함시켜 주는 방식 사용
        all_recipients = set(to_addrs)

        # 헤더의 Cc를 실제 수신 대상에 포함(헤더에만 있고 to_addrs에 없을 수 있으므로)
        cc_header = message.get_all('Cc', [])
        if cc_header:
            for part in ','.join(cc_header).split(','):
                addr = part.strip()
                if addr:
                    all_recipients.add(addr)

        # ---------- 465(SSL) 방식 ----------
        if self.config.use_ssl:
            context = ssl.create_default_context()
            try:
                # SMTP_SSL로 즉시 TLS 암호화 상태로 접속
                with smtplib.SMTP_SSL(
                    self.config.server,
                    self.config.port,
                    context=context,
                    timeout=30
                ) as server:
                    # 로그인(앱 비밀번호 사용 권장)
                    server.login(self.config.username, self.config.password)
                    # 메시지 전송 (from_addr는 명시적으로, to_addrs는 리스트로)
                    server.send_message(
                        message,
                        from_addr=message['From'],
                        to_addrs=list(all_recipients)
                    )
                    print('✅ 메일 발송 완료(SSL).')
            except smtplib.SMTPAuthenticationError as exc:
                # 인증 실패 (앱 비밀번호 미사용/오타 등)
                print('❌ 인증 실패: Gmail의 앱 비밀번호를 사용했는지 확인하세요.')
                print(f'   코드={exc.smtp_code}, 응답={exc.smtp_error}')
            except smtplib.SMTPConnectError as exc:
                print('❌ SMTP 서버 연결 실패.')
                print(f'   코드={exc.smtp_code}, 응답={exc.smtp_error}')
            except smtplib.SMTPServerDisconnected:
                print('❌ 서버 연결이 끊어졌습니다.')
            except smtplib.SMTPSenderRefused as exc:
                print(f'❌ 발신자 거부: {exc.sender} (코드={exc.smtp_code})')
            except smtplib.SMTPRecipientsRefused as exc:
                print(f'❌ 수신자 거부: {exc.recipients}')
            except smtplib.SMTPDataError as exc:
                print(f'❌ 데이터 전송 오류: 코드={exc.smtp_code}, 응답={exc.smtp_error}')
            except socket.timeout:
                print('❌ 네트워크 타임아웃: 인터넷 연결을 확인하세요.')
            except ssl.SSLError as exc:
                print(f'❌ SSL 오류: {exc}')
            except Exception as exc:
                # 그 외 모든 예외(최후 방어)
                print(f'❌ 알 수 없는 오류: {exc}')
            return

        # ---------- 587(STARTTLS) 방식 ----------
        try:
            # 평문으로 먼저 접속
            with smtplib.SMTP(self.config.server, self.config.port, timeout=30) as server:
                server.ehlo()  # 서버가 지원하는 확장기능 확인(EHLO 권장)
                # STARTTLS로 평문 → TLS 전환
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                # 로그인(앱 비밀번호 사용 권장)
                server.login(self.config.username, self.config.password)
                # 메시지 전송
                server.send_message(
                    message,
                    from_addr=message['From'],
                    to_addrs=list(all_recipients)
                )
                print('✅ 메일 발송 완료(STARTTLS).')
        except smtplib.SMTPAuthenticationError as exc:
            print('❌ 인증 실패: Gmail의 앱 비밀번호를 사용했는지 확인하세요.')
            print(f'   코드={exc.smtp_code}, 응답={exc.smtp_error}')
        except smtplib.SMTPConnectError as exc:
            print('❌ SMTP 서버 연결 실패.')
            print(f'   코드={exc.smtp_code}, 응답={exc.smtp_error}')
        except smtplib.SMTPServerDisconnected:
            print('❌ 서버 연결이 끊어졌습니다.')
        except smtplib.SMTPSenderRefused as exc:
            print(f'❌ 발신자 거부: {exc.sender} (코드={exc.smtp_code})')
        except smtplib.SMTPRecipientsRefused as exc:
            print(f'❌ 수신자 거부: {exc.recipients}')
        except smtplib.SMTPDataError as exc:
            print(f'❌ 데이터 전송 오류: 코드={exc.smtp_code}, 응답={exc.smtp_error}')
        except socket.timeout:
            print('❌ 네트워크 타임아웃: 인터넷 연결을 확인하세요.')
        except ssl.SSLError as exc:
            print(f'❌ SSL 오류: {exc}')
        except Exception as exc:
            print(f'❌ 알 수 없는 오류: {exc}')


# =========================
# 콘솔 입출력(편의 함수)
# =========================

def prompt_multi_addresses(label: str) -> List[str]:
    """
    쉼표로 구분된 이메일 문자열을 입력 받아 리스트로 변환.
    예: 'a@x.com, b@y.com' → ['a@x.com', 'b@y.com']
    """
    raw = input(f'{label} (쉼표로 여러 개 입력 가능): ').strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(',')]
    return [p for p in parts if p]


def prompt_attachments() -> List[str]:
    """
    쉼표 구분으로 첨부 파일 경로를 입력받아 리스트로 변환.
    빈 입력이면 빈 리스트 반환.
    """
    raw = input('첨부 파일 경로(생략 가능, 여러 개는 쉼표 구분): ').strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(',')]
    return [p for p in parts if p]


def choose_port_mode() -> Tuple[int, bool]:
    """
    사용할 SMTP 포트/모드를 선택.
    - 1 입력 또는 기본: 465(SSL)
    - 2 입력: 587(STARTTLS)
    반환: (port, use_ssl)
    """
    print('\n[SMTP 포트 선택]')
    print('1) 465 (SSL/TLS, 권장)')
    print('2) 587 (STARTTLS, 권장)')
    choice = input('번호 선택(기본: 1): ').strip()
    if choice == '2':
        return 587, False
    return 465, True


# =========================
# 메인 실행부
# =========================

def main() -> None:
    """
    실행 진입점.
    - 환경변수(GMAIL_ADDRESS, GMAIL_APP_PASSWORD, SMTP_SERVER, SMTP_PORT)를 우선 사용
    - 없으면 콘솔에서 입력 받음
    - 본문은 빈 줄 입력 시 종료(간단한 멀티라인 입력)
    """
    print('=== Gmail SMTP 메일 발송기 ===')

    # 보내는 사람 주소/앱 비밀번호: 환경변수 우선 → 사용자 입력
    username = os.getenv('GMAIL_ADDRESS') or input('보내는 사람 Gmail 주소: ').strip()
    password = os.getenv('GMAIL_APP_PASSWORD') or getpass('앱 비밀번호(App Password): ')
    server = os.getenv('SMTP_SERVER') or 'smtp.gmail.com'

    # 포트/모드: 환경변수(SMTP_PORT)가 있으면 사용, 없으면 선택지 표시
    env_port = os.getenv('SMTP_PORT')
    if env_port and env_port.isdigit():
        port = int(env_port)
        use_ssl = (port == 465)  # 465면 SSL, 587이면 STARTTLS로 처리
    else:
        port, use_ssl = choose_port_mode()

    # 설정 객체 구성
    config = SmtpConfig(
        server=server,
        port=port,
        use_ssl=use_ssl,
        username=username,
        password=password
    )

    # 받는 사람/Cc/Bcc 입력
    to_addrs = prompt_multi_addresses('받는 사람 이메일')
    if not to_addrs:
        print('❌ 최소 한 명의 받는 사람을 입력해야 합니다.')
        return

    cc_addrs = prompt_multi_addresses('Cc (생략 가능)')
    bcc_addrs = prompt_multi_addresses('Bcc (생략 가능)')

    # 제목/본문 입력
    subject = input('제목: ').strip()
    print('본문(끝내려면 빈 줄에서 Enter):')
    body_lines: List[str] = []
    while True:
        line = input()
        # 첫 줄부터 바로 빈 줄일 수도 있으므로, 한 줄이라도 입력 이후 빈 줄이면 종료
        if line.strip() == '' and len(body_lines) > 0:
            break
        body_lines.append(line)
    body = '\n'.join(body_lines)

    # 첨부 파일 경로 입력(보너스)
    attachments = prompt_attachments()

    # 메일 메시지 구성
    sender = EmailSender(config=config)
    msg = sender.build_message(
        subject=subject,
        body=body,
        sender=username,
        to_addrs=to_addrs,
        cc_addrs=cc_addrs,
        bcc_addrs=bcc_addrs,
        attachments=attachments
    )

    # 실제 발송 대상: To + Cc + Bcc 모두 합치기
    # - Bcc는 헤더에 남지 않기 때문에 이 단계에서만 합쳐서 전달
    final_recipients = list(to_addrs) + cc_addrs + bcc_addrs

    # 발송
    print('\n메시지 발송 중...')
    sender.send(message=msg, to_addrs=final_recipients)


# 파이썬 스크립트로 직접 실행될 때만 main() 호출
if __name__ == '__main__':
    main()