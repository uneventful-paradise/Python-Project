import time
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)
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
#https://www.geeksforgeeks.org/how-to-update-a-plot-on-same-figure-during-the-loop/
#https://www.geeksforgeeks.org/how-to-embed-matplotlib-charts-in-tkinter-gui/

#TODO: network montoring
#TODO: split graphs in subgraphs

LARGE_FONT = ("Verdana", 12)

class GraphFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Example of Live Plotting", font=LARGE_FONT)
        label.pack(pady=10, padx=10, side='top')


        self.cpu_usage_data = collections.deque(maxlen=5)
        self.cpu_freq_data = collections.deque(maxlen=5)
        self.mem_usage_data = collections.deque(maxlen=5)
        self.time_data = collections.deque(maxlen=5)
        self.network_data = collections.deque(maxlen=5)
        self.old_network_value = 0
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
        self.network_usage_ax.xaxis.set_major_formatter(ax_format)

        self.cpu_usage_plot = self.cpu_usage_ax.plot(self.time_data, self.cpu_usage_data, color = 'blue', label='CPU USAGE', linestyle = 'solid', linewidth = 3)[0]
        self.mem_usage_plot = self.mem_usage_ax.plot(self.time_data, self.mem_usage_data, color = 'green', label='MEMORY USAGE', linestyle = 'solid', linewidth = 3)[0]
        self.cpu_usage_ax.set_ylim(0, 100)
        self.mem_usage_ax.set_ylim(0, 100)
        # self.percentage_ax.set_xlim(self.time_data[0], self.time_data[-1])


        self.cpu_freq_plot = self.cpu_freq_ax.plot(self.time_data, self.cpu_freq_data, label='CPU Frequency (MHz)', linestyle = 'solid', color='purple', linewidth = 3)[0]
        self.network_usage_plot = self.network_usage_ax.plot(self.time_data, self.network_data, label = 'Network Usage(Kbs/s)', linestyle = 'solid', color='orange', linewidth = 3)[0]
        self.network_usage_ax.set_ylim(0, 5000)
        self.cpu_freq_ax.set_ylim(0, 5000)

        self.cpu_usage_ax.set_xlabel('Time')
        self.cpu_usage_ax.set_ylabel('Usage (%)')
        self.cpu_freq_ax.set_ylabel('Frequency (MHz)')

        self.cpu_usage_ax.legend(loc='upper left')
        self.cpu_freq_ax.legend(loc='upper right')

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        #creating matplotlib toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()

        # button1 = ttk.Button(self, text="Back",
        #                      command=lambda: controller.show_frame(StartPage))
        # button1.pack(side='bottom')
        #place the canvas on the tkinter window
        self.canvas.get_tk_widget().pack(side='top', fill=tk.BOTH, expand=True)
        self.update_data()

    def get_network_usage(self):
        new_value = psutil.net_io_counters(nowrap=True).bytes_sent + psutil.net_io_counters(nowrap=True).bytes_recv
        net_usage = (new_value - self.old_network_value) / 1024.0 * 8
        return (net_usage, new_value)

    def update_data(self):
        self.cpu_usage_data.append(psutil.cpu_percent())
        self.cpu_freq_data.append(psutil.cpu_freq().current)
        self.mem_usage_data.append(psutil.virtual_memory().percent)
        # time_data.append(datetime.datetime.now().strftime("%H:%M:%S"))
        self.time_data.append(datetime.datetime.now())
        (current_net_usage, new_network_usage) = self.get_network_usage()
        self.network_data.append(current_net_usage)
        self.old_network_value = new_network_usage

    def animate(self):
        # while True:
        self.update_data()
        print(f'time: {self.time_data}; cpu_usage: {self.cpu_usage_data}')
        self.cpu_usage_plot.set_xdata(self.time_data)
        self.cpu_usage_plot.set_ydata(self.cpu_usage_data)

        self.mem_usage_plot.set_xdata(self.time_data)
        self.mem_usage_plot.set_ydata(self.mem_usage_data)

        self.cpu_freq_plot.set_xdata(self.time_data)
        self.cpu_freq_plot.set_ydata(self.cpu_freq_data)

        self.network_usage_plot.set_xdata(self.time_data)
        self.network_usage_plot.set_ydata(self.network_data)

        self.cpu_freq_ax.set_xlim(self.time_data[0], self.time_data[-1])
        self.cpu_usage_ax.set_xlim(self.time_data[0], self.time_data[-1])
        self.mem_usage_ax.set_xlim(self.time_data[0], self.time_data[-1])
        self.network_usage_ax.set_xlim(self.time_data[0], self.time_data[-1])
        self.network_usage_ax.set_ylim(0, max(self.network_data)+1000)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        self.canvas.draw_idle()  # redraw plot
        # self.after(10000, self.update_data)  # repeat after 1s
        # time.sleep(0.5)
        #sau cu animate
        self.after(1000, self.animate)



class MainApp(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.grid(row=0, column=0, sticky='ew')
        self.pack_propagate(False)  # Prevent the frame from resizing to fit its contents

        # Button that displays the plot
        self.plot_button = tk.Button(master=self,
                                height=2,
                                width=10,
                                text="Plot")
        self.plot_button.pack(side='bottom', pady=10)


# plt.ion()
# graph = ResGraph()
# graph.animate()


root = tk.Tk()
root.title('ResMon')
root.geometry('{}x{}'.format(1200, 600))
root.resizable(False, False)
root.pack_propagate(False)

# MainApp(root, bg='grey', height=300).pack(side='top', fill='both', expand=False)
graph_frame = GraphFrame(root)
graph_frame.pack(fill=tk.BOTH, expand=True)
graph_frame.animate()
root.mainloop()
