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


LARGE_FONT = ("Verdana", 12)
data = {}
for name in ("cpu_usage", "cpu_freq", "mem_usage", "disk_usage", "time", "network_data", "network_in", "network_out"):
    data[name] = collections.deque(maxlen=5)
data["old_network_value"] = 0


def get_network_usage():
    new_value = psutil.net_io_counters(nowrap=True).bytes_sent + psutil.net_io_counters(nowrap=True).bytes_recv
    net_usage = (new_value - data["old_network_value"]) / 1024.0 * 8
    return net_usage, new_value

def update_data(data_type = "all"):
    if (len(data["time"]) > 0 and datetime.datetime.now() > data["time"][-1] + datetime.timedelta(0, 1)) or data_type == "all":
        data["time"].append(datetime.datetime.now())
    if data_type == "cpu_usage" or data_type == "all":
        data["cpu_usage"].append(psutil.cpu_percent())
    if data_type == "cpu_freq" or data_type == "all":
        data["cpu_freq"].append(psutil.cpu_freq().current)
    if data_type == "mem_usage" or data_type == "all":
        data["mem_usage"].append(psutil.virtual_memory().percent)
    if data_type == "network_data" or data_type == "all":
        (current_net_usage, new_network_usage) = get_network_usage()
        data["network_data"].append(current_net_usage)
        data["old_network_value"] = new_network_usage

class GraphFrame(tk.Frame):
    def __init__(self, parent, color, title, label, ylim, ylabel, data_type):
        self.color = color
        self.title = title
        self.label = label

        self.ylim = ylim
        self.ylabel = ylabel
        self.data_type = data_type

        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text=self.title, font=LARGE_FONT)
        label.pack(pady=10, padx=10, side='top')


        self.fig = plt.figure()
        self.ax = self.fig.add_subplot()

        ax_format = mdates.DateFormatter('%H:%M:%S')
        self.ax.xaxis.set_major_formatter(ax_format)
        print(f'{data["time"]} and {data[self.data_type]}')
        self.plot = self.ax.plot(data["time"], data[self.data_type], color = self.color, label=self.label, linestyle = 'solid', linewidth = 3)[0]
        self.ax.set_ylim(0, ylim)


        self.ax.set_xlabel('Time')
        self.ax.set_ylabel(self.ylabel)
        self.ax.legend(loc='upper left')

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        #creating matplotlib toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()

        # button1 = ttk.Button(self, text="Back",
        #                      command=lambda: controller.show_frame(StartPage))
        # button1.pack(side='bottom')
        #place the canvas on the tkinter window
        self.canvas.get_tk_widget().pack(side='top', fill=tk.BOTH, expand=True)


    def animate(self):
        # while True:
        update_data(self.data_type)

        # print(f'time: {self.time_data}; cpu_usage: {self.cpu_usage_data}')
        self.plot.set_xdata(data["time"])
        self.plot.set_ydata(data[self.data_type])


        self.ax.set_xlim(data["time"][0],data["time"][-1])
        if self.ylim != 100:
            self.ax.set_ylim(0, max(data[self.data_type])+1000)

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

class ScrollableFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        # Canvas for scrolling
        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        # Update scroll region when resizing
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        # Create window inside canvas
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")



root = tk.Tk()
root.title('ResMon')
root.geometry('{}x{}'.format(1200, 600))
root.resizable(False, False)
# root.pack_propagate(False)

scrollable_frame = ScrollableFrame(root)
scrollable_frame.pack(side="top", fill="both", expand=True)


for _ in range(0, 5):
    update_data()
    time.sleep(1)

cpu_graph = GraphFrame(scrollable_frame.scrollable_frame, "blue", "CPU USAGE", "CPU USAGE", 100, "CPU USAGE (%)", "cpu_usage")
cpu_graph.grid(row=0, column=0, pady=20, sticky='ew')
cpu_graph.animate()

mem_graph = GraphFrame(scrollable_frame.scrollable_frame, "orange", "CPU USAGE", "CPU USAGE", 100, "CPU USAGE (%)", "mem_usage")
mem_graph.grid(row=1, column=0, pady=20, sticky='ew')
mem_graph.animate()


# graph_frame.pack(fill=tk.BOTH, expand=True)
# graph_frame.animate()
root.mainloop()
