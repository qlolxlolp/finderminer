import sys
import logging
from pathlib import Path
from src.utils import setup_logger, load_config
from src.signal_processor import SignalProcessor
from src.report_generator import ReportGenerator
from src.alert_system import AlertSystem
from src.gui import DetectorGUI

def main():
    """Main entry point of the application."""
    try:
        # Set up logging
        logger = setup_logger()
        logger.info("Starting Crypto Miner Signal Detector")
        
        # Load configuration
        try:
            config = load_config()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)
        
        # Initialize components
        try:
            signal_processor = SignalProcessor(config)
            report_generator = ReportGenerator(config)
            alert_system = AlertSystem(config)
            
            # Register alert callback for GUI updates
            def alert_callback(alert):
                logger.info(f"Alert triggered: {alert['timestamp']}")
            alert_system.register_callback(alert_callback)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            sys.exit(1)
        
        # Create and run GUI
        try:
            gui = DetectorGUI(config, signal_processor, report_generator, alert_system)
            logger.info("GUI initialized successfully")
            
            # Start GUI main loop
            gui.run()
            
        except Exception as e:
            logger.error(f"Error in GUI: {str(e)}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
    
    finally:
        # Cleanup
        try:
            if 'gui' in locals():
                gui.cleanup()
            logging.shutdown()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    main()
