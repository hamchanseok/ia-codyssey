def read_csv_file(filename):
    try:
        with open(filename, 'r', encoding='UTF-8') as file:
            content = file.read()
            print('----csv파일 읽어서 출력----')
            print(content)
            lines = content.strip().split('\n')
            data = [line.split(',') for line in lines]
            return data
    except Exception as e:
        print('CSV 파일 읽기 오류:', e)
        return []


def sort_by_flammability(data):
    try:
        header = data[0]
        body = data[1:]
        body.sort(key=lambda x: float(x[4]), reverse=True)
        return [header] + body
    except Exception as e:
        print('정렬 오류:', e)
        return data


def save_to_binary_file(data, filename):
    try:
        with open(filename, 'wb') as f:
            for row in data:
                for item in row:
                    f.write(item.encode())
                    f.write(b' ')
                f.write(b'\n')
    except Exception as e:
        print('이진 파일 저장 오류:', e)


def read_binary_file(filename):
    print('----인화성 정렬 이진파일 출력----')
    try:
        with open(filename, 'rb') as f:
            for line in f.readlines():
                print(line)
    except Exception as e:
        print('이진 파일 읽기 오류:', e)


def filter_high_flammability(data, threshold=0.7):
    high_list = []
    for row in data[1:]:  # skip header
        try:
            if float(row[4]) >= threshold:
                high_list.append(row)
        except ValueError:
            continue
    return high_list


def save_to_csv(data, filename):
    try:
        with open(filename, 'w', encoding='UTF-8') as file:
            file.write('Substance,Weight (g/cm³),Specific Gravity,Strength,Flammability\n')
            for row in data:
                line = ','.join(row)
                file.write(line + '\n')
    except Exception as e:
        print('CSV 저장 오류:', e)


def print_table(data):
    print('─────────────────────────────────────────────────────────────')
    print(f'{"Substance":<20} {"Weight":<10} {"Gravity":<10} {"Strength":<15} {"Flammability":<10}')
    print('─────────────────────────────────────────────────────────────')
    for row in data:
        print(f'{row[0]:<20} {row[1]:<10} {row[2]:<10} {row[3]:<15} {row[4]:<10}')


def main():
    base_path = 'codyssey02/'

    csv_filename = base_path + 'Mars_Base_Inventory_List.csv'
    bin_filename = base_path + 'Mars_Base_Inventory_List.bin'
    danger_csv_filename = base_path + 'Mars_Base_Inventory_danger.csv'

    # 1. CSV 읽기
    data = read_csv_file(csv_filename)
    if not data:
        return

    # 2. 인화성 기준 정렬
    sorted_data = sort_by_flammability(data)

    # 3. 정렬된 데이터를 이진 파일로 저장
    save_to_binary_file(sorted_data, bin_filename)

    # 4. 이진 파일 내용 출력
    read_binary_file(bin_filename)

    # 5. 인화성 0.7 이상 필터링
    danger_items = filter_high_flammability(sorted_data)

    print('\n----인화성 0.7 이상----')
    print_table(danger_items)

    # 6. 필터링된 데이터 CSV 저장
    save_to_csv(danger_items, danger_csv_filename)


if __name__ == '__main__':
    main()