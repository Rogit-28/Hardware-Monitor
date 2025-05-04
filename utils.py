import logging
import os
from datetime import datetime
from typing import Optional

def setup_logging(log_dir: str = "telemetry_logs") -> logging.Logger:
    # Logger fn
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logger = logging.getLogger("TelemetryCollector")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger