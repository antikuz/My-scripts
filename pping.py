import platform
import subprocess
import argparse
import time
import sys
import re
import plotly.graph_objects as go

# The program uses built-in ping tools
# Displays time-stamped responses
# When finished, it will display the chart in the browser


def ping(host_or_ip, packets=1, timeout=1000):
    if platform.system() == 'Windows':
        command = ['ping', '-n', str(packets), '-w', str(timeout), str(host_or_ip)]
        
        # run parameters: capture output, discard error messages, do not show window
        result = subprocess.run(command, capture_output=True)

        if result.returncode == 0 and b'TTL=' in result.stdout:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            text = timestamp + ' ' + result.stdout.decode('cp866').split("\r\n")[2]
            print(text)
            return text
        else:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            text = timestamp + ' ' + result.stdout.decode('cp866').split("\r\n")[2]
            print(text)
            return text
    else:
        print('Linux system is not ready')
        sys.exit()
        
        # command = ['ping', '-c', str(packets), '-w', str(timeout), host_or_ip]
        
        # # run parameters: discard output and error messages
        # result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # return result.returncode == 0

def plot(fh, period=None):
    with open(fh, 'r', encoding='utf8') as result:
        pattern_online = re.compile(r'^(.+?) Ответ.*время.(\d*)мс')
        pattern_offline = re.compile(r'^(.+?) Превышен')
        time_date = []
        time_ms = []
        time_pass = []
        for index, line in enumerate(result):
            if period and index % period != 0:
                continue
            data = re.search(pattern_online, line)
            if data:
                x = int(data.group(2))
                time_date.append(data.group(1))
                time_ms.append(x)
                time_pass.append('')
            else:
                data = re.search(pattern_offline, line)
                time_date.append(data.group(1))
                try:
                    time_ms.append(time_ms[-1])
                except:
                    time_ms.append(0)
                time_pass.append(1)
    maximum = max(time_ms) * 1.10
    
    # Draw ping chart
    trace_comp0 = go.Scattergl(
        x=time_date,
        y=time_ms,
        mode='lines',
        line_shape='hvh',
        line=dict(width=1)
    )

    # Add drop bar
    trace_comp1 = go.Bar(
        x=time_date, 
        y=[maximum if x==1 else '' for x in time_pass],
        hovertemplate =
        '<i>Time</i>: %{x}'+
        '<br>Latency: drop<extra></extra>',
        hoverinfo = 'none',
    )
    
    fig = go.Figure([trace_comp0, trace_comp1])
    fig.update_layout(bargap=0, yaxis=dict(fixedrange=True))
    ip = fh.split()[0].split("\\")[1]
    fig.update_layout(title_text=f'{ip}')
    fig.show()

def main():
    parser = argparse.ArgumentParser(description='Tools to ping with time stamp')
    parser.add_argument(
        "host", 
        help="host or ip (str, address of host to ping)"
    )
    parser.add_argument(
        "-p", 
        "--period", 
        action='store', 
        default=1, 
        type=int,
        help="pause between send packets [default: 1]"
    )
    args = parser.parse_args()
    
    timestamp = time.strftime("%d.%m.%y %H-%M-%S", time.localtime(time.time()))
    fh = f'log\\{args.host} {timestamp}.txt'
    
    with open(fh, 'w', encoding='utf8') as result:
        try:
            while True:
                text = ping(args.host)
                result.write(text + '\n')
                time.sleep(args.period)
        except KeyboardInterrupt:
            input('Catch ctrl-C!, press Enter to exit')
    
    plot(fh, period=args.period)


if __name__ == "__main__":
    sys.exit(main())