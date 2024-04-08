import sys

from dynaconf import Dynaconf
from loguru import logger

from pv_stats.config.validators import get_validators

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
settings = Dynaconf(
    envvar_prefix="FOTOVOLTAICA_MADRID",
    settings_files=['settings.toml', '.secrets.toml'],
    validators=get_validators(),
    merge_enabled=True
)


def configure_logs() -> None:
    """ Configures the logging system for the order. """
    logger.remove()
    log_level = settings.logging.level
    log_path = settings.logging.path
    logger.add(sys.stderr, level=log_level)
    # If log is a path to a file, save them.
    if log_path:
        logger.add(log_path, level=log_level)
        logger.info('Saving logs in file. Path: {}.', log_path)
    logger.debug('Setting log level to: {}', log_level)
