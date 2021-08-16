import speedtest
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import csv

'''
This script is designed to be called on a schedule. It checks the internet speed, 
writes data to the sqlite database, json and csv files for further diagnostics. 
It also generates an html page with 5 latest results.
'''

class SpeedDB():
    def __enter__(self):
        if Path('result_speedtest.db').is_file():
            self.conn = sqlite3.connect('result_speedtest.db')
            self.cur = self.conn.cursor()
        else:
            self.conn = sqlite3.connect('result_speedtest.db')
            self.cur = self.conn.cursor()
            self.cur.execute('''create table speedtest (
                date,
                time,
                ping,
                download,
                upload,
                url unique)''')
            self.conn.commit()
        return self

    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()

    def add_data(self, data):
        query = 'insert into speedtest values (?, ?, ?, ?, ?, ?)'
        self.cur.execute(query, data)
        self.conn.commit()
        return True

    def get_last_data(self):
        query = 'SELECT * FROM speedtest ORDER BY date DESC, time DESC LIMIT 5'
        last_data = self.cur.execute(query).fetchall()
        return last_data


def get_speedtest(host=None):
    servers = None
    # If you want to test against a specific server
    # servers = [1234]

    threads = None
    # If you want to use a single threaded test
    # threads = 1

    s = speedtest.Speedtest()
    s.get_servers(servers)
    s.get_best_server()
    s.download(threads=threads)
    s.upload(threads=threads)
    s.results.share()
    result = s.results.dict()

    return result


def convert_result_speedtest(result_dict):
    """
    Convert dict received from get_speedtest function, to
    {
        date: 2021.02.12
        time: 13:56:26
        ping: 116
        download: 48.75
        upload: 20.09
        url: https://www.speedtest.net/result/10916674697
    }
    """
    def convert_to_mbps(bps):
        return round(bps/1000000, 2)

    def convert_date(_date):
        _date = datetime.strptime(_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        _date = _date.replace(tzinfo=timezone.utc).astimezone(tz=None)
        _date = _date.strftime('%Y.%m.%d %H:%M').split()
        return _date

    date, time = convert_date(result_dict['timestamp'])
    ping = int(result_dict['ping'])
    download = convert_to_mbps(result_dict['download'])
    upload = convert_to_mbps(result_dict['upload'])
    url = result_dict['share'][:-4].replace('http', 'https')
    with SpeedDB() as db:
        db.add_data((date, time, ping, download, upload, url))

    return (date, time, ping, download, upload, url)


def save_result_to_json(result_dict, date, time):
    Path("results").mkdir(parents=True, exist_ok=True)
    with open(f'results/{date}_{time}.json', 'w') as fh:
        json.dump(result_dict, fh, indent=4)


def write_to_csv(convert_result):
    if Path('results/Total.csv').is_file():
        fh = open('results/Total.csv', 'a', newline='')
    else:
        fh = open('results/Total.csv', 'w', newline='')
        writer = csv.writer(fh)
        writer.writerow(('date', 'time', 'ping', 'download', 'upload', 'url'))

    writer = csv.writer(fh)
    writer.writerow(convert_result)
    fh.close()


def make_html():
    head = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
 <head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>Последние результаты проверки speedtest</title>
  <style type="text/css">
    table {
        border: 1px solid #69c;
    }
    th {
        font-weight: normal;
        color: #039;
        border-bottom: 1px dashed #69c;
        padding: 12px 17px;
    }
    td {
        color: #669;
        padding: 7px 17px;
        text-align: center;
    }
    tr:hover td {
        background: #ccddff;
    }
    a {
        color:#669;
        text-decoration:none;
    }
    a:visited{
        color:#669;
    }
  </style>
 </head>
 <body>
  <table>
    <tr>
      <th>Date</th>
      <th>Time</th>
      <th>Ping</th>
      <th>Download</th>
      <th>Upload</th>
      <th>URL</th>
    </tr>'''
    row_template = '''    <tr>
      <td>{0}</td>
      <td>{1}</td>
      <td>{2}</td>
      <td>{3}</td>
      <td>{4}</td>
      <td><a href="{5}" target="_blank">{5}</a></td>
    </tr>'''
    end = '''  </table>
 </body>
</html>'''
    with open('last_result.html', 'w', encoding='utf8') as fh:
        fh.write(head)
        with SpeedDB() as db:
            list_results = db.get_last_data()

        for line in list_results:
            fh.write(row_template.format(*line))
        fh.write(end)


def main():
    result_speedtest = get_speedtest()
    convert_result = convert_result_speedtest(result_speedtest)
    date = convert_result[0].replace('.', '-')
    time = convert_result[1].replace(':', '-')
    save_result_to_json(result_speedtest, date, time)
    write_to_csv(convert_result)
    make_html()


if __name__ == '__main__':
    main()
