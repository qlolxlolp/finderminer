import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging
from datetime import datetime
import json
from pathlib import Path
from .utils import format_frequency, timestamp_to_str

class AlertSystem:
    def __init__(self, config):
        """Initialize AlertSystem with configuration."""
        self.logger = logging.getLogger('CryptoMinerDetector')
        self.config = config
        self.smtp_config = config['alert']['smtp']
        self.alert_history = []
        self.alert_callbacks = []
    
    def register_callback(self, callback):
        """Register a callback function for alerts."""
        self.alert_callbacks.append(callback)
    
    def send_alert(self, detection_data, report_path=None):
        """Send alert about detected suspicious signal."""
        try:
            # Create alert record
            alert = {
                'timestamp': timestamp_to_str(),
                'detection': detection_data,
                'report_path': str(report_path) if report_path else None
            }
            self.alert_history.append(alert)
            
            # Send email alert
            self._send_email_alert(alert, report_path)
            
            # Trigger callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {str(e)}")
            return False
    
    def _send_email_alert(self, alert, report_path=None):
        """Send email alert with detection details."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = 'هشدار: شناسایی سیگنال مشکوک ماینر'
            msg['From'] = self.smtp_config['sender']
            msg['To'] = ', '.join(self.smtp_config['recipients'])
            
            # Create message body
            body = self._create_alert_body(alert)
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Attach report if available
            if report_path and Path(report_path).exists():
                with open(report_path, 'rb') as f:
                    report = MIMEApplication(f.read(), _subtype='pdf')
                    report.add_header('Content-Disposition', 'attachment', 
                                    filename='report.pdf')
                    msg.attach(report)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['server'], 
                            self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['sender'], 
                           self.smtp_config['password'])
                server.send_message(msg)
            
            self.logger.info("Alert email sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def _create_alert_body(self, alert):
        """Create HTML body for alert email."""
        detection = alert['detection']
        
        # Create frequency list
        freq_list = '<br>'.join([
            f"• فرکانس: {format_frequency(freq)}, "
            f"قدرت: {power:.2f} dB"
            for freq, power in zip(detection['frequencies'], detection['powers'])
        ])
        
        body = f"""
        <div dir="rtl" style="font-family: Arial, sans-serif;">
            <h2>هشدار: شناسایی سیگنال مشکوک ماینر</h2>
            
            <p>در تاریخ {alert['timestamp']} سیگنال‌های مشکوک زیر شناسایی شدند:</p>
            
            <div style="margin: 20px 0;">
                {freq_list}
            </div>
            
            <p>سطح اطمینان تشخیص: {detection['confidence']*100:.1f}%</p>
            
            <hr>
            
            <p style="color: #666; font-size: 0.9em;">
                این هشدار به صورت خودکار توسط سیستم شناسایی سیگنال ماینر ارسال شده است.
                {f'گزارش کامل در فایل پیوست موجود است.' if alert['report_path'] else ''}
            </p>
        </div>
        """
        
        return body
    
    def get_alert_history(self):
        """Return list of previous alerts."""
        return self.alert_history
    
    def clear_alert_history(self):
        """Clear alert history."""
        self.alert_history = []
    
    def save_alert_history(self, filepath):
        """Save alert history to JSON file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving alert history: {str(e)}")
            return False
    
    def load_alert_history(self, filepath):
        """Load alert history from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.alert_history = json.load(f)
            return True
        except Exception as e:
            self.logger.error(f"Error loading alert history: {str(e)}")
            return False
