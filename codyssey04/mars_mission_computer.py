import time
import json
import threading
import random
import sys

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

class MissionComputer:
    
    def __init__(self):
        self.ds = DummySensor()
        self.env_values = {}
        self.running = True
        self.accumulated_data = {key: [] for key in self.ds.env_values.keys()}

    def get_sensor_data(self):
        count = 0
        last_five_minute = time.time()
        try:
            while self.running:
                self.ds.set_env()
                self.env_values = self.ds.get_env()

                # 5분 누적 데이터 저장
                for key, value in self.env_values.items():
                    self.accumulated_data[key].append(value)

                print(json.dumps(self.env_values, indent=2))
                print("-" * 30)

                count += 1
                time.sleep(5)

                # 5분(60회) 마다 평균 출력
                if time.time() - last_five_minute >= 300:
                    print("=== 5분 평균 환경 데이터 ===")
                    avg_data = {
                        key: sum(values) / len(values)
                        for key, values in self.accumulated_data.items()
                    }
                    print(json.dumps(avg_data, indent=2))
                    print("=" * 30)
                    self.accumulated_data = {key: [] for key in self.env_values.keys()}
                    last_five_minute = time.time()

        except KeyboardInterrupt:
            self.running = False
            print("System stopped...")

def listen_for_stop(mission_computer):
    while mission_computer.running:
        key = input()
        if key.lower() == 'q':
            mission_computer.running = False
            print("System stopped...")

if __name__ == "__main__":
    RunComputer = MissionComputer()

    # 스레드로 키 입력 감지
    stop_thread = threading.Thread(target=listen_for_stop, args=(RunComputer,))
    stop_thread.daemon = True
    stop_thread.start()

    RunComputer.get_sensor_data()
    