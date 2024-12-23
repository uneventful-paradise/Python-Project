import time
import psutil
import matplotlib.pyplot as plt
import collections
import datetime

cpu_usage_data = collections.deque(maxlen=5)
cpu_freq_data = collections.deque(maxlen=5)
mem_usage_data = collections.deque(maxlen=5)
time_data = collections.deque(maxlen=5)

def bar_display(cpu_usage, mem_usage, bars=50):
    cpu_percent = (cpu_usage / 100.0)
    mem_percent = (mem_usage / 100.0)
    cpu_bar = '█' * (int(cpu_percent * bars)) + '-'*(bars - int(cpu_percent * bars))
    mem_bar = '█' * (int(mem_percent * bars)) + '-'*(bars - int(mem_percent * bars))
    print(f"CPU USAGE: |{cpu_bar}| {cpu_usage}%")
    print(f"MEM USAGE: |{mem_bar}| {mem_usage}%")
    print("\033[1A\x1b[2K", end="")
    print("\033[1A\x1b[2K", end="")

def update_data():
    cpu_usage_data.append(psutil.cpu_percent())
    cpu_freq_data.append(psutil.cpu_freq().current)
    mem_usage_data.append(psutil.virtual_memory().percent)
    # time_data.append(datetime.datetime.now().strftime("%H:%M:%S"))
    time_data.append(datetime.datetime.timestamp(datetime.datetime.now()))

    # print(cpu_usage_data)
    # print(cpu_freq_data)
    # print(mem_usage_data)

# while True:
#     # print(psutil.cpu_percent())
#     # print(psutil.virtual_memory().percent)
#     # print(psutil.cpu_freq().current)
#
#     # bar_display(psutil.cpu_percent(), psutil.virtual_memory().percent)
#     update_data(psutil.cpu_percent(), psutil.cpu_freq().current, psutil.virtual_memory().percent)
#     time.sleep(1)

plt.ion()
graph = plt.plot(time_data, cpu_usage_data)[0]

for i in range(0, 6):
    update_data()

    graph.set_xdata(time_data)
    graph.set_ydata(cpu_usage_data)

    plt.draw()
    plt.pause(0.01)
    time.sleep(1)

