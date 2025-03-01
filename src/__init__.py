"""
CryptoMinerSignalDetector - A system for detecting cryptocurrency miner radio signals
"""

from .utils import setup_logger, load_config
from .signal_processor import SignalProcessor
from .report_generator import ReportGenerator
from .alert_system import AlertSystem
from .gui import DetectorGUI

__version__ = '1.0.0'
__author__ = 'BLACKBOXAI'
