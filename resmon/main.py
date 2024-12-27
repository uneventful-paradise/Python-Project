import time
import psutil
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import collections
import datetime
import tkinter as tk
from tkinter import ttk

# Create two subplots and unpack the output array immediately
# f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
# ax1.plot(x, y)
# ax1.set_title('Sharing Y axis')
# ax2.scatter(x, y)
#https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html
# https://www.geeksforgeeks.org/how-to-update-a-plot-on-same-figure-during-the-loop/


#TODO: network montoring
#TODO: split graphs in subgraphs

class ResGraph():
    def __init__(self):
        self.cpu_usage_data = collections.deque(maxlen=5)
        self.cpu_freq_data = collections.deque(maxlen=5)
        self.mem_usage_data = collections.deque(maxlen=5)
        self.time_data = collections.deque(maxlen=5)
        self.update_data()

        self.fig = plt.figure(figsize = (16, 16))
        self.cpu_usage_ax = self.fig.add_subplot(2, 2, 1)
        self.cpu_freq_ax = self.fig.add_subplot(2, 2, 2)
        self.mem_usage_ax = self.fig.add_subplot(2, 2, 3)
        self.network_usage_ax = self.fig.add_subplot(2, 2, 4)


        ax_format = mdates.DateFormatter('%H:%M:%S')
        self.cpu_usage_ax.xaxis.set_major_formatter(ax_format)
        self.cpu_freq_ax.xaxis.set_major_formatter(ax_format)
        self.mem_usage_ax.xaxis.set_major_formatter(ax_format)


        self.cpu_usage_plot = self.cpu_usage_ax.plot(self.time_data, self.cpu_usage_data, color = 'blue', label='CPU USAGE', linestyle = 'solid', linewidth = 3)[0]
        self.mem_usage_plot = self.mem_usage_ax.plot(self.time_data, self.mem_usage_data, color = 'green', label='MEMORY USAGE', linestyle = 'solid', linewidth = 3)[0]
        self.cpu_usage_ax.set_ylim(0, 100)
        self.mem_usage_ax.set_ylim(0, 100)
        # self.percentage_ax.set_xlim(self.time_data[0], self.time_data[-1])


        self.cpu_freq_plot = self.cpu_freq_ax.plot(self.time_data, self.cpu_freq_data, label='CPU Frequency (MHz)', linestyle = 'solid', color='purple', linewidth = 3)[0]
        self.cpu_freq_ax.set_ylim(0, 5000)

        self.cpu_usage_ax.set_xlabel('Time')
        self.cpu_usage_ax.set_ylabel('Usage (%)')
        self.cpu_freq_ax.set_ylabel('Frequency (MHz)')

        self.cpu_usage_ax.legend(loc='upper left')
        self.cpu_freq_ax.legend(loc='upper right')

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
            self.cpu_usage_plot.set_xdata(self.time_data)
            self.cpu_usage_plot.set_ydata(self.cpu_usage_data)

            self.mem_usage_plot.set_xdata(self.time_data)
            self.mem_usage_plot.set_ydata(self.mem_usage_data)

            self.cpu_freq_plot.set_xdata(self.time_data)
            self.cpu_freq_plot.set_ydata(self.cpu_freq_data)

            self.cpu_freq_ax.set_xlim(self.time_data[0], self.time_data[-1])
            self.cpu_usage_ax.set_xlim(self.time_data[0], self.time_data[-1])
            self.mem_usage_ax.set_xlim(self.time_data[0], self.time_data[-1])
            self.network_usage_ax.set_xlim(self.time_data[0], self.time_data[-1])

            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            time.sleep(0.5)
            # self.after(1000, self.animate)

# plt.ion()
# graph = ResGraph()
# graph.animate()


root = tk.Tk()
root.title('ResMon')
root.geometry('{}x{}'.format(1200, 600))
root.resizable(False, False)

cpu_usage_frame = tk.Frame(master=root, bg='grey', height=300)
cpu_usage_frame.grid(row=0, column=0, sticky='ew')
cpu_usage_frame.pack_propagate(False)  # Prevent the frame from resizing to fit its contents

root.grid_columnconfigure(0, weight=1)

# Button that displays the plot
plot_button = tk.Button(master=cpu_usage_frame,
                        height=2,
                        width=10,
                        text="Plot")
plot_button.pack(side='bottom', pady=10)

root.mainloop()
