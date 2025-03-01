import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime
from pathlib import Path
import logging
from .utils import format_frequency, timestamp_to_str
import threading

class DetectorGUI:
    def __init__(self, config, signal_processor, report_generator, alert_system):
        """Initialize the GUI with all components."""
        self.logger = logging.getLogger('CryptoMinerDetector')
        self.config = config
        self.signal_processor = signal_processor
        self.report_generator = report_generator
        self.alert_system = alert_system
        
        self.setup_gui()
        self.setup_plot()
        self.monitoring = False
    
    def setup_gui(self):
        """Set up the main GUI window and components."""
        self.root = tk.Tk()
        self.root.title("سیستم شناسایی سیگنال ماینر")
        self.root.geometry("1200x800")
        
        # Configure Persian font
        font_config = self.config['ui']['font']
        self.font_normal = (font_config['family'], font_config['size']['normal'])
        self.font_title = (font_config['family'], font_config['size']['title'])
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('Persian.TButton', font=self.font_normal)
        self.style.configure('Persian.TLabel', font=self.font_normal)
    
    def _create_header(self):
        """Create header frame with controls."""
        header = ttk.Frame(self.root, padding="10")
        header.grid(row=0, column=0, sticky="ew")
        
        # Title
        title = ttk.Label(header, 
                         text="سیستم شناسایی سیگنال ماینر رمزارز",
                         font=self.font_title)
        title.pack(side=tk.TOP, pady=10)
        
        # Control buttons
        controls = ttk.Frame(header)
        controls.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.start_button = ttk.Button(controls, 
                                     text="شروع پایش",
                                     style='Persian.TButton',
                                     command=self.toggle_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls, 
                  text="شبیه‌سازی سیگنال",
                  style='Persian.TButton',
                  command=self.simulate_signal).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls, 
                  text="تولید گزارش",
                  style='Persian.TButton',
                  command=self.generate_report).pack(side=tk.LEFT, padx=5)
        
        # Frequency input
        freq_frame = ttk.Frame(controls)
        freq_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(freq_frame, 
                 text="فرکانس (MHz):",
                 style='Persian.TLabel').pack(side=tk.LEFT)
        
        self.freq_entry = ttk.Entry(freq_frame, width=10)
        self.freq_entry.pack(side=tk.LEFT, padx=5)
        self.freq_entry.insert(0, "433")
    
    def _create_main_content(self):
        """Create main content area with plot and detection list."""
        main = ttk.Frame(self.root, padding="10")
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)
        
        # Plot frame
        self.plot_frame = ttk.Frame(main)
        self.plot_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        
        # Detections list frame
        list_frame = ttk.Frame(main)
        list_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        ttk.Label(list_frame, 
                 text="سیگنال‌های شناسایی شده",
                 font=self.font_title).pack(side=tk.TOP, pady=5)
        
        # Create detection list
        self.detection_list = ttk.Treeview(list_frame, 
                                         columns=('time', 'freq', 'power', 'conf'),
                                         show='headings')
        
        self.detection_list.heading('time', text='زمان')
        self.detection_list.heading('freq', text='فرکانس')
        self.detection_list.heading('power', text='قدرت')
        self.detection_list.heading('conf', text='اطمینان')
        
        self.detection_list.column('time', width=100)
        self.detection_list.column('freq', width=100)
        self.detection_list.column('power', width=80)
        self.detection_list.column('conf', width=80)
        
        self.detection_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self):
        """Create status bar at bottom of window."""
        self.status_var = tk.StringVar()
        status = ttk.Label(self.root, 
                          textvariable=self.status_var,
                          style='Persian.TLabel',
                          padding="5")
        status.grid(row=2, column=0, sticky="ew")
        self.status_var.set("آماده")
    
    def setup_plot(self):
        """Set up matplotlib plot in GUI."""
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.plot = self.figure.add_subplot(111)
        self.plot.grid(True)
        self.plot.set_xlabel('فرکانس (MHz)')
        self.plot.set_ylabel('قدرت سیگنال (dB)')
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def update_plot(self, fft_result):
        """Update plot with new FFT data."""
        self.plot.clear()
        self.plot.plot(fft_result['frequencies'] / 1e6, fft_result['power'])
        self.plot.grid(True)
        self.plot.set_xlabel('فرکانس (MHz)')
        self.plot.set_ylabel('قدرت سیگنال (dB)')
        self.canvas.draw()
    
    def add_detection(self, detection):
        """Add new detection to the list."""
        for freq, power in zip(detection['frequencies'], detection['powers']):
            self.detection_list.insert('', 'end', values=(
                timestamp_to_str(detection['timestamp']),
                format_frequency(freq),
                f"{power:.2f}",
                f"{detection['confidence']*100:.1f}%"
            ))
    
    def toggle_monitoring(self):
        """Toggle signal monitoring on/off."""
        if not self.monitoring:
            try:
                # Get frequency from input
                freq = float(self.freq_entry.get()) * 1e6  # Convert MHz to Hz
                
                # Initialize SDR
                if not self.signal_processor.initialize_sdr():
                    messagebox.showerror("خطا", 
                                       "خطا در اتصال به دستگاه RTL-SDR")
                    return
                
                # Set frequency
                if not self.signal_processor.set_frequency(freq):
                    messagebox.showerror("خطا", 
                                       "خطا در تنظیم فرکانس")
                    return
                
                # Start processing
                self.signal_processor.start_processing(self.handle_detection)
                self.monitoring = True
                self.start_button.configure(text="توقف پایش")
                self.status_var.set("در حال پایش...")
                
            except ValueError:
                messagebox.showerror("خطا", 
                                   "لطفاً فرکانس معتبر وارد کنید")
        else:
            self.signal_processor.stop_processing()
            self.monitoring = False
            self.start_button.configure(text="شروع پایش")
            self.status_var.set("پایش متوقف شد")
    
    def simulate_signal(self):
        """Simulate miner signal and update display."""
        fft_result = self.signal_processor.simulate_miner_signal()
        self.update_plot(fft_result)
        self.status_var.set("شبیه‌سازی سیگنال انجام شد")
    
    def generate_report(self):
        """Generate and save PDF report."""
        if not self.signal_processor.get_detected_signals():
            messagebox.showwarning("هشدار", 
                                 "هیچ سیگنالی برای گزارش‌گیری یافت نشد")
            return
        
        # Get save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="ذخیره گزارش"
        )
        
        if filename:
            if self.report_generator.generate_report(
                self.signal_processor.get_detected_signals(),
                self.signal_processor.simulate_miner_signal(),  # For visualization
                filename
            ):
                messagebox.showinfo("موفق", 
                                  "گزارش با موفقیت ذخیره شد")
                self.status_var.set("گزارش ذخیره شد")
            else:
                messagebox.showerror("خطا", 
                                   "خطا در ذخیره گزارش")
    
    def handle_detection(self, detection):
        """Handle new signal detection."""
        # Update GUI in thread-safe way
        self.root.after(0, self.add_detection, detection)
        
        # Send alert
        self.alert_system.send_alert(detection)
    
    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()
        
    def cleanup(self):
        """Clean up resources before closing."""
        if self.monitoring:
            self.signal_processor.stop_processing()
        self.root.quit()
