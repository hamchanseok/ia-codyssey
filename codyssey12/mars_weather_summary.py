import csv
import os
import mysql.connector
import matplotlib.pyplot as plt
from datetime import datetime


class MySQLHelper:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host = host,
            user = user,
            password = password,
            database = database
        )
        self.cursor = self.conn.cursor()

    def create_table(self):
        query = (
            'CREATE TABLE IF NOT EXISTS mars_weather ('
            'weather_id INT AUTO_INCREMENT PRIMARY KEY, '
            'mars_date DATETIME NOT NULL, '
            'temp INT, '
            'storm INT)'
        )
        self.cursor.execute(query)
        self.conn.commit()

    def insert_data(self, mars_date, temp, storm):
        query = 'INSERT INTO mars_weather (mars_date, temp, storm) VALUES (%s, %s, %s)'
        self.cursor.execute(query, (mars_date, temp, storm))
        self.conn.commit()

    def fetch_all_data(self):
        self.cursor.execute('SELECT mars_date, temp FROM mars_weather')
        return self.cursor.fetchall() #fetchall : 레코드를 배열형식으로 저장

    def close(self):
        self.cursor.close()
        self.conn.close()


def read_csv_and_insert(helper, csv_path):
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader) 
        for row in reader:
            mars_date = datetime.strptime(row[1], '%Y-%m-%d')
            temp = int(float(row[2]))  # 예: 21.4 → 21
            storm = int(row[3])
            helper.insert_data(mars_date, temp, storm)


def draw_summary_chart(helper):
    data = helper.fetch_all_data()
    dates = [d[0].strftime('%Y-%m-%d') for d in data]
    temps = [d[1] for d in data]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, temps, marker='o')
    plt.title('Mars Temperature Over Time')
    plt.xlabel('Mars Date')
    plt.ylabel('Temperature')
    plt.xticks(rotation=45)
    plt.tight_layout()

    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mars_temperature_summary.png')
    plt.savefig(save_path)
    print('그래프 저장 완료:', save_path)


def main():
    helper = MySQLHelper(
        host = 'localhost',
        user = 'root',       
        password = '4531',   
        database = 'codyssey'    
    )

    try:
        helper.create_table()
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mars_weathers_data.CSV')
        read_csv_and_insert(helper, csv_path)
        draw_summary_chart(helper)
    finally:
        helper.close()


if __name__ == '__main__':
    main()