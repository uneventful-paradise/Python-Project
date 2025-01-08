import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import collections
import datetime
import tkinter as tk
import json



# plt.style.use('seaborn-v0_8-whitegrid')
plt.style.use("dark_background")
LARGE_FONT = ("Verdana", 12)
MAX_LENGTH = 5
data = {}
for name in (
    "time",
    "cpu_usage",
    "cpu_freq",
    "mem_usage",
    "disk_usage",
    "network_data",
    "network_in",
    "network_out",
    "IO_out",
    "IO_in",
):
    data[name] = collections.deque(maxlen=MAX_LENGTH)

data["old_network_value"] = 0
data["old_tx"] = 0
data["old_rx"] = 0
JPEG_CNT = 0
PDF_CNT = 0


def get_network_usage():
    """Calculate and return current network usage.

    Returns:
        tuple: A tuple containing:
         - net_usage (float): Network usage in kilobits per second.
         - new_value (int): Total bytes sent and received.
         - tx (int): Current bytes sent.
         - rx (int): Current bytes received.
    """
    tx = psutil.net_io_counters(nowrap=True).bytes_sent
    rx = psutil.net_io_counters(nowrap=True).bytes_recv
    new_value = rx + tx
    net_usage = (new_value - data["old_network_value"]) / 1024 * 8
    return net_usage, new_value, tx, rx


def get_io_usage():
    """Calculate and update disk I/O usage."""
    bytes_sent = round(psutil.disk_io_counters().read_bytes / 1024**2, 2)
    bytes_recv = round(psutil.disk_io_counters().write_bytes / 1024**2, 2)
    if len(data["IO_in"]) == 0:
        data["IO_in"].append(bytes_recv)
        data["IO_out"].append(bytes_sent)
    else:
        data["IO_in"].append(bytes_recv - data["IO_in"][-1])
        data["IO_out"].append(bytes_sent - data["IO_out"][-1])


def update_data():
    """Get and update system data in real-time."""

    data["time"].append(datetime.datetime.now())

    data["cpu_usage"].append(psutil.cpu_percent())

    data["cpu_freq"].append(psutil.cpu_freq().current)

    data["mem_usage"].append(psutil.virtual_memory().percent)

    (current_net_usage, new_network_usage, tx, rx) = get_network_usage()
    data["network_data"].append(current_net_usage)
    data["network_in"].append((rx - data["old_rx"]) / 1024 * 8)
    data["network_out"].append((tx - data["old_tx"]) / 1024 * 8)

    data["old_network_value"] = new_network_usage
    data["old_tx"] = tx
    data["old_rx"] = rx

    get_io_usage()

    data["disk_usage"].append(psutil.disk_usage("/").percent)


def write_json_data(filename, write_data):
    """Write logged data to a JSON file.

    Args:
      filename (str): The log file to write to.
      write_data (dict): Log data to be written.
    """
    try:
        with open(filename, "a") as f:
            json.dump(write_data, f)
            f.write("\n")
            f.flush()
    except OSError:
        print("Could not open/write file:", filename)


def log_data(filename):
    """Append current system resource data to a log file.

    Args:
        filename (str): The file to append data to.
    """
    current_data = dict()
    for key in data:
        try:
            if key == "time":
                current_data[key] = data[key][-1].strftime("%Y-%m-%d %H:%M:%S")
            elif key in ("old_network_value", "old_tx", "old_rx"):
                current_data[key] = data[key]
            else:
                current_data[key] = data[key][-1]
        except IndexError:
            current_data[key] = 0
    write_json_data(filename, current_data)


def read_data(filename, time_offset, y_data):
    """Read and filter logged data based on a time offset.

    Args:
       filename (str): Log file to read.
       time_offset (timedelta): Time offset to filter data.
       y_data (list): Data keys to retrieve.

    Returns:
       dict: Filtered data.
    """
    temp_data = {}
    for key in y_data:
        temp_data[key] = []
    temp_data["time"] = []
    try:
        with open(filename, "r") as f:
            # offset = datetime.timedelta(seconds=time_offset)
            content = f.readlines()
            for line in content:
                try:
                    entry = json.loads(line)
                    entry_date = datetime.datetime.strptime(
                        entry["time"], "%Y-%m-%d %H:%M:%S"
                    )
                    if (
                        entry_date + time_offset
                        > datetime.datetime.now() - datetime.timedelta(seconds=1)
                    ):
                        print(json.dumps(entry, indent=4))
                        temp_data["time"].append(entry_date)
                        for key in y_data:
                            temp_data[key].append(entry[key])
                        # print(json.dumps(temp_data, indent=4))
                except (json.JSONDecodeError, KeyError):
                    print("Skipping invalid or incomplete entry.")
    except FileNotFoundError:
        print("Log file not found.")

    return temp_data


def plot_history(offset, graph, resize_y_axis=True):
    """Plot past data.

    Args:
       offset (timedelta): Time offset for plotting.
       graph (GraphFrame): Graph object whose set attributes will help build the new plot.
       resize_y_axis (bool, optional): Resize the y-axis to make plots more easily readable. Defaults to True.
    """
    temp_data = read_data("log_file.txt", offset, graph.legend)
    x_data = temp_data["time"]
    y_data = []
    for key in temp_data:
        if key != "time":
            y_data.append(temp_data[key])
    new_y_lim = 0
    for y in y_data:
        new_y_lim = max(new_y_lim, max(y))
    if resize_y_axis and graph.y_data_lim != 100:
        visualize_log(
            graph.plot_color,
            new_y_lim,
            graph.y_data_label,
            x_data,
            y_data,
            graph.legend,
            graph.line_styles,
        )
    else:
        visualize_log(
            graph.plot_color,
            graph.y_data_lim,
            graph.y_data_label,
            x_data,
            y_data,
            graph.legend,
            graph.line_styles,
        )


def visualize_log(
    plot_color, y_data_lim, y_data_label, x_data, y_data, legend, line_styles
):
    """Create and display a new window with plotted past data.

    Args:
       plot_color (str): Color of the plot line.
       y_data_lim (int): Upper limit for the y-axis.
       y_data_label (str): Label for the y-axis.
       x_data (list): List of datetime objects for the x-axis.
       y_data (list): List of lists of data for the y-axis.
       legend (list): List of legend labels. Also names y_data keys
       line_styles (list): List of line styles for each plot line.
    """
    window = tk.Toplevel(master=root)
    window.title(f"Log History of {legend[0]} plot")
    window.geometry("900x600")

    history = GraphFrame(
        window,
        plot_color,
        y_data_lim,
        y_data_label,
        x_data,
        y_data,
        legend,
        line_styles,
    )
    history.pack()


class GraphFrame(tk.Frame):
    """A tkinter frame that embeds a matplotlib plot for displaying resource data.

    Attributes:
        plot_color (str): Color of the plot line.
        y_data_lim (int): Upper limit for the y-axis.
        y_data_label (str): Label for the y-axis.
        x_data (list): X-axis data (datetime).
        y_data (list): Y-axis data (resource values).
        legend (list): Plot legend labels. Also names y_data keys
        line_styles (list): Line styles for each plot.
    """

    def __init__(
        self,
        parent_frame,
        plot_color,
        y_data_lim,
        y_data_label,
        x_data,
        y_data,
        legend,
        line_styles,
    ):
        """Initialize the GraphFrame.

        Args:
          parent_frame (tk.Frame): Parent tkinter frame.
          plot_color (str): Color of the plot.
          y_data_lim (int): Y-axis limit.
          y_data_label (str): Label for the y-axis.
          x_data (deque): X-axis data (time).
          y_data (list): Y-axis data.
          legend (list): Plot legend. Also names y_data keys
          line_styles (list): Line styles for each plot line.
        """
        self.plot_color = plot_color

        self.y_data_lim = y_data_lim
        self.y_data_label = y_data_label
        self.y_data = y_data
        self.x_data = x_data

        self.line_styles = line_styles
        self.legend = legend
        # plot list for every y_data sets
        self.plots = []

        tk.Frame.__init__(self, parent_frame, bg="#676767")
        self.title_label = tk.Label(
            self,
            text=f'{self.y_data_label.replace("_", " ")}',
            font="Helvetica 18 bold",
            background="#676767",
        )
        self.title_label.pack(pady=10, padx=10, side="top")

        self.fig = plt.figure()
        self.fig.set_size_inches(10, 6, forward=True)
        self.ax = self.fig.add_subplot()

        ax_format = mdates.DateFormatter("%H:%M:%S")
        self.ax.xaxis.set_major_formatter(ax_format)
        # plot every y_data set and add it to the plot list
        for t in zip(self.y_data, self.line_styles):
            self.plots.append(
                self.ax.plot(
                    self.x_data,
                    t[0],
                    color=self.plot_color,
                    linestyle=t[1],
                    linewidth=3,
                )[0]
            )
        self.ax.set_ylim(0, y_data_lim)

        self.ax.set_xlabel("Time")
        self.ax.set_ylabel(self.y_data_label)
        self.ax.legend(self.plots, self.legend, loc="upper left")

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        # creating matplotlib toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()

        # place the canvas on the tkinter window
        self.canvas.get_tk_widget().pack(side="top", fill=tk.BOTH, expand=True)

    def animate(self):
        """Get latest data and redraw the graphs"""
        # update_data(self.data_type)
        for t in zip(self.plots, self.y_data):
            t[0].set_xdata(self.x_data)
            t[0].set_ydata(t[1])

        self.ax.set_xlim(self.x_data[0], self.x_data[-1])
        if self.y_data_lim != 100:
            max_y_val = self.y_data_lim
            for y in self.y_data:
                max_y_val = max(max_y_val, max(y))
            self.ax.set_ylim(0, max_y_val + 0.2 * max_y_val)
            # self.y_data_lim = max_y_val

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        self.canvas.draw_idle()  # redraw plot
        # time.sleep(0.5)
        # sau cu animate
        # self.after(1000, self.animate)


class GraphManager:
    """Update all graphs every second to create an animation

    Attributes:
      graphs (list): List of GraphFrame objects to manage.
      log_file (str): Path to the log file for saving resource data.
    """

    def __init__(self, graphs, log_file):
        """Initialize the GraphManager.

        Args:
          graphs (list): List of GraphFrame objects to manage.
          log_file (str): Log file path for data recording.
        """
        self.graphs = graphs
        self.log_file = log_file
        self.update_all_data()

    def update_all_data(self):
        """Update data for all graphs and start logging process."""
        update_data()  # Update all data at once
        for graph in self.graphs:
            graph.animate()
        log_data(self.log_file)
        root.after(1000, self.update_all_data)


class ScrollableFrame(tk.Frame):
    """A scrollable tkinter frame to hold multiple graphs.

    Attributes:
        canvas(tk.Canvas): Canvas object for drawing graphs.
        scrollbar(tk.Scrollbar): Scrollbar object to be displayed on the side of the screen.
        scrollable_frame(tk.Frame): ScrollableFrame object to hold the canvas.
    """

    def __init__(self, parent):
        """Initialize the ScrollableFrame.

        Args:
           parent (tk.TK): Parent tkinter widget.
        """
        tk.Frame.__init__(self, parent)
        #https://stackoverflow.com/questions/73095063/adding-a-scrollbar-to-a-canvas-with-figures-tkinter
        #https://stackoverflow.com/questions/69934460/how-i-can-add-scrollbar-in-frame-tkinter-python
        self.canvas = tk.Canvas(self, bg="light green")
        self.scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg="pink")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        window_id = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.bind(
            "<Configure>", lambda e: self.canvas.itemconfig(window_id, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")


class ButtonFrame:
    """Frame for buttons to save and plot historical data.

    Attributes:
        base_frame (tk.Frame): Frame object to hold the button frames.
        left_frame (tk.Frame): Frame object to hold the left button.
        right_frame (tk.Frame): Frame object to hold the right button and spinboxes.
        png_save_button (tk.Button): Button to trigger saving function for the png.
        pdf_save_button (tk.Button): Button to trigger saving function for the pdf.
        graph (GraphFrame): The graph associated with the button actions.
        sec_var (tk.IntVar): Variable to store the offset seconds
        min_var (tk.IntVar): Variable to store the offset minutes
        hr_var (tk.IntVar): Variable to store the offset hours
        sec_spinbox (tk.Spinbox): Spinbox object to set the offset seconds
        min_spinbox (tk.Spinbox): Spinbox object to set the offset minutes
        hr_spinbox (tk.Spinbox): Spinbox object to set the offset hours
        sec_label (tk.Label): Label object to show the sec_spinbox
        min_label (tk.Label): Label object to show the min_spinbox
        hr_label (tk.Label): Label object to indicate the hr_spinbox
    """

    def __init__(self, parent, graph):
        """Initialize the ButtonFrame.

        Args:
           parent (tk.Widget): Parent tkinter widget.
           graph (GraphFrame): The graph associated with this button frame.
        """
        self.base_frame = tk.Frame(parent, height=50)
        self.base_frame.pack(side="top", fill="x")
        self.left_frame = tk.Frame(self.base_frame, bg="#676767")
        self.right_frame = tk.Frame(self.base_frame, bg="#676767")

        self.graph = graph

        self.left_frame.pack(side="left", fill="both", expand=True)
        self.right_frame.pack(side="right", fill="both", expand=True)
        self.png_save_button = tk.Button(
            self.left_frame,
            text="Save as JPEG",
            bg="#3f3f3f",
            fg="white",
            command=self.save_current_plot_as_jpeg,
        )
        self.png_save_button.pack(side="right", padx=10, pady=10)
        self.pdf_save_button = tk.Button(
            self.right_frame,
            text="Save as PDF",
            bg="#3f3f3f",
            fg="white",
            command=self.save_current_plot_as_pdf,
        )
        self.pdf_save_button.pack(side="left", padx=10, pady=10)
        # https://stackoverflow.com/questions/66510020/select-date-range-with-tkinter

        self.sec_var = tk.IntVar()
        self.min_var = tk.IntVar()
        self.hr_var = tk.IntVar()
        # sau entry
        self.hr_spinbox = tk.Spinbox(
            self.right_frame, from_=0, to=100, textvariable=self.hr_var, width=3
        )
        self.hr_spinbox.pack(side="left", padx=10, pady=10)
        self.hr_label = tk.Label(self.right_frame, text="Hr", bg="#676767", fg="white")
        self.hr_label.pack(side="left", padx=0, pady=10)

        self.min_spinbox = tk.Spinbox(
            self.right_frame, from_=0, to=59, textvariable=self.min_var, width=3
        )
        self.min_spinbox.pack(side="left", padx=10, pady=10)
        self.min_label = tk.Label(
            self.right_frame, text="Min", bg="#676767", fg="white"
        )
        self.min_label.pack(side="left", padx=0, pady=10)

        self.sec_spinbox = tk.Spinbox(
            self.right_frame, from_=0, to=59, textvariable=self.sec_var, width=3
        )
        self.sec_spinbox.pack(side="left", padx=10, pady=10)
        self.sec_label = tk.Label(
            self.right_frame, text="Sec", bg="#676767", fg="white"
        )
        self.sec_label.pack(side="left", padx=0, pady=10)

        # time_label = ttk.Label(right_frame, textvariable=time_spinvar)
        # time_label.pack(side='left', padx=10, pady=10)

        self.sec_spinbox.bind("<Return>", self.send_offset)
        self.min_spinbox.bind("<Return>", self.send_offset)
        self.hr_spinbox.bind("<Return>", self.send_offset)

    def send_offset(self, event):
        """Calculate time offset input and start the history plot creation.

        This method reads the offset from the spinboxes and generates
        the corresponding historical plot.

        Args:
            event (tk.Event): Event object (triggered by <Return> key).
        """
        # entry -> entry.get()
        offset = datetime.timedelta(
            seconds=self.sec_var.get(),
            minutes=self.min_var.get(),
            hours=self.hr_var.get(),
        )
        self.sec_var.set(0)
        self.min_var.set(0)
        self.hr_var.set(0)
        plot_history(offset, self.graph)

    def save_current_plot_as_pdf(self):
        """Save the current graph as a PDF file.

        The filename is dynamically generated based on the graph's label.
        """
        global PDF_CNT
        new_file_name = self.graph.y_data_label.replace("/s", "").replace("(%)", "").replace("/", "_")
        self.graph.fig.savefig(f"{new_file_name}{PDF_CNT}.pdf", format="pdf")
        print(f"saved figure {PDF_CNT} as pdf")
        plt.close(self.graph.fig)
        PDF_CNT += 1

    def save_current_plot_as_jpeg(self):
        """Save the current graph as a JPEG file.

        The filename is dynamically generated based on the graph's label.
        """
        global JPEG_CNT
        new_file_name = self.graph.y_data_label.replace("/s", "").replace("(%)", "").replace("/", "_")
        self.graph.fig.savefig(f"{new_file_name}{JPEG_CNT}.jpeg", format="jpeg")
        print(f"saved figure {JPEG_CNT} as jpeg")
        plt.close(self.graph.fig)
        JPEG_CNT += 1


root = tk.Tk()
root.title("ResMon")
root.geometry("{}x{}".format(1200, 600))
# root.resizable(False, False)

scrollable_frame = ScrollableFrame(root)
scrollable_frame.pack(side="top", fill="both", expand=True)

update_data()
update_data()

cpu_graph = GraphFrame(
    scrollable_frame.scrollable_frame,
    "blue",
    100,
    "CPU USAGE (%)",
    data["time"],
    [data["cpu_usage"]],
    ["cpu_usage"],
    ["solid"],
)
cpu_graph.pack(side="top", fill="both", expand=True)
cpu_button_frame = ButtonFrame(scrollable_frame.scrollable_frame, cpu_graph)

mem_graph = GraphFrame(
    scrollable_frame.scrollable_frame,
    "orange",
    100,
    "MEMORY USAGE (%)",
    data["time"],
    [data["mem_usage"]],
    ["mem_usage"],
    ["solid"],
)
mem_graph.pack(side="top", fill="both", expand=True)
mem_button_frame = ButtonFrame(scrollable_frame.scrollable_frame, mem_graph)

# cpu_freq_graph = GraphFrame(scrollable_frame.scrollable_frame, "green",  5000,
#                             "CPU FREQUENCY (Mhz)", ["cpu_freq"], ["solid"])
# cpu_freq_graph.pack(side="top", fill="both", expand=True)
# cpu_freq_button = ButtonFrame(scrollable_frame.scrollable_frame, cpu_freq_graph)

network_data_graph = GraphFrame(
    scrollable_frame.scrollable_frame,
    "pink",
    1000,
    "NETWORK DATA (Kbs/s)",
    data["time"],
    [data["network_data"], data["network_in"], data["network_out"]],
    ["network_data", "network_in", "network_out"],
    ["solid", "dotted", "dashed"],
)
network_data_graph.pack(side="top", fill="both", expand=True)
network_data_button = ButtonFrame(scrollable_frame.scrollable_frame, network_data_graph)

io_data_graph = GraphFrame(
    scrollable_frame.scrollable_frame,
    "red",
    5000,
    "I/O DATA (Mbs)",
    data["time"],
    [data["IO_out"], data["IO_in"]],
    ["IO_out", "IO_in"],
    ["solid", "dotted"],
)
io_data_graph.pack(side="top", fill="both", expand=True)
io_data_button = ButtonFrame(scrollable_frame.scrollable_frame, io_data_graph)

disk_usage_graph = GraphFrame(
    scrollable_frame.scrollable_frame,
    "purple",
    100,
    "DISK USAGE (%)",
    data["time"],
    [data["disk_usage"]],
    ["disk_usage"],
    ["solid"],
)
disk_usage_graph.pack(side="top", fill="both", expand=True)
disk_usage_button = ButtonFrame(scrollable_frame.scrollable_frame, disk_usage_graph)

manager = GraphManager(
    [cpu_graph, mem_graph, network_data_graph, io_data_graph, disk_usage_graph],
    "log_file.txt",
)

root.mainloop()
# read_data("log_file.txt", 6, datetime.datetime.now())