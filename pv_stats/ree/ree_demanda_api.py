import json
from datetime import datetime
from typing import Dict

import requests
from dateutil.parser import isoparse
from loguru import logger
from pandas import DataFrame

from pv_stats.config.config import settings


def parse_timestamp(timestamp: str) -> datetime:
    """
    Parse the timestamp to a datetime object taking into account
    the change of hour in winter.

    :param timestamp: Timestamp to parse.
    :return: Datetime object.
    """
    try:
        time = isoparse(timestamp)
    except ValueError:
        # When the hour is changed in winter, the timestamp is not in ISO format,
        # so we need to parse it manually. The hour is such as 2019-10-27 2A:00 for the first one
        # and 2019-10-27 2B:00 for the second one. We are not using the timestamp as key,
        # so we can repeat the same timestamp for both.
        timestamp = timestamp.replace('2A', '02').replace('2B', '02')
        time = isoparse(timestamp)

    return time

def parse_response(data: Dict,
                   desired_date: datetime) -> DataFrame:
    """
    Parse the response from the REE API to generate a pandas dataframe.

    :param data: Data from the REE API.
    :param desired_date: Date to filter the data.
    :return: Parsed data.
    """
    generation_data = DataFrame(data['valoresHorariosGeneracion'])
    # The time is in the 'ts' column, so we need to parse it to datetime, check if it can be parsed
    # TODO: check error https://demanda.ree.es/visiona/peninsula/nacional/tablas/2019-10-27/2
    generation_data['Fecha'] = generation_data['ts'].apply(lambda x: parse_timestamp(x))

    # The data includes some rows of the previous and next day, so we filter them
    generation_data = generation_data[generation_data['Fecha'].dt.date == desired_date.date()]

    # Rename the columns to have a more descriptive name
    column_mapping = settings.ree.generation_mapping
    generation_data = generation_data.rename(columns=column_mapping)

    return generation_data


class REEDemandaAPI:

    def __init__(self):
        self.host = settings.ree_demanda.url
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Host': self.host
        }

        self.url = f'https://{self.host}/WSvisionaMovilesPeninsulaRest/resources/'

    def get_data(self,
                 category: str,
                 date: str | datetime,
                 geo_limit: str) -> Dict:
        """
        Get data from the REEData API. https://www.ree.es/en/apidatos

        :param category: Defines the general category. Examples seen are:
         "coeficientesCO2", "maxMinPeninsula", "prevProgPeninsula", "demandaGeneracionPeninsula"
        :param date: Defines the date to retrieve the data in ISO 8601 format. Example: 2021-01-01.
        :param geo_limit: Optional. Defines the electrical system of the requested data.
          Valid values are: peninsular, canarias, baleares, ceuta, melilla, ccaa.

        :return: the response in a dict from the JSON response.
        """
        # Get endpoint is formed with the category and widget
        endpoint = f'{self.url}/{category}'
        logger.debug('Requesting data from {}', endpoint)

        # Parse the date to string with YYYY-MM-DD format
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        elif isinstance(date, str):
            date = isoparse(date).strftime('%Y-%m-%d')

        params = {
            'callback': 'angular.callbacks._0',
            'fecha': date,
            'curva': geo_limit,
        }

        res = requests.get(endpoint,
                           headers=self.headers,
                           params=params)
        logger.info('Request status code: {}', res.status_code)
        res.raise_for_status()

        data = res.text

        # The desired JSON is inside the callback function, so we need to remove the function call
        data = data[data.find('(') + 1:data.rfind(')')]
        data = json.loads(data)

        return data

    def get_generation(self,
                       date: str | datetime,
                       geo_limit: str) -> DataFrame:
        """ Get the demand data from the REE API.

        :param date: Defines the date to retrieve the data in ISO 8601 format. Example: 2021-01-01.
        :param geo_limit: Optional. Defines the electrical system of the requested data.
          Valid values are: peninsular, canarias, baleares, ceuta, melilla, ccaa.
        :return: DataFrame with the demand data.
        """
        logger.debug('Getting demand data from REE API for the day {} in {}.', date, geo_limit)
        data = self.get_data(category='demandaGeneracionPeninsula',
                             date=date,
                             geo_limit=geo_limit)
        data = parse_response(data, date)
        return data
