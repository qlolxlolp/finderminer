import numpy as np
import matplotlib.pyplot as plt
from rtlsdr import RtlSdr
from fpdf import FPDF
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# تنظیمات RTL-SDR
sdr = RtlSdr()
sdr.sample_rate = 2.048e6  # نرخ نمونه‌برداری
sdr.center_freq = 100e6  # فرکانس مرکزی
sdr.gain = 'auto'  # تنظیم اتوماتیک تقویت

# شبیه‌سازی سیگنال ماینر
def simulate_miner_signal(freq, duration, sample_rate):
    t = np.arange(0, duration, 1/sample_rate)
    signal = np.sin(2 * np.pi * freq * t)  # سیگنال سینوسی شبیه‌سازی شده
    return signal

# تجزیه و تحلیل سیگنال
def analyze_signal(samples, simulated_signal):
    fft_samples = np.fft.fft(samples)
    fft_simulated = np.fft.fft(simulated_signal)
    
    power_received = np.abs(fft_samples)**2
    power_simulated = np.abs(fft_simulated)**2
    
    suspected_frequencies = []
    threshold = 1000  # آستانه قدرت برای شناسایی سیگنال‌های مشکوک
    
    for i in range(len(power_received)):
        if power_received[i] > threshold:
            suspected_frequencies.append(np.fft.fftfreq(len(power_received), 1/sdr.sample_rate)[i])
    
    return suspected_frequencies

# تولید گزارش PDF
def generate_report(frequencies, file_name="report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", size=12)

    # عنوان گزارش
    pdf.cell(200, 10, txt="گزارش شناسایی سیگنال ماینر", ln=True, align='C')

    # جدول نتایج
    pdf.ln(10)
    pdf.cell(50, 10, txt="فرکانس (Hz)", border=1)
    pdf.cell(50, 10, txt="قدرت", border=1)
    pdf.ln()

    # اضافه کردن داده‌های فرکانسی مشکوک
    for freq in frequencies:
        pdf.cell(50, 10, txt=str(freq), border=1)
        pdf.cell(50, 10, txt="High", border=1)
        pdf.ln()

    # ذخیره فایل PDF
    pdf.output(file_name)

# ارسال هشدار
def send_alert(email, message):
    msg = MIMEText(message)
    msg['Subject'] = "هشدار: شناسایی سیگنال مشکوک ماینر"
    msg['From'] = "your_email@example.com"
    msg['To'] = email

    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login("your_email@example.com", "your_password")
        server.sendmail("your_email@example.com", email, msg.as_string())
        print("هشدار ارسال شد!")

# طراحی رابط کاربری
class MinerSignalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نرم‌افزار شناسایی سیگنال ماینر")
        self.root.geometry("600x400")

        # فونت فارسی
        self.root.option_add("*Font", "BNazanin 12")

        # بخش ورودی فرکانس
        self.label_freq = tk.Label(self.root, text="فرکانس ماینر (Hz):")
        self.label_freq.pack(pady=10)
        self.entry_freq = tk.Entry(self.root)
        self.entry_freq.pack(pady=5)

        # دکمه شروع تحلیل
        self.button_start = tk.Button(self.root, text="شروع تحلیل", command=self.start_analysis)
        self.button_start.pack(pady=20)

        # دکمه ذخیره گزارش
        self.button_save = tk.Button(self.root, text="ذخیره گزارش PDF", command=self.save_report)
        self.button_save.pack(pady=10)

        # نمودار تحلیل سیگنال
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, self.root)
        self.canvas.get_tk_widget().pack(pady=20)

    def start_analysis(self):
        try:
            # دریافت فرکانس از ورودی
            freq = float(self.entry_freq.get())

            # شبیه‌سازی سیگنال ماینر و دریافت سیگنال
            simulated_signal = simulate_miner_signal(freq, 0.01, sdr.sample_rate)
            samples = sdr.read_samples(256*1024)

            # تحلیل سیگنال و پیدا کردن فرکانس‌های مشکوک
            suspected_frequencies = analyze_signal(samples, simulated_signal)

            # نمایش نتایج در نمودار
            self.ax.clear()
            self.ax.plot(np.abs(np.fft.fft(samples)), label="Signal FFT")
            self.ax.set_title("سیگنال‌های رادیویی دریافت شده")
            self.ax.set_xlabel("فرکانس (Hz)")
            self.ax.set_ylabel("قدرت")
            self.canvas.draw()

            # نمایش فرکانس‌های مشکوک
            result_text = "فرکانس‌های مشکوک شناسایی شده:\n"
            result_text += "\n".join([str(freq) for freq in suspected_frequencies])

            messagebox.showinfo("نتیجه تحلیل", result_text)

        except ValueError:
            messagebox.showerror("خطا", "لطفاً فرکانس معتبر وارد کنید.")

    def save_report(self):
        frequencies = self.ax.get_lines()[0].get_xdata()  # استفاده از داده‌های فرکانس از نمودار
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            generate_report(frequencies, file_path)
            messagebox.showinfo("ذخیره سازی", "گزارش با موفقیت ذخیره شد.")

# اجرای برنامه
if __name__ == "__main__":
    root = tk.Tk()
    app = MinerSignalApp(root)
    root.mainloop()
