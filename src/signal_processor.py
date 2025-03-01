import numpy as np
from rtlsdr import RtlSdr
import logging
from scipy import signal
from datetime import datetime
import threading
from .utils import error_handler, format_frequency, calculate_fft_params

class SignalProcessor:
    def __init__(self, config):
        """Initialize SignalProcessor with configuration."""
        self.logger = logging.getLogger('CryptoMinerDetector')
        self.config = config
        self.sdr = None
        self.running = False
        self.processing_thread = None
        self.callback = None
        self.detected_signals = []
        
        # FFT parameters
        self.fft_params = calculate_fft_params(config)
        self.window = signal.get_window(config['fft']['window'], 
                                      config['fft']['sample_size'])
    
    @error_handler
    def initialize_sdr(self):
        """Initialize the RTL-SDR device."""
        try:
            self.sdr = RtlSdr()
            self.sdr.sample_rate = self.config['rtlsdr']['sample_rate']
            self.sdr.gain = self.config['rtlsdr']['gain']
            self.logger.info("RTL-SDR initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize RTL-SDR: {str(e)}")
            return False
    
    def set_frequency(self, freq):
        """Set the center frequency of RTL-SDR."""
        if self.sdr:
            try:
                self.sdr.center_freq = freq
                self.logger.info(f"Frequency set to {format_frequency(freq)}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to set frequency: {str(e)}")
                return False
    
    def start_processing(self, callback=None):
        """Start signal processing in a separate thread."""
        if self.running:
            return False
        
        self.running = True
        self.callback = callback
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        return True
    
    def stop_processing(self):
        """Stop signal processing."""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
        if self.sdr:
            self.sdr.close()
            self.sdr = None
    
    def _processing_loop(self):
        """Main processing loop for signal analysis."""
        while self.running:
            try:
                # Read samples from RTL-SDR
                samples = self.sdr.read_samples(self.config['fft']['sample_size'])
                
                # Perform FFT
                fft_result = self._compute_fft(samples)
                
                # Analyze for miner signatures
                detected = self._analyze_signal(fft_result)
                
                if detected and self.callback:
                    self.callback(detected)
                    
            except Exception as e:
                self.logger.error(f"Error in processing loop: {str(e)}")
                self.running = False
                break
    
    def _compute_fft(self, samples):
        """Compute FFT of the signal samples."""
        # Apply window function
        windowed = samples * self.window
        
        # Compute FFT
        fft = np.fft.fft(windowed)
        fft = np.fft.fftshift(fft)
        
        # Calculate power spectrum
        power = 20 * np.log10(np.abs(fft))
        
        return {
            'power': power,
            'frequencies': np.fft.fftfreq(len(samples), 
                                        1/self.config['rtlsdr']['sample_rate'])
        }
    
    def _analyze_signal(self, fft_result):
        """Analyze FFT result for cryptocurrency miner signatures."""
        # Get power threshold from config
        threshold = self.config['alert']['threshold']['power']
        
        # Find peaks above threshold
        peaks = signal.find_peaks(fft_result['power'], 
                                height=threshold, 
                                distance=20)[0]
        
        if len(peaks) > 0:
            # Create detection record
            detection = {
                'timestamp': datetime.now(),
                'frequencies': [fft_result['frequencies'][p] for p in peaks],
                'powers': [fft_result['power'][p] for p in peaks],
                'confidence': self._calculate_confidence(fft_result['power'][peaks])
            }
            
            self.detected_signals.append(detection)
            return detection
        
        return None
    
    def _calculate_confidence(self, peak_powers):
        """Calculate confidence level of miner detection."""
        # Simple confidence calculation based on signal strength
        # Can be enhanced with more sophisticated algorithms
        avg_power = np.mean(peak_powers)
        threshold = self.config['alert']['threshold']['power']
        
        # Scale confidence between 0 and 1 based on power level
        confidence = (avg_power - threshold) / abs(threshold)
        return min(max(confidence, 0), 1)
    
    def get_detected_signals(self):
        """Return list of detected signals."""
        return self.detected_signals
    
    def clear_detected_signals(self):
        """Clear the list of detected signals."""
        self.detected_signals = []
    
    def simulate_miner_signal(self):
        """Generate simulated cryptocurrency miner signal patterns."""
        # Create synthetic signal patterns typical of miners
        sample_rate = self.config['rtlsdr']['sample_rate']
        n_samples = self.config['fft']['sample_size']
        t = np.arange(n_samples) / sample_rate
        
        # Simulate typical miner frequencies
        freq1 = 433e6  # Common frequency for RF emissions
        freq2 = 915e6  # Another common frequency
        
        # Generate complex signal
        signal = (np.sin(2 * np.pi * freq1 * t) + 
                 0.5 * np.sin(2 * np.pi * freq2 * t))
        
        # Add some noise
        noise = np.random.normal(0, 0.1, len(t))
        signal += noise
        
        return self._compute_fft(signal)
