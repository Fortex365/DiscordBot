import logging

def setup_logging():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.WARNING)

    handler = logging.FileHandler(filename='log_service/barmaid.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

    logger.addHandler(handler)
    return logger