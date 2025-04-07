import time        
import threading    
import random       

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

def listen_for_stop(mission_computer):
    while mission_computer.running:
        key = input()
        if key.lower() == 'q':
            mission_computer.running = False
            print("System stopped...")

if __name__ == "__main__":
    RunComputer = MissionComputer()
    stop_thread = threading.Thread(target=listen_for_stop, args=(RunComputer,))
    stop_thread.daemon = True
    stop_thread.start()
    RunComputer.get_sensor_data()