###############################################################################
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
###############################################################################


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
        if level is not None and isinstance(level, basestring):
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
