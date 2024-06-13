from typing import List

from dynaconf import Validator


def get_logging_validators() -> List[Validator]:
    """ Logging validators.

    :return: list of logging validators.
    """
    return [
        Validator('logging.level',
                  default='INFO',
                  is_in=['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']),
        Validator('logging.path',
                  default=None),
    ]


def get_config_validators() -> List[Validator]:
    """ Data validators.

    :return: list of data validators.
    """
    return [
        Validator('geodata.saving_format',
                  default='parquet',
                  is_type_of=str),
        Validator('data.saving_format',
                  default='parquet',
                  is_type_of=str),
    ]


def get_ree_api_validator() -> List[Validator]:
    """ REE API validator.

    :return: REE API validator.
    """
    return [
        Validator('ree_data.url',
                  default='apidatos.ree.es',
                  is_type_of=str),
        Validator('ree.url',
                  default='api.esios.ree.es',
                  is_type_of=str),
        Validator('ree_demanda.url',
                  default='demanda.ree.es',
                  is_type_of=str),
        Validator('ree.token',
                  must_exist=True,
                  is_type_of=str),
        Validator('ree.max_days_per_request',
                  default=31,
                  is_type_of=int)
    ]


def get_validators() -> List[Validator]:
    """ Get the list of validators for the system.

    :return: list of system validators.
    """
    validators = get_logging_validators()
    validators += get_config_validators()
    validators += get_ree_api_validator()

    return validators
