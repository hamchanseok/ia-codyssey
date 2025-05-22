import os

def caesar_cipher_decode(target_text):
    result_list = []
    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    for shift in range(1, 26):  
        decoded_text = ''
        for char in target_text:
            if char.islower():
                index = (ord(char) - ord('a') - shift) % 26
                decoded_text += alphabet[index]
            elif char.isupper():
                index = (ord(char) - ord('A') - shift) % 26
                decoded_text += alphabet[index].upper()
            else:
                decoded_text += char
        print(f'{shift} : {decoded_text}') 
        result_list.append(decoded_text)
    return result_list

def load_password_text(base_path):
    try:
        file_path = os.path.join(base_path, 'password.txt')
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print('password.txt 파일을 찾을 수 없습니다.')
    except Exception as e:
        print(f'파일을 읽는 중 오류 발생: {e}')
    return ''

def save_result(result_text, shift_number, base_path):
    try:
        file_path = os.path.join(base_path, 'result.txt')
        with open(file_path, 'w') as file:
            file.write(f'{shift_number} : {result_text}')
        print('해독 결과가 result.txt에 저장되었습니다.')
    except Exception as e:
        print(f'파일을 저장하는 중 오류 발생: {e}')

def contains_dictionary_word(text, dictionary):
    lowered_text = text.lower()
    words = lowered_text.split()
    
    if lowered_text.strip() in [entry.lower() for entry in dictionary]:
        return True
    
    for word in words:
        if word in dictionary:
            return True
    return False

def main():
    base_path = os.path.dirname(os.path.abspath(__file__)) 

    target_text = load_password_text(base_path)
    if not target_text:
        return

    dictionary = ['secret', 'password', 'escape', 'key', 'exit','love', 'mars', 'i', 'i love mars']

    print('--- 카이사르 암호 해독 시도 ---')
    decoded_list = caesar_cipher_decode(target_text)

    for i, decoded in enumerate(decoded_list, start=1):
        if contains_dictionary_word(decoded, dictionary):
            print(f'\n자동 감지됨 - {i}번째 시프트 결과가 의미있는 단어 포함\n')
            save_result(decoded, i, base_path)
            return

    try:
        user_input = input('\n정상적으로 해독된 번호를 입력하세요 (1~25): ')
        shift_index = int(user_input)
        if 1 <= shift_index <= 25:
            save_result(decoded_list[shift_index - 1], shift_index, base_path) 
        else:
            print('유효한 번호가 아닙니다.')
    except ValueError:
        print('숫자를 입력해주세요.')

if __name__ == '__main__':
    main()