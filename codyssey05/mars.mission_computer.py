import random
import platform
import json
import os

try:
    import psutil
except ImportError:
    psutil = None


class DummySensor:

    def __init__(self):
        self.__env_values = {
            "mars_base_internal_temperature": None,
            "mars_base_external_temperature": None,
            "mars_base_internal_humidity": None,
            "mars_base_external_illuminance": None,
            "mars_base_internal_co2": None,
            "mars_base_internal_oxygen": None
        }

    def set_env(self):
        self.__env_values["mars_base_internal_temperature"] = random.uniform(18, 30)
        self.__env_values["mars_base_external_temperature"] = random.uniform(0, 21)
        self.__env_values["mars_base_internal_humidity"] = random.uniform(50, 60)
        self.__env_values["mars_base_external_illuminance"] = random.uniform(500, 715)
        self.__env_values["mars_base_internal_co2"] = random.uniform(0.02, 0.1)
        self.__env_values["mars_base_internal_oxygen"] = random.uniform(4, 7)

    def get_env(self):
        year = 2025
        month = random.randint(1, 12)
        if month in (1, 3, 5, 7, 8, 10, 12):
            day = random.randint(1, 31)
        elif month in (4, 6, 9, 11):
            day = random.randint(1, 30)
        else:
            day = random.randint(1, 28)

        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        timestamp = f"{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}"

        log_line = (
            f"{timestamp}\n"
            f"mars_base_internal_temperature : {self.__env_values['mars_base_internal_temperature']:.2f}°C\n"
            f"mars_base_external_temperature : {self.__env_values['mars_base_external_temperature']:.2f}°C\n"
            f"mars_base_internal_humidity : {self.__env_values['mars_base_internal_humidity']:.2f}%\n"
            f"mars_base_external_illuminance : {self.__env_values['mars_base_external_illuminance']:.2f} W/m²\n"
            f"mars_base_internal_co2 : {self.__env_values['mars_base_internal_co2']:.4f}%\n"
            f"mars_base_internal_oxygen : {self.__env_values['mars_base_internal_oxygen']:.2f}%\n"
        )

        # 로그 파일 저장
        if not os.path.exists('codyssey03'):
            os.makedirs('codyssey03')

        with open("codyssey03/sensor_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(log_line)

        return self.__env_values


class MissionComputer:

    def __init__(self):
        self.setting_path = 'codyssey05/setting.txt'
        self.setting = self.load_settings()

    def load_settings(self):
        settings = {
            'os': True,
            'os_version': True,
            'cpu_type': True,
            'cpu_cores': True,
            'memory_total': True,
            'cpu_usage': True,
            'memory_usage': True
        }

        if not os.path.exists('codyssey05'):
            os.makedirs('codyssey05')

        if not os.path.exists(self.setting_path):
            try:
                with open(self.setting_path, 'w', encoding='utf-8') as f:
                    for key in settings:
                        f.write(f'{key}=true\n')
            except Exception as e:
                print('setting.txt 생성 실패:', e)
                return settings

        try:
            with open(self.setting_path, 'r', encoding='utf-8') as f:
                for line in f:
                    key_value = line.strip().split('=')
                    if len(key_value) == 2:
                        key, value = key_value
                        if key in settings:
                            settings[key] = value.strip().lower() == 'true'
        except Exception as e:
            print('설정 파일 읽기 오류:', e)

        return settings

    def get_mission_computer_info(self):
        info = {}

        if psutil is None:
            info['Error'] = 'psutil 모듈이 설치되지 않았습니다.'
            print(json.dumps(info, indent=2, ensure_ascii=False))
            return

        try:
            if self.setting['os']:
                info['Operating System'] = platform.system()

            if self.setting['os_version']:
                info['OS Version'] = platform.version()

            if self.setting['cpu_type']:
                info['CPU Type'] = platform.processor()

            if self.setting['cpu_cores']:
                info['CPU Cores'] = os.cpu_count()

            if self.setting['memory_total']:
                memory = psutil.virtual_memory()
                info['Total Memory (MB)'] = round(memory.total / (1024 * 1024), 2)
        except Exception as e:
            info['Error'] = str(e)

        print(json.dumps(info, indent=2, ensure_ascii=False))

    def get_mission_computer_load(self):
        load = {}

        if psutil is None:
            load['Error'] = 'psutil 모듈이 설치되지 않았습니다.'
            print(json.dumps(load, indent=2, ensure_ascii=False))
            return

        try:
            if self.setting['cpu_usage']:
                load['CPU Usage (%)'] = psutil.cpu_percent(interval=1)

            if self.setting['memory_usage']:
                memory = psutil.virtual_memory()
                load['Memory Usage (%)'] = memory.percent
        except Exception as e:
            load['Error'] = str(e)

        print(json.dumps(load, indent=2, ensure_ascii=False))


# 실행부
if __name__ == "__main__":
    print('--- 센서 로그 ---')
    ds = DummySensor()
    ds.set_env()
    env_data = ds.get_env()

    for key, value in env_data.items():
        print(f"{key}: {value:.4f}")

    print('\n--- 시스템 정보 ---')
    runComputer = MissionComputer()
    runComputer.get_mission_computer_info()

    print('\n--- 시스템 부하 ---')
    runComputer.get_mission_computer_load()