import json
import logging
from datetime import datetime
from pathlib import Path

def setup_logger():
    """Configure and return the application logger."""
    logger = logging.getLogger('CryptoMinerDetector')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('detector.log')
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.INFO)
    
    # Create formatters and add to handlers
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger

def load_config():
    """Load configuration from config.json file."""
    try:
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger = logging.getLogger('CryptoMinerDetector')
        logger.error(f"Error loading config: {str(e)}")
        raise

def format_frequency(freq_hz):
    """Format frequency in Hz to a human-readable string."""
    if freq_hz >= 1e9:
        return f"{freq_hz/1e9:.2f} GHz"
    elif freq_hz >= 1e6:
        return f"{freq_hz/1e6:.2f} MHz"
    elif freq_hz >= 1e3:
        return f"{freq_hz/1e3:.2f} kHz"
    else:
        return f"{freq_hz:.2f} Hz"

def timestamp_to_str(timestamp=None):
    """Convert timestamp to formatted string."""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def validate_frequency(freq):
    """Validate if a frequency is within acceptable range for RTL-SDR."""
    min_freq = 24e6  # 24 MHz
    max_freq = 1766e6  # 1.766 GHz
    return min_freq <= freq <= max_freq

def calculate_fft_params(config):
    """Calculate FFT parameters based on configuration."""
    sample_rate = config['rtlsdr']['sample_rate']
    sample_size = config['fft']['sample_size']
    
    freq_resolution = sample_rate / sample_size
    time_resolution = sample_size / sample_rate
    
    return {
        'freq_resolution': freq_resolution,
        'time_resolution': time_resolution,
        'freq_range': (0, sample_rate/2)
    }

# Error handling decorator
def error_handler(func):
    """Decorator for handling and logging errors."""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('CryptoMinerDetector')
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper
