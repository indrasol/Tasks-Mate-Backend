import logging


def get_logger(
    name=__name__, 
    to_console=True, 
    to_file=True, 
    filename="app.log", 
    level=logging.INFO
):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent double logging if root logger is configured
    
    # Clear existing handlers (if any)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
    )
    
    if to_console:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    if to_file:
        fh = logging.FileHandler(filename)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

logger = get_logger('utils.logger', to_console=True, to_file=True, filename='app.log', level=logging.INFO)

def log_info(message):
    logger.info(f"--------------------------------")
    logger.info(f"{message}")
    logger.info(f"--------------------------------")

def log_error(message):
    logger.error(f"--------------------------------")
    logger.error(f"{message}")
    logger.error(f"--------------------------------")

def log_debugger(message):
    logger.debug(f"--------------------------------")
    logger.debug(f"{message}")
    logger.debug(f"--------------------------------")

