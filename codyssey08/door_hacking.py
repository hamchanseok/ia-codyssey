<<<<<<< HEAD
# import zipfile
# import time
# import os
# import string

# def unlock_zip():
#     start_time = time.time()
#     charset = string.digits + string.ascii_lowercase
#     total_attempts = 0
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     zip_path = os.path.join(current_dir, 'emergency_storage_key.zip')

#     try:
#         with zipfile.ZipFile(zip_path, 'r') as zip_file:
#             for a in charset:
#                 for b in charset:
#                     for c in charset:
#                         for d in charset:
#                             for e in charset:
#                                 for f in charset:
#                                     password = (a + b + c + d + e + f).encode('utf-8')
#                                     total_attempts += 1

#                                     try:
#                                         zip_file.extractall(pwd=password)
#                                         print('암호 해제 성공!')
#                                         print('암호:', password.decode())
#                                         with open(os.path.join(current_dir, 'password.txt'), 'w') as f:
#                                             f.write(password.decode())
#                                         print('총 시도 횟수:', total_attempts)
#                                         print('총 소요 시간: {:.2f}초'.format(time.time() - start_time))
#                                         return
#                                     except RuntimeError:
#                                         if total_attempts % 100000 == 0:
#                                             print(f'{total_attempts}회 시도 중...')
#                                     except Exception:
#                                         continue

#         print('암호를 찾을 수 없습니다.')
#     except FileNotFoundError:
#         print('[오류] zip 파일이 존재하지 않습니다.')
#     except zipfile.BadZipFile:
#         print('[오류] 잘못된 zip 파일입니다.')
#     except Exception as e:
#         print('[오류] 예기치 못한 오류:', e)

# if __name__ == '__main__':
#     unlock_zip()


import os
import zipfile
import time
import string
from itertools import product
from multiprocessing import Process, Queue, current_process

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_PATH = os.path.join(BASE_DIR, "emergency_storage_key.zip")
PASSWORD_PATH = os.path.join(BASE_DIR, "password.txt")
CHARSET = string.ascii_lowercase + string.digits 
MAX_LENGTH = 6
NUM_WORKERS = 8 #병렬로 살행할 프로세스 수

def crack_zip(start_chars, found_queue, zip_path):
    if not os.path.exists(zip_path):
        print(f"[{current_process().name}] 경고: zip 파일이 존재하지 않습니다.")
        return

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for prefix in start_chars: #6자리 중 첫번째 문자
                for suffix in product(CHARSET, repeat=MAX_LENGTH - 1): #나머지 5자리를 반복문으로 돌림
                    if not found_queue.empty(): #found_queue에 비밀번호를 다 찾으면 중단
                        return

                    password = prefix + ''.join(suffix) #비밀번호 조합 생성
                    try:
                        zf.extractall(pwd=password.encode()) #시도한 비밀번호로 암축 해제
                        print(f"[{current_process().name}] [성공] 암호: {password}")
                        found_queue.put(password)
                        return
                    except:
                        continue
    except Exception as e:
        print(f"[{current_process().name}] 오류: {e}")

def unlock_zip():
    print("[시작] 멀티프로세싱 ZIP 해제 시작")
    start_time = time.time()
    chunk_size = len(CHARSET) // NUM_WORKERS #문자열을 프로세스 수만큼 분할
    char_chunks = [CHARSET[i:i + chunk_size] for i in range(0, len(CHARSET), chunk_size)]
    
    if len(char_chunks) > NUM_WORKERS:
        char_chunks[-2] += char_chunks[-1]
        char_chunks = char_chunks[:-1]

    found_queue = Queue()
    processes = []

    for i in range(NUM_WORKERS):#프로세스 수만큼 생성 
        p = Process(target=crack_zip, args=(char_chunks[i], found_queue, ZIP_PATH), name=f"Worker-{i}") #각 프로세스에 문자 시작 조합과 Queue, zip 경로 전달 
        processes.append(p)
        p.start()

    for p in processes: #모든 프로세스가 종료 될 때까지
        p.join()

    if not found_queue.empty(): #비밀번호를 찾은 경우 
        password = found_queue.get()
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        print(f"[완료] 비밀번호: {password}")
        print(f"[총 소요 시간] {minutes}분 {seconds}초")

        try:
            with open(PASSWORD_PATH, "w", encoding="utf-8") as f:
                f.write(f"비밀번호 : {password}\n")
                f.write(f"{minutes}분 {seconds}초\n")
        except Exception as e:
            print("[에러] password.txt 저장 실패:", e)
    else:
        print("[실패] 암호를 찾지 못했습니다.")
        
if __name__ == '__main__':
    unlock_zip()