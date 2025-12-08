from src.smtp.logger.log_hierarchy import transc
from src.smtp.logger.transc_log import setup_logger

# Setup logging module 'transcations'
log_file = transc.create_log()
logger = setup_logger(log_filepath=log_file)
