import time
import psutil
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import collections
import datetime


class ResGraph():
    def __init__(self):
        self.cpu_usage_data = collections.deque(maxlen=5)
        self.cpu_freq_data = collections.deque(maxlen=5)
        self.mem_usage_data = collections.deque(maxlen=5)
        self.time_data = collections.deque(maxlen=5)
        self.update_data()

        self.fig, self.cpu_ax = plt.subplots()
        myFmt = mdates.DateFormatter('%H:%M:%S')
        self.cpu_ax.xaxis.set_major_formatter(myFmt)
        self.plot = self.cpu_ax.plot(self.time_data, self.cpu_usage_data, label='CPU USAGE')[0]
        self.cpu_ax.set_ylim(0, 100)
        # self.cpu_ax.set_xlim(self.time_data[0], self.time_data[-1])


    def update_data(self):
        self.cpu_usage_data.append(psutil.cpu_percent())
        self.cpu_freq_data.append(psutil.cpu_freq().current)
        self.mem_usage_data.append(psutil.virtual_memory().percent)
        # time_data.append(datetime.datetime.now().strftime("%H:%M:%S"))
        self.time_data.append(datetime.datetime.now())

    def animate(self):
        while True:
            self.update_data()
            print(f'time: {self.time_data}; cpu_usage: {self.cpu_usage_data}')
            self.plot.set_xdata(self.time_data)
            self.plot.set_ydata(self.cpu_usage_data)
            self.cpu_ax.set_xlim(self.time_data[0], self.time_data[-1])
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            time.sleep(0.5)
            # self.after(1000, self.animate)

plt.ion()
graph = ResGraph()
graph.animate()