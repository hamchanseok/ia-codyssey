#pip install SpeechRecognition


import os
import datetime
import wave
import csv
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr

class VoiceRecorder:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.records_dir = os.path.join(script_dir, 'records')

        if not os.path.exists(self.records_dir):
            os.makedirs(self.records_dir)

    def get_timestamp(self):
        now = datetime.datetime.now()
        return now.strftime('%Y%m%d-%H%M%S')

    def record_voice(self, duration=5, sample_rate=44100):
        print('녹음을 시작합니다...')
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='int16'
        )
        sd.wait()

        filename = self.get_timestamp() + '.wav'
        file_path = os.path.join(self.records_dir, filename)

        write(file_path, sample_rate, recording)
        print(f'녹음이 완료되었습니다: {file_path}')

    def list_files_in_range(self, start_date_str, end_date_str):
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y%m%d')
            end_date = datetime.datetime.strptime(end_date_str, '%Y%m%d')
        except ValueError:
            print('날짜 형식이 잘못되었습니다. 예시: 20240601')
            return

        print('날짜 범위 내 녹음 파일 목록:')
        for file in os.listdir(self.records_dir):
            if file.lower().endswith('.wav'):
                try:
                    file_date = datetime.datetime.strptime(
                        file.split('.')[0], '%Y%m%d-%H%M%S'
                    )
                    if start_date <= file_date <= end_date:
                        print(file)
                except ValueError:
                    continue

    def list_all_audio_files(self):
        return [f for f in os.listdir(self.records_dir)
                if f.lower().endswith('.wav')]


class STTProcessor:
    def __init__(self, records_dir, chunk_length=5):
        self.records_dir = records_dir
        self.chunk_length = chunk_length
        self.recognizer = sr.Recognizer()

    def transcribe(self, file_name):
        file_path = os.path.join(self.records_dir, file_name)
        results = []

        # WAV 파일 열어서 전체 길이 계산
        with wave.open(file_path, 'rb') as wf:
            frame_rate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / frame_rate

        offset = 0.0
        while offset < duration:
            with sr.AudioFile(file_path) as source:
                audio = self.recognizer.record(
                    source,
                    offset=offset,
                    duration=self.chunk_length
                )
            try:
                text = self.recognizer.recognize_google(
                    audio, language='ko-KR'
                )
            except sr.UnknownValueError:
                text = ''
            except sr.RequestError as e:
                print(f'STT 서비스 오류: {e}')
                text = ''

            time_str = str(datetime.timedelta(seconds=int(offset)))
            results.append((time_str, text))
            offset += self.chunk_length

        return results

    def save_transcription(self, results, file_name):
        base_name, _ = os.path.splitext(file_name)
        csv_name = base_name + '.CSV'
        csv_path = os.path.join(self.records_dir, csv_name)
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['시간', '인식된 텍스트'])
                for time_str, text in results:
                    writer.writerow([time_str, text])
            print(f'CSV 파일이 저장되었습니다: {csv_path}')
        except Exception as e:
            print(f'CSV 저장 오류: {e}')

    def process_all(self):
        files = self.list_audio_files()
        for file_name in files:
            print(f'파일 처리 중: {file_name}')
            results = self.transcribe(file_name)
            self.save_transcription(results, file_name)

    def search_keyword(self, keyword):
        found = False
        for csv_file in os.listdir(self.records_dir):
            if csv_file.lower().endswith('.csv'):
                csv_path = os.path.join(self.records_dir, csv_file)
                try:
                    with open(csv_path, 'r', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        next(reader, None)  # 헤더 건너뛰기
                        for time_str, text in reader:
                            if keyword in text:
                                print(f'{csv_file}: {time_str} -> {text}')
                                found = True
                except Exception as e:
                    print(f'CSV 읽기 오류 ({csv_file}): {e}')
        if not found:
            print('해당 키워드를 찾을 수 없습니다.')

    def list_audio_files(self):
        # STTProcessor 내부에서 사용되는 list
        return [f for f in os.listdir(self.records_dir)
                if f.lower().endswith('.wav')]


def main():
    recorder = VoiceRecorder()
    stt = STTProcessor(recorder.records_dir, chunk_length=5)

    while True:
        print('\n1. 음성 녹음')
        print('2. 날짜 범위로 파일 목록 보기')
        print('3. 전체 파일 STT 처리 및 CSV 저장')
        print('4. 저장된 CSV에서 키워드 검색')
        print('5. 종료')

        choice = input('선택: ')

        if choice == '1':
            try:
                seconds = int(input('녹음 시간(초): '))
                recorder.record_voice(duration=seconds)
            except ValueError:
                print('숫자 형식이 잘못되었습니다.')
            except Exception:
                print('녹음 중 오류가 발생했습니다.')

        elif choice == '2':
            start = input('시작 날짜 (YYYYMMDD): ')
            end = input('종료 날짜 (YYYYMMDD): ')
            recorder.list_files_in_range(start, end)

        elif choice == '3':
            stt.process_all()

        elif choice == '4':
            keyword = input('검색할 키워드를 입력하세요: ')
            if keyword:
                stt.search_keyword(keyword)

        elif choice == '5':
            print('프로그램을 종료합니다.')
            break

        else:
            print('잘못된 입력입니다.')


if __name__ == '__main__':
    main()
