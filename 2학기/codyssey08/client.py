import json
import urllib.request
import urllib.error


BASE_URL = 'http://127.0.0.1:8000'


def call_api(method: str, path: str, data: dict | None = None) -> None:
    '''
    Todo API 서버에 HTTP 요청을 보내고, 결과를 출력한다.

    :param method: HTTP 메서드 (GET, POST, PUT, DELETE)
    :param path: 요청 경로 (예: '/todos', '/todos/1')
    :param data: 전송할 JSON 데이터 (dict). 없으면 None.
    '''
    url = BASE_URL + path
    headers = {
        'Content-Type': 'application/json'
    }

    body = None
    if data is not None:
        body_str = json.dumps(data, ensure_ascii=False)
        body = body_str.encode('utf-8')

    request = urllib.request.Request(url, data=body, headers=headers, method=method)

    print(f'\n=== 요청: {method} {url}')
    if data is not None:
        print(f'보내는 데이터: {data}')

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            print(f'응답 코드: {response.status}')
            try:
                parsed = json.loads(response_body)
                pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
                print('응답 본문(JSON):')
                print(pretty)
            except json.JSONDecodeError:
                print('응답 본문(텍스트):')
                print(response_body)
    except urllib.error.HTTPError as error:
        print(f'HTTPError 발생: {error.code}')
        try:
            error_body = error.read().decode('utf-8')
            print('에러 응답 본문:')
            print(error_body)
        except Exception:
            print('에러 내용을 읽을 수 없습니다.')
    except urllib.error.URLError as error:
        print(f'URLError 발생: {error.reason}')


def list_todos() -> None:
    '''전체 Todo 목록 조회'''
    call_api('GET', '/todos')


def get_todo() -> None:
    '''단일 Todo 조회'''
    todo_id_str = input('조회할 Todo의 id를 입력하세요: ').strip()
    if not todo_id_str.isdigit():
        print('id는 숫자여야 합니다.')
        return
    path = f'/todos/{todo_id_str}'
    call_api('GET', path)


def create_todo() -> None:
    '''Todo 생성'''
    task = input('새 Todo의 task 내용을 입력하세요: ').strip()
    if not task:
        print('task는 비어 있을 수 없습니다.')
        return

    done_input = input('done 값(true/false, 기본 false): ').strip().lower()
    if done_input == 'true':
        done = True
    else:
        done = False

    data = {
        'task': task,
        'done': done
    }
    call_api('POST', '/todos', data)


def update_todo() -> None:
    '''Todo 수정'''
    todo_id_str = input('수정할 Todo의 id를 입력하세요: ').strip()
    if not todo_id_str.isdigit():
        print('id는 숫자여야 합니다.')
        return

    task = input('수정할 task 내용을 입력하세요: ').strip()
    if not task:
        print('task는 비어 있을 수 없습니다.')
        return

    done_input = input('done 값(true/false, 기본 false): ').strip().lower()
    if done_input == 'true':
        done = True
    else:
        done = False

    data = {
        'id': int(todo_id_str),
        'task': task,
        'done': done
    }
    path = f'/todos/{todo_id_str}'
    call_api('PUT', path, data)


def delete_todo() -> None:
    '''Todo 삭제'''
    todo_id_str = input('삭제할 Todo의 id를 입력하세요: ').strip()
    if not todo_id_str.isdigit():
        print('id는 숫자여야 합니다.')
        return

    path = f'/todos/{todo_id_str}'
    call_api('DELETE', path)


def print_menu() -> None:
    '''메인 메뉴 출력'''
    print('\n========= Todo 클라이언트 =========')
    print('1. 전체 Todo 목록 조회')
    print('2. 단일 Todo 조회')
    print('3. Todo 생성')
    print('4. Todo 수정')
    print('5. Todo 삭제')
    print('0. 종료')
    print('===================================')


def main() -> None:
    '''클라이언트 메인 루프'''
    while True:
        print_menu()
        choice = input('메뉴 번호를 선택하세요: ').strip()

        if choice == '1':
            list_todos()
        elif choice == '2':
            get_todo()
        elif choice == '3':
            create_todo()
        elif choice == '4':
            update_todo()
        elif choice == '5':
            delete_todo()
        elif choice == '0':
            print('클라이언트를 종료합니다.')
            break
        else:
            print('올바른 메뉴 번호를 입력하세요.')


if __name__ == '__main__':
    main()