import random

class DummySensor:
    
    def __init__(self):
        self.env_values ={
            "mars_base_internal_temperature" : None,
            "mars_base_external_temperature" : None,
            "mars_base_internal_humidity" : None,
            "mars_base_external_illuminance" : None,
            "mars_base_internal_co2" : None,
            "mars_base_internal_oxygen" : None
        }
        
    def set_env(self):
        self.env_values["mars_base_internal_temperature"] = random.uniform(18, 30)
        self.env_values["mars_base_external_temperature"] = random.uniform(0, 21)
        self.env_values["mars_base_internal_humidity"] = random.uniform(50, 60)
        self.env_values["mars_base_external_illuminance"] = random.uniform(500, 715)
        self.env_values["mars_base_internal_co2"] = random.uniform(0.02, 0.1)
        self.env_values["mars_base_internal_oxygen"] = random.uniform(4, 7)
        
    def get_env(self):
        year = 2025
        month = random.randint(1, 12)
        if month in (1,3,5,7,8,10,12) :
            day = random.randint(1, 31)
        elif month in (4,6,9,11):
            day = random.randint(1,30)
        else :
            day = random.randint(1,28)  
        hour = random.randint (0,23)
        minute = random.randint (0, 59)
        second = random.randint (0, 59)
        timestamp =  f"{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}"
         
        log_line = (
            f"{timestamp}\n"
            f"mars_base_internal_temperature : {self.env_values['mars_base_internal_temperature']:.2f}°C\n"
            f"mars_base_external_temperature : {self.env_values['mars_base_external_temperature']:.2f}°C\n"
            f"mars_base_internal_humidity : {self.env_values['mars_base_internal_humidity']:.2f}%\n"
            f"mars_base_external_illuminance : {self.env_values['mars_base_external_illuminance']:.2f} W/m²\n"
            f"mars_base_internal_co2 : {self.env_values['mars_base_internal_co2']:.4f}%\n"
            f"mars_base_internal_oxygen : {self.env_values['mars_base_internal_oxygen']:.2f}%\n"
        )

        with open("codyssey03/sensor_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(log_line)

        return self.env_values

if __name__ == "__main__":
    ds = DummySensor()
    ds.set_env()
    env_data = ds.get_env()

    # 확인용 출력
    for key, value in env_data.items():
        print(f"{key}: {value:.4f}")