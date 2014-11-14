# coding=utf-8


import logging

import manager


_LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }


def set_up_logger(root_logger, level = None):
    logger = None
    if root_logger is not None:
        logger = root_logger.getChild(manager._LOGGER_MODULE)
        if level is not None and isinstance(level, str):
            level = level.lower()
            level = _LOG_LEVELS[level]
            logger.setLevel(level)
    return logger


def log(logger, level, message):
    assert level in _LOG_LEVELS
    if logger is not None:
        getattr(logger, level)(message)


def debug(logger, message):
    log(logger, 'debug', message)


def info(logger, message):
    log(logger, 'info', message)


def warning(logger, message):
    log(logger, 'warning', message)


def error(logger, message):
    log(logger, 'error', message)


def critical(logger, message):
    log(logger, 'critical', message)


def cover_auth_data(data, show):
    if show:
        return data
    if not isinstance(data, dict):
        return manager._COVER_AUTH_DATA_WITH
    covered_data = {}
    for k in data:
        covered_data[k] = manager._COVER_AUTH_DATA_WITH
    return str(covered_data).strip()
