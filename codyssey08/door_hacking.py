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



import zipfile
import os
import time
import string
import multiprocessing
import io

CHARSET = string.digits + string.ascii_lowercase  # 0~9 + a~z

def brute_force_memory(zip_bytes, prefixes, result_queue, stop_event):
    zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))

    for a in prefixes:
        for b in CHARSET:
            for c in CHARSET:
                for d in CHARSET:
                    for e in CHARSET:
                        for f in CHARSET:
                            if stop_event.is_set():
                                return
                            pwd = a + b + c + d + e + f
                            try:
                                zip_file.extractall(pwd=pwd.encode('utf-8'))
                                result_queue.put(pwd)
                                stop_event.set()
                                return
                            except:
                                continue

def unlock_zip_optimized():
    start_time = time.time()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(current_dir, 'emergency_storage_key.zip')
    password_txt_path = os.path.join(current_dir, 'password.txt')

    if not os.path.exists(zip_path):
        print('[오류] ZIP 파일이 존재하지 않습니다.')
        return

    print('[INFO] ZIP 파일 메모리 적재 중...')
    with open(zip_path, 'rb') as f:
        zip_bytes = f.read()

    print('[INFO] 병렬 브루트포스 탐색 시작...')
    manager = multiprocessing.Manager()
    result_queue = manager.Queue()
    stop_event = manager.Event()

    cpu_count = multiprocessing.cpu_count()
    chunk_size = len(CHARSET) // cpu_count
    prefix_groups = [CHARSET[i*chunk_size:(i+1)*chunk_size] for i in range(cpu_count - 1)]
    prefix_groups.append(CHARSET[(cpu_count - 1)*chunk_size:])  # 나머지

    processes = []
    for group in prefix_groups:
        p = multiprocessing.Process(target=brute_force_memory, args=(zip_bytes, group, result_queue, stop_event))
        p.start()
        processes.append(p)

    while True:
        if not result_queue.empty():
            found_pwd = result_queue.get()
            elapsed = time.time() - start_time
            with open(password_txt_path, 'w') as f:
                f.write(f'암호: {found_pwd}\n탐색 시간: {elapsed:.2f}초\n')
            print(f'[성공] 암호: {found_pwd} (시간: {elapsed:.2f}초)')
            break
        if all(not p.is_alive() for p in processes):
            print('[실패] 암호를 찾지 못했습니다.')
            break

    for p in processes:
        p.terminate()

if __name__ == '__main__':
    unlock_zip_optimized()