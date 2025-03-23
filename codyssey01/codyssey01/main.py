print('Hello Mars')

try:
    with open('codyssey01/mission_computer_main.log', 'r') as r:  # 'r'은 읽기 형식으로 불러옴
        str = r.read()
except Exception as e:
    print(e)

print('---로그파일 출력---')
print(str)

pb = []  # 문제가 되는 부분을 저장하기 위한 리스트

print('---보너스 1---')
list = str.split('\n')  # 로그를 줄바꿈 단위로 리스트로 변환
list.reverse()  # 리스트를 시간 역순으로 바꿈
for i in range(1, len(list)-1):
    if 'Oxygen tank' in list[i]:
        pb.append(list[i])
    print(list[i])

pb.sort()  # pb가 시간 역순으로 들어가 있으니 다시 정렬

try:
    with open('codyssey01/problem.txt', 'w') as problem:  # codyssey01 경로에 저장
        for i in pb:
            problem.write(i + '\n')  # 줄바꿈 추가
except Exception as e:
    print(e)


text = '''로그 분석 보고서  

사고 원인 분석  
산소 탱크가 불안정하여 폭발함.

관련 로그
'''
for log in pb:
    text += f'- {log}\n'

try:
    with open('codyssey01/log_analysis.md', 'w', encoding='UTF-8') as analysis:
        analysis.write(text)
except Exception as e:
    print(e)