from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import io
from datetime import datetime
import numpy as np
from pathlib import Path
import logging
from .utils import format_frequency, timestamp_to_str

class ReportGenerator:
    def __init__(self, config):
        """Initialize ReportGenerator with configuration."""
        self.logger = logging.getLogger('CryptoMinerDetector')
        self.config = config
        self._register_fonts()
        self.styles = self._create_styles()
        
    def _register_fonts(self):
        """Register Persian fonts for use in PDF."""
        try:
            # Register BNazanin font
            font_path = Path(__file__).parent.parent / 'fonts' / 'BNazanin.ttf'
            pdfmetrics.registerFont(TTFont('BNazanin', str(font_path)))
            self.logger.info("Persian fonts registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering fonts: {str(e)}")
            raise
    
    def _create_styles(self):
        """Create custom styles for the report."""
        styles = getSampleStyleSheet()
        
        # Create Persian text style
        styles.add(ParagraphStyle(
            name='Persian',
            fontName='BNazanin',
            fontSize=12,
            leading=16,
            alignment=1,  # Center alignment
            rightIndent=0,
            leftIndent=0,
        ))
        
        # Create Persian header style
        styles.add(ParagraphStyle(
            name='PersianHeader',
            fontName='BNazanin',
            fontSize=16,
            leading=20,
            alignment=1,
            spaceAfter=30,
            spaceBefore=30,
        ))
        
        return styles
    
    def _create_header(self):
        """Create report header elements."""
        elements = []
        
        # Title
        title = Paragraph("گزارش شناسایی سیگنال‌های ماینر رمزارز", self.styles['PersianHeader'])
        elements.append(title)
        
        # Date and Time
        date_str = timestamp_to_str()
        date_text = Paragraph(f"تاریخ و زمان گزارش: {date_str}", self.styles['Persian'])
        elements.append(date_text)
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _create_signal_table(self, detected_signals):
        """Create table of detected signals."""
        # Table headers
        headers = ['زمان شناسایی', 'فرکانس', 'قدرت سیگنال (dB)', 'سطح اطمینان']
        
        # Table data
        data = [headers]
        for signal in detected_signals:
            for freq, power in zip(signal['frequencies'], signal['powers']):
                row = [
                    timestamp_to_str(signal['timestamp']),
                    format_frequency(freq),
                    f"{power:.2f}",
                    f"{signal['confidence']*100:.1f}%"
                ]
                data.append(row)
        
        # Create table
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'BNazanin'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        return table
    
    def _create_signal_plot(self, fft_result):
        """Create signal plot as an image."""
        buffer = io.BytesIO()
        
        plt.figure(figsize=(8, 4))
        plt.plot(fft_result['frequencies'], fft_result['power'])
        plt.grid(True)
        plt.xlabel('فرکانس (Hz)')
        plt.ylabel('قدرت سیگنال (dB)')
        plt.title('نمودار طیف فرکانسی')
        
        # Save plot to buffer
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create Image object
        buffer.seek(0)
        return Image(buffer, width=6*inch, height=3*inch)
    
    def _create_summary(self, detected_signals):
        """Create summary section of the report."""
        elements = []
        
        # Summary header
        summary_header = Paragraph("خلاصه تحلیل", self.styles['PersianHeader'])
        elements.append(summary_header)
        elements.append(Spacer(1, 10))
        
        # Summary text
        total_signals = len(detected_signals)
        if total_signals > 0:
            max_confidence = max(s['confidence'] for s in detected_signals)
            avg_power = np.mean([p for s in detected_signals for p in s['powers']])
            
            summary_text = f"""
            تعداد کل سیگنال‌های شناسایی شده: {total_signals}<br/>
            بالاترین سطح اطمینان: {max_confidence*100:.1f}%<br/>
            میانگین قدرت سیگنال: {avg_power:.2f} dB
            """
        else:
            summary_text = "هیچ سیگنال مشکوکی شناسایی نشد."
        
        summary = Paragraph(summary_text, self.styles['Persian'])
        elements.append(summary)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def generate_report(self, detected_signals, fft_result, output_path):
        """Generate PDF report with detected signals and analysis."""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=cm,
                leftMargin=cm,
                topMargin=cm,
                bottomMargin=cm
            )
            
            elements = []
            
            # Add header
            elements.extend(self._create_header())
            
            # Add summary
            elements.extend(self._create_summary(detected_signals))
            
            # Add signal plot if available
            if fft_result:
                elements.append(self._create_signal_plot(fft_result))
                elements.append(Spacer(1, 20))
            
            # Add signal table
            if detected_signals:
                elements.append(self._create_signal_table(detected_signals))
            
            # Build PDF
            doc.build(elements)
            self.logger.info(f"Report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            return False
