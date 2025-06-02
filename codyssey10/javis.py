# pip install sounddevice scipy 외부 라이브러리 설치

import os
import datetime
import sounddevice as sd
from scipy.io.wavfile import write


class VoiceRecorder:
    def __init__(self):
        self.records_dir = os.path.join(os.getcwd(), 'records')
        if not os.path.exists(self.records_dir):
            os.makedirs(self.records_dir)

    def get_timestamp(self):
        now = datetime.datetime.now()
        return now.strftime('%Y%m%d-%H%M%S')

    def record_voice(self, duration = 5, sample_rate = 44100):
        print('녹음을 시작합니다...')
        recording = sd.rec(int(duration * sample_rate), samplerate = sample_rate, channels = 1, dtype = 'int16')
        sd.wait()
        filename = self.get_timestamp() + '.wav'
        file_path = os.path.join(self.records_dir, filename)
        write(file_path, sample_rate, recording)
        print('녹음이 완료되었습니다: {}'.format(file_path))

    def list_files_in_range(self, start_date_str, end_date_str):
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y%m%d')
            end_date = datetime.datetime.strptime(end_date_str, '%Y%m%d')
        except ValueError:
            print('날짜 형식이 잘못되었습니다. 예시: 20240601')
            return

        print('날짜 범위 내 녹음 파일 목록:')
        for file in os.listdir(self.records_dir):
            if file.endswith('.wav'):
                try:
                    file_date = datetime.datetime.strptime(file.split('.')[0], '%Y%m%d-%H%M%S')
                    if start_date <= file_date <= end_date:
                        print(file)
                except Exception:
                    continue


def main():
    recorder = VoiceRecorder()
    while True:
        print('\n1. 음성 녹음')
        print('2. 날짜 범위로 파일 보기')
        print('3. 종료')
        choice = input('선택: ')
        if choice == '1':
            try:
                seconds = int(input('녹음 시간(초): '))
                recorder.record_voice(duration = seconds)
            except Exception:
                print('녹음 중 오류가 발생했습니다.')
        elif choice == '2':
            start = input('시작 날짜 (YYYYMMDD): ')
            end = input('종료 날짜 (YYYYMMDD): ')
            recorder.list_files_in_range(start, end)
        elif choice == '3':
            print('프로그램을 종료합니다.')
            break
        else:
            print('잘못된 입력입니다.')


if __name__ == '__main__':
    main()