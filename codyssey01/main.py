print('Hello Mars')

try:
    with open('codyssey01/mission_computer_main.log', 'r') as r: #'r'은 읽기 형식으로 불러옴 as r은 오픈하는 파일에 이름을 붙여줌
        str = r.read() 
except Exception as e:
    print(e)
    
print('---로그파일 출력---')
print(str)


pb = []#문제가 되는 부분을 저장하기 위한 리스트 

print('---보너스 1---')
list = str.split('\n') #로그를 줄바꿈 단위로 리스트로 변환
list.reverse() # 리스트를 시간 역순으로 바꿈
for i in range(1, len(list)-1):
    if 'Oxygen tank' in list[i]:
        pb.append(list[i])
    print(list[i])


pb.sort()#pb가 시간 역순으로 들어가 있으니 다시 정렬
try:
    with open('problem.txt','w') as problem: #problem.tet 파일을 write 쓰기모드로 열기
        for i in pb: #pb에 들어가 있는 모든 로그를 순회
            problem.write(i) #pb에 들어가 있는 로그를 problem에 로그를 기록
            if i == pb[-1]: # 마지막 로그까지 들어갔다면 break
                break
            
except Exception as e:
    print(e)

text = '''로그 분석 보고서  

사고 원인 분석
산소 탱크가 불안정하여 폭발함.

관련 로그
'''
# text 변수에 분석 보고서 기본 내용을 저장
for log in pb: #pb 리스트의 모든 문제로그를 text에 추가
    text += f'- {log}\n' # markdown리스트 형식으로 저장
    
try:
    with open('log_analysis.md', 'w', encoding = 'UTF-8') as analysis: #log_analysis.md 파일을 UTF-8 형식의 쓰기모드로 열기
        analysis.write(text) #분석내용을 파일에 저장
except Exception as e: 
    print(e)