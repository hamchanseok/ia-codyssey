import time
import threading
import random
import platform #cpu와 운영체제의 기본정보를 가져오기 위해 사용 
import psutil #사용량을 실시간으로 체크하기 위해 외부 라이브러리를 사용
import os

class DummySensor:

    def __init__(self):
        self.env_values = {
            "mars_base_internal_temperature": None,
            "mars_base_external_temperature": None,
            "mars_base_internal_humidity": None,
            "mars_base_external_illuminance": None,
            "mars_base_internal_co2": None,
            "mars_base_internal_oxygen": None
        }

    def set_env(self):
        self.env_values["mars_base_internal_temperature"] = random.uniform(18, 30)
        self.env_values["mars_base_external_temperature"] = random.uniform(0, 21)
        self.env_values["mars_base_internal_humidity"] = random.uniform(50, 60)
        self.env_values["mars_base_external_illuminance"] = random.uniform(500, 715)
        self.env_values["mars_base_internal_co2"] = random.uniform(0.02, 0.1)
        self.env_values["mars_base_internal_oxygen"] = random.uniform(4, 7)

    def get_env(self):
        return self.env_values


def dict_to_json_like_string(d):
    json_like = "{\n"
    count = len(d)
    for i, (key, value) in enumerate(d.items()):
        if isinstance(value, str):
            val_str = f'"{value}"'
        else:
            val_str = f"{value:.4f}"
        comma = "," if i < count - 1 else ""
        json_like += f'  "{key}": {val_str}{comma}\n'
    json_like += "}"
    return json_like


class MissionComputer:

    def __init__(self):
        self.ds = DummySensor()
        self.env_values = {}
        self.running = True
        self.accumulated_data = {key: [] for key in self.ds.env_values.keys()}
        self.setting = self.load_settings()

    def load_settings(self): #초기값을 false로 설정
        default = {
            'os': False,
            'os_version': False,
            'cpu_type': False,
            'cpu_cores': False,
            'memory_total': False,
            'cpu_usage': False,
            'memory_usage': False
        }

        # 가능한 정보만 True로 변경 
        try: # 이름이 있는지 확인하여 있으면 true 없으면 false
            default['os'] = bool(platform.system())
            default['os_version'] = bool(platform.version())
            default['cpu_type'] = bool(platform.processor())
            default['cpu_cores'] = os.cpu_count() is not None
            memory = psutil.virtual_memory()
            default['memory_total'] = memory.total > 0
            default['cpu_usage'] = True
            default['memory_usage'] = True
        except Exception as e:
            print('[ERROR] 시스템 정보 확인 실패:', e)

        if not os.path.exists('setting.txt'): #setting.txt파일 생성
            try:
                with open('setting.txt', 'w') as f:
                    for key in default:
                        f.write(f'{key}={"true" if default[key] else "false"}\n')
                print('[INFO] setting.txt 파일이 생성되었습니다.')
            except Exception as e:
                print('[ERROR] setting.txt 자동 생성 실패:', e)
            return default

        try:
            with open('setting.txt', 'r') as f:
                for line in f:
                    parts = line.strip().split('=')
                    if len(parts) == 2:
                        key, value = parts
                        key = key.strip()
                        value = value.strip().lower()
                        if key in default:
                            default[key] = value == 'true'
        except Exception as e:
            print('[ERROR] setting.txt 파일 읽기 실패:', e)

        return default

    def get_sensor_data(self):
        last_five_minute = time.time()
        try:
            while self.running:
                self.ds.set_env()
                self.env_values = self.ds.get_env()

                for key, value in self.env_values.items():
                    self.accumulated_data[key].append(value)

                print(dict_to_json_like_string(self.env_values))
                print("-" * 30)

                time.sleep(5)

                if time.time() - last_five_minute >= 300:
                    print("=== 5분 평균 환경 데이터 ===")
                    avg_data = {
                        key: sum(values) / len(values)
                        for key, values in self.accumulated_data.items()
                    }
                    print(dict_to_json_like_string(avg_data))
                    print("=" * 30)
                    self.accumulated_data = {key: [] for key in self.env_values.keys()}
                    last_five_minute = time.time()

        except KeyboardInterrupt:
            self.running = False
            print("System stopped...")

    def get_mission_computer_info(self): #운영체제 cpu 메모리 정보 
        info = {}
        try:
            if self.setting.get('os'):
                info['Operating System'] = platform.system()
            if self.setting.get('os_version'):
                info['OS Version'] = platform.version()
            if self.setting.get('cpu_type'):
                info['CPU Type'] = platform.processor()
            if self.setting.get('cpu_cores'):
                info['CPU Cores'] = os.cpu_count()
            if self.setting.get('memory_total'): 
                memory = psutil.virtual_memory()
                info['Total Memory (MB)'] = round(memory.total / (1024 * 1024), 2)
        except Exception as e:
            info['Error'] = str(e)

        print("=== Mission Computer Info ===")
        print(dict_to_json_like_string(info))
        print("=" * 30)

    def get_mission_computer_load(self): #실시간 cpu와 메모리 사용량
        load = {}
        try:
            if self.setting.get('cpu_usage'):
                load['CPU Usage (%)'] = psutil.cpu_percent(interval=1) #1초간 평균 cpu 사용률
            if self.setting.get('memory_usage'):
                memory = psutil.virtual_memory()
                load['Memory Usage (%)'] = memory.percent
        except Exception as e:
            load['Error'] = str(e)

        print("=== Mission Computer Load ===")
        print(dict_to_json_like_string(load))
        print("=" * 30)


def listen_for_stop(mission_computer):
    while mission_computer.running:
        key = input()
        if key.lower() == 'q':
            mission_computer.running = False
            print("System stopped...")


if __name__ == "__main__":
    RunComputer = MissionComputer()
    RunComputer.get_mission_computer_info()
    RunComputer.get_mission_computer_load()
    
    stop_thread = threading.Thread(target=listen_for_stop, args=(RunComputer,))
    stop_thread.daemon = True
    stop_thread.start()
    RunComputer.get_sensor_data()