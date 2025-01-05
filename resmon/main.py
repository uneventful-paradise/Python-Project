import time
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
import matplotlib.dates as mdates
import collections
import datetime
import tkinter as tk
from tkinter import ttk
import tkcalendar
import json
import winstats

# Create two subplots and unpack the output array immediately
# f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
# ax1.plot(x, y)
# ax1.set_title('Sharing Y axis')
# ax2.scatter(x, y)
# https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html
# https://www.geeksforgeeks.org/how-to-update-a-plot-on-same-figure-during-the-loop/
# https://www.geeksforgeeks.org/how-to-embed-matplotlib-charts-in-tkinter-gui/

# TODO: flush problem
# TODO: network graph
# TODO: add disk usage and sent/received network data

# plt.style.use('seaborn-v0_8-whitegrid')
plt.style.use('dark_background')
LARGE_FONT = ("Verdana", 12)
data = {}
for name in ("cpu_usage", "cpu_freq", "mem_usage", "disk_usage", "network_data", "network_in", "network_out",
             "cpu_usage_time", "cpu_freq_time", "mem_usage_time", "disk_usage_time", "network_data_time"):
    data[name] = collections.deque(maxlen=5)
data["old_network_value"] = 0
data["old_tx"] = 0
data["old_rx"] = 0
jpeg_cnt = 0
pdf_cnt = 0


def get_network_usage():
    tx = psutil.net_io_counters(nowrap=True).bytes_sent
    rx = psutil.net_io_counters(nowrap=True).bytes_recv
    new_value = rx + tx
    net_usage = (new_value - data["old_network_value"]) / 1024 * 8
    return net_usage, new_value, tx, rx


def update_data(data_type="all"):
    # if (len(data["time"]) > 0 and datetime.datetime.now() > data["time"][-1] + datetime.timedelta(0, 1)) or data_type == "all":
    #     data["time"].append(datetime.datetime.now())
    if data_type == "cpu_usage" or data_type == "all":
        data["cpu_usage"].append(psutil.cpu_percent())
        data["cpu_usage_time"].append(datetime.datetime.now())
    if data_type == "cpu_freq" or data_type == "all":
        data["cpu_freq"].append(psutil.cpu_freq().current)
        data["cpu_freq_time"].append(datetime.datetime.now())
    if data_type == "mem_usage" or data_type == "all":
        data["mem_usage"].append(psutil.virtual_memory().percent)
        data["mem_usage_time"].append(datetime.datetime.now())
    if data_type == "network_data" or data_type == "all":
        (current_net_usage, new_network_usage, tx, rx) = get_network_usage()
        data["network_data"].append(current_net_usage)
        data["network_in"].append((rx - data["old_rx"]) / 1024 * 8)
        data["network_out"].append((tx - data["old_tx"]) / 1024 * 8)
        data["network_data_time"].append(datetime.datetime.now())
        data["old_network_value"] = new_network_usage
        data["old_tx"] = tx
        data["old_rx"] = rx
    # adding a time array for each graph to avoid sync issues


def write_json_data(filename, write_data):
    try:
        with open(filename, "a") as f:
            json.dump(write_data, f)
            f.write("\n")
            f.flush()
    except OSError:
        print("Could not open/write file:", filename)


def log_data(filename):
    current_data = dict()
    for key in data:
        try:
            if key.endswith("_time"):
                current_data[key] = data[key][-1].strftime("%Y-%m-%d %H:%M:%S")
            elif key in ("old_network_value", "old_tx", "old_rx"):
                current_data[key] = data[key]
            else:
                current_data[key] = data[key][-1]
        except IndexError:
            current_data[key] = 0
    write_json_data(filename, current_data)


def read_data(filename, time_offset):
    try:
        with open(filename, "r") as f:
            # offset = datetime.timedelta(seconds=time_offset)
            content = f.readlines()
            for line in content:
                try:
                    entry = json.loads(line)
                    entry_date = datetime.datetime.strptime(entry["cpu_usage_time"], "%Y-%m-%d %H:%M:%S")
                    if entry_date + time_offset >= datetime.datetime.now():
                        print(json.dumps(entry, indent=4))  # Pretty print filtered entry

                except (json.JSONDecodeError, KeyError):
                    print("Skipping invalid or incomplete entry.")
    except FileNotFoundError:
        print("Log file not found.")


class GraphFrame(tk.Frame):
    def __init__(self, parent_frame, plot_color, y_data_lim, y_data_label, y_data, line_styles):
        self.plot_color = plot_color

        self.y_data_lim = y_data_lim
        self.y_data_label = y_data_label
        self.y_data = y_data
        self.line_styles = line_styles
        # plot list for every y_data sets
        self.plots = []
        # TODO: change to global time variable
        self.time_index = "cpu_usage_time"

        tk.Frame.__init__(self, parent_frame, bg='blue')
        label = tk.Label(self, text=f'{self.y_data} plot', font=LARGE_FONT)
        label.pack(pady=10, padx=10, side='top')

        self.fig = plt.figure()
        self.fig.set_size_inches(10, 6, forward=True)
        self.ax = self.fig.add_subplot()

        ax_format = mdates.DateFormatter('%H:%M:%S')
        self.ax.xaxis.set_major_formatter(ax_format)
        # plot every y_data set and add it to the plot list
        for t in zip(self.y_data, self.line_styles):
            self.plots.append(
                self.ax.plot(data[self.time_index], data[t[0]], color=self.plot_color, linestyle=t[1], linewidth=3)[0])
        self.ax.set_ylim(0, y_data_lim)

        self.ax.set_xlabel('Time')
        self.ax.set_ylabel(self.y_data_label)
        self.ax.legend(self.plots, self.y_data, loc='upper left')

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        # creating matplotlib toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()

        # place the canvas on the tkinter window
        self.canvas.get_tk_widget().pack(side='top', fill=tk.BOTH, expand=True)

    def animate(self):
        # update_data(self.data_type)
        for t in zip(self.plots, self.y_data):
            t[0].set_xdata(data[self.time_index])
            t[0].set_ydata(data[t[1]])

        self.ax.set_xlim(data[self.time_index][0], data[self.time_index][-1])
        if self.y_data_lim != 100:
            max_y_val = 0
            for y in self.y_data:
                max_y_val = max(max_y_val, max(data[y]))
            self.ax.set_ylim(0, max_y_val + 1000)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        self.canvas.draw_idle()  # redraw plot
        # time.sleep(0.5)
        # sau cu animate
        # self.after(1000, self.animate)


class GraphManager:
    def __init__(self, graphs, log_file):
        self.graphs = graphs
        self.log_file = log_file
        self.update_all_data()

    def update_all_data(self):
        update_data("all")  # Update all data at once
        for graph in self.graphs:
            graph.animate()
        log_data(self.log_file)
        root.after(1000, self.update_all_data)


class ScrollableFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        # self.graphs = graphs

        # Canvas for scrolling
        canvas = tk.Canvas(self, bg='light green')
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg='pink')

        # Update scroll region when resizing
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        # Create window inside canvas
        window_id = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(window_id, width=e.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class ButtonFrame():
    def __init__(self, parent_frame, graph):
        self.base_frame = tk.Frame(parent_frame, height=50)
        self.base_frame.pack(side='top', fill='x')
        self.left_frame = tk.Frame(self.base_frame, bg='red')
        self.right_frame = tk.Frame(self.base_frame, bg='red')

        self.graph = graph

        self.left_frame.pack(side='left', fill='both', expand=True)
        self.right_frame.pack(side='right', fill='both', expand=True)
        self.png_save_button = ttk.Button(self.left_frame, text="Save as JPEG", command=self.save_current_plot_as_jpeg)
        self.png_save_button.pack(side='right', padx=10, pady=10)
        self.pdf_save_button = ttk.Button(self.right_frame, text="Save as PDF", command=self.save_current_plot_as_pdf)
        self.pdf_save_button.pack(side='left', padx=10, pady=10)
        # https://stackoverflow.com/questions/66510020/select-date-range-with-tkinter

        self.sec_var = tk.IntVar()
        self.min_var = tk.IntVar()
        self.hr_var = tk.IntVar()
        # sau entry
        self.hr_spinbox = ttk.Spinbox(self.right_frame, from_=0, to=100, textvariable=self.hr_var, width=3)
        self.hr_spinbox.pack(side='left', padx=10, pady=10)
        self.min_spinbox = ttk.Spinbox(self.right_frame, from_=0, to=59, textvariable=self.min_var, width=3)
        self.min_spinbox.pack(side='left', padx=10, pady=10)
        self.sec_spinbox = ttk.Spinbox(self.right_frame, from_=0, to=59, textvariable=self.sec_var, width=3)
        self.sec_spinbox.pack(side='left', padx=10, pady=10)

        # time_label = ttk.Label(right_frame, textvariable=time_spinvar)
        # time_label.pack(side='left', padx=10, pady=10)

        self.sec_spinbox.bind("<Return>", self.send_offset)
        self.min_spinbox.bind("<Return>", self.send_offset)
        self.hr_spinbox.bind("<Return>", self.send_offset)

    def send_offset(self, event):
        # entry -> entry.get()
        offset = datetime.timedelta(seconds=self.sec_var.get(), minutes=self.min_var.get(), hours=self.hr_var.get())
        print("do something:", offset)
        read_data("log_file.txt", offset)

    def save_current_plot_as_pdf(self):
        global pdf_cnt
        self.graph.fig.savefig(f'{self.graph.label}_{pdf_cnt}.pdf', format='pdf')
        print(f"saved figure {pdf_cnt} as pdf")
        plt.close(self.graph.fig)
        pdf_cnt += 1

    def save_current_plot_as_jpeg(self):
        global jpeg_cnt
        self.graph.fig.savefig(f'{self.graph.label}_{jpeg_cnt}.jpeg', format='jpeg')
        print(f"saved figure {jpeg_cnt} as jpeg")
        plt.close(self.graph.fig)
        jpeg_cnt += 1


root = tk.Tk()
root.title('ResMon')
root.geometry('{}x{}'.format(1200, 600))
# root.resizable(False, False)

scrollable_frame = ScrollableFrame(root)
scrollable_frame.pack(side="top", fill="both", expand=True)

update_data()
update_data()

cpu_graph = GraphFrame(scrollable_frame.scrollable_frame, "blue",  100, "CPU USAGE (%)",
                       ["cpu_usage"], ["solid"])
cpu_graph.pack(side="top", fill="both", expand=True)
cpu_button_frame = ButtonFrame(scrollable_frame.scrollable_frame, cpu_graph)

mem_graph = GraphFrame(scrollable_frame.scrollable_frame, "orange", 100,
                       "MEMORY USAGE (%)", ["mem_usage"], ["solid"])
mem_graph.pack(side="top", fill="both", expand=True)
mem_button_frame = ButtonFrame(scrollable_frame.scrollable_frame, mem_graph)

cpu_freq_graph = GraphFrame(scrollable_frame.scrollable_frame, "green",  5000,
                            "CPU FREQUENCY (Mhz)", ["cpu_freq"], ["solid"])
cpu_freq_graph.pack(side="top", fill="both", expand=True)
cpu_freq_button = ButtonFrame(scrollable_frame.scrollable_frame, cpu_freq_graph)

network_data_graph = GraphFrame(scrollable_frame.scrollable_frame,
                                "pink", 1000, "NETWORK DATA (Mbs/s)",
["network_data", "network_in", "network_out"], ["solid", "dotted", "dashed"])
network_data_graph.pack(side="top", fill="both", expand=True)
network_data_button = ButtonFrame(scrollable_frame.scrollable_frame, network_data_graph)

manager = GraphManager([cpu_graph, mem_graph, cpu_freq_graph, network_data_graph], "log_file.txt")

root.mainloop()
# read_data("log_file.txt", 6, datetime.datetime.now())
