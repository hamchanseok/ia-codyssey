from typing import List, Dict, Any, Optional
from fastapi import FastAPI, APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from model import TodoItem
import csv
import os
import threading


# CSV 저장 경로 설정
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
                writer.writerow(['id', 'task', 'done'])
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
                            'task': row.get('task', '').strip(),
                            'done': _str_to_bool(row.get('done', 'false'))
                        }
                        self.todo_list.append(item)
                    except ValueError:
                        continue

    def _save_to_csv(self) -> None:
        '''메모리 내용을 CSV로 저장한다.'''
        with open(self.csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'task', 'done'])
            for item in self.todo_list:
                writer.writerow([
                    item['id'],
                    item['task'],
                    _bool_to_str(item['done'])
                ])

    def _next_id(self) -> int:
        '''다음 ID 값을 계산한다.'''
        if not self.todo_list:
            return 1
        return max(item['id'] for item in self.todo_list) + 1

    # -------------------------------------
    #              CRUD 기능
    # -------------------------------------

    def add(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Todo 항목 추가.

        입력 payload 예:
        {
            'task': '장보기',
            'done': false
        }
        '''
        task = str(payload.get('task', '')).strip()
        if not task:
            raise HTTPException(status_code=422, detail='task 필드는 필수입니다.')

        done = bool(payload.get('done', False))

        with self._lock:
            new_item = {
                'id': self._next_id(),
                'task': task,
                'done': done
            }
            self.todo_list.append(new_item)
            self._save_to_csv()

        return {
            'result': 'ok',
            'todo': new_item
        }

    def retrieve_all(self) -> Dict[str, Any]:
        '''전체 Todo 목록을 조회한다.'''
        with self._lock:
            items = [dict(item) for item in self.todo_list]
        return {
            'todos': items,
            'count': len(items)
        }

    def retrieve_one(self, todo_id: int) -> Dict[str, Any]:
        '''ID 기준 단일 Todo 항목을 조회한다.'''
        with self._lock:
            for item in self.todo_list:
                if item['id'] == todo_id:
                    return dict(item)
        raise HTTPException(status_code=404, detail='해당 ID의 Todo 항목이 없습니다.')

    def update(self, todo_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Todo 항목 수정.

        payload 예:
        {
            'task': '수정된 내용',
            'done': true
        }
        '''
        task = str(payload.get('task', '')).strip()
        if not task:
            raise HTTPException(status_code=422, detail='task 필드는 비어 있을 수 없습니다.')

        done = bool(payload.get('done', False))

        with self._lock:
            for item in self.todo_list:
                if item['id'] == todo_id:
                    item['task'] = task
                    item['done'] = done
                    self._save_to_csv()
                    return dict(item)

        raise HTTPException(status_code=404, detail='해당 ID의 Todo 항목이 없습니다.')

    def delete(self, todo_id: int) -> None:
        '''ID 기준 Todo 항목 삭제.'''
        with self._lock:
            for index, item in enumerate(self.todo_list):
                if item['id'] == todo_id:
                    del self.todo_list[index]
                    self._save_to_csv()
                    return

        raise HTTPException(status_code=404, detail='해당 ID의 Todo 항목이 없습니다.')


# FastAPI 앱 구성
app = FastAPI(title='Todo API', version='1.0.0')
router = APIRouter(prefix='/todos', tags=['todos'])
store = TodoStore(CSV_PATH)


# -------------------------------------
#             라우터 API
# -------------------------------------

@router.post('', summary='할 일 추가', response_model=dict)
async def add_todo(payload: Optional[Dict[str, Any]] = Body(default=None)) -> Dict[str, Any]:
    '''
    Todo 추가.

    - 메서드: POST /todos
    - 바디 예:
      {
        "task": "장보기",
        "done": false
      }
    '''
    if payload is None or payload == {}:
        return JSONResponse(
            status_code=400,
            content={'warning': '입력 Dict가 비어 있습니다. task 필드를 포함해 주세요.'}
        )
    return store.add(payload)


@router.get('', summary='할 일 목록 조회', response_model=dict)
def retrieve_todo() -> Dict[str, Any]:
    '''
    Todo 전체 목록 조회.

    - 메서드: GET /todos
    '''
    return store.retrieve_all()


@router.get('/{todo_id}', summary='할 일 단건 조회', response_model=dict)
def get_single_todo(todo_id: int) -> Dict[str, Any]:
    '''
    단일 Todo 항목 조회.

    - 메서드: GET /todos/{todo_id}
    '''
    todo = store.retrieve_one(todo_id)
    return {'todo': todo}


@router.put('/{todo_id}', summary='할 일 수정', response_model=dict)
async def update_todo(todo_id: int, item: TodoItem) -> Dict[str, Any]:
    '''
    단일 Todo 항목 수정.

    - 메서드: PUT /todos/{todo_id}
    - 경로 매개변수: todo_id
    - 바디 예:
      {
        "id": 1,
        "task": "수정된 내용",
        "done": true
      }

    전달된 item.id 값은 참고용이며,
    실제 수정 대상은 경로의 todo_id 기준으로 처리한다.
    '''
    payload = {
        'task': item.task,
        'done': item.done
    }
    updated = store.update(todo_id, payload)
    return {
        'result': 'ok',
        'todo': updated
    }


@router.delete('/{todo_id}', summary='할 일 삭제', response_model=dict)
def delete_single_todo(todo_id: int) -> Dict[str, Any]:
    '''
    단일 Todo 항목 삭제.

    - 메서드: DELETE /todos/{todo_id}
    '''
    store.delete(todo_id)
    return {
        'result': 'ok',
        'deleted_id': todo_id
    }


# -------------------------------------
#               실행
# -------------------------------------
app.include_router(router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)