from typing import List, Dict, Any, Optional
from fastapi import FastAPI, APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
import csv
import os
import threading


# ✅ 현재 파일(todo.py) 위치 기준으로 CSV 파일 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'todo_data.csv')


def _bool_to_str(value: bool) -> str:
    '''Convert boolean to CSV-safe string.'''
    return 'true' if value else 'false'


def _str_to_bool(value: str) -> bool:
    '''Convert CSV string to boolean.'''
    return value.strip().lower() == 'true'


class TodoStore:
    '''
    CSV 기반 간단한 ToDo 저장소.

    - 메모리 목록(todo_list)과 CSV 파일을 동기화한다.
    - 스레드 안전성을 위해 Lock을 사용한다.
    '''
    def __init__(self, csv_path: str) -> None:
        self.csv_path = csv_path
        self.todo_list: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._ensure_csv()
        self._load_from_csv()

    def _ensure_csv(self) -> None:
        '''CSV 파일이 없으면 헤더와 함께 생성한다.'''
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'title', 'done'])
            print(f'[INFO] CSV 파일이 생성되었습니다: {self.csv_path}')

    def _load_from_csv(self) -> None:
        '''CSV 파일에서 메모리로 적재한다.'''
        with self._lock:
            self.todo_list.clear()
            with open(self.csv_path, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        item = {
                            'id': int(row.get('id', '0')),
                            'title': row.get('title', '').strip(),
                            'done': _str_to_bool(row.get('done', 'false'))
                        }
                        self.todo_list.append(item)
                    except ValueError:
                        continue

    def _save_to_csv(self) -> None:
        '''메모리 내용을 CSV로 저장한다.'''
        with open(self.csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'title', 'done'])
            for item in self.todo_list:
                writer.writerow([
                    item['id'],
                    item['title'],
                    _bool_to_str(item['done'])
                ])

    def _next_id(self) -> int:
        '''다음 ID 값을 계산한다.'''
        if not self.todo_list:
            return 1
        return max(item['id'] for item in self.todo_list) + 1

    def add(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''
        새로운 Todo 항목을 추가하고 결과 Dict를 반환한다.

        필수: title
        선택: done (기본 False)
        '''
        if payload == {}:
            # 보너스 과제: 빈 Dict 경고 응답
            return {
                'warning': '입력 Dict가 비어 있습니다. title 필드를 포함해 주세요.'
            }

        title = str(payload.get('title', '')).strip()
        if not title:
            raise HTTPException(status_code=422, detail='title 필드는 필수입니다.')

        done = bool(payload.get('done', False))

        with self._lock:
            new_item = {
                'id': self._next_id(),
                'title': title,
                'done': done
            }
            self.todo_list.append(new_item)
            self._save_to_csv()

        return {
            'result': 'ok',
            'todo': new_item
        }

    def retrieve_all(self) -> Dict[str, Any]:
        '''전체 목록을 Dict로 반환한다.'''
        with self._lock:
            items = [dict(item) for item in self.todo_list]
        return {
            'todos': items,
            'count': len(items)
        }


# ✅ FastAPI 앱 및 라우터 생성
app = FastAPI(title='Todo API', version='1.0.0')
router = APIRouter(prefix='/todos', tags=['todos'])
store = TodoStore(CSV_PATH)


@router.post('', summary='할 일 추가', response_model=dict)
async def add_todo(payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
    # 바디가 아예 없거나 빈 객체면 보너스 과제: 경고 반환(400)
    if payload is None or payload == {}:
        return JSONResponse(
            status_code=400,
            content={'warning': '입력 Dict가 비어 있습니다. title 필드를 포함해 주세요.'}
        )

    result = store.add(payload)
    # store.add에서 추가 검증 실패 시(이상 케이스)도 그대로 반환
    if 'warning' in result:
        return JSONResponse(status_code=400, content=result)
    return result

@router.get('', summary='할 일 목록 조회', response_model=dict)
def retrieve_todo() -> Dict[str, Any]:
    '''
    todo_list 전체를 가져온다.
    - 메서드: GET /todos
    - 입력: 없음
    - 출력: Dict (예: { 'todos': [...], 'count': N })
    '''
    return store.retrieve_all()


# ✅ 라우터 등록
app.include_router(router)


# ✅ uvicorn 실행 진입점
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('todo:app', host='127.0.0.1', port=8000, reload=True)