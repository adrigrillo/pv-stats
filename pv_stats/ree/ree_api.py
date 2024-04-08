from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List

import requests
from dateutil.parser import isoparse
from loguru import logger
from pandas import DataFrame

from pv_stats.config.config import settings


def parse_date(date: str | datetime) -> str:
    """
    Parse the date to ISO 8601 format. It returns until minutes to match the
    REE API format.

    :param date: Date to be parsed.
    :return: Date in ISO 8601 format.
    """
    if isinstance(date, str):
        # If the date is correct ISO format, it will parse it correctly else
        # it will raise an error.
        final_date = isoparse(date).isoformat(timespec='minutes')
    elif isinstance(date, datetime):
        # Get the ISO 8601 format from the datetime as string
        final_date = date.isoformat(timespec='minutes')
    else:
        raise ValueError('Date must be a string or a datetime object.')

    return final_date


def parse_response(data: Dict) -> DataFrame:
    """
    Parse the response from the REE API to generate a pandas dataframe.

    :param data: Data from the REE API.
    :return: Parsed data.
    """
    demand_data = dict()

    for demand_type in data['included']:
        demand_name = demand_type['attributes']['title']
        for value_in_time in demand_type['attributes']['values']:
            demand_time = value_in_time['datetime']
            demand_value = value_in_time['value']

            # Start from an empty dict if the time is not in the dict
            demand_for_time = demand_data.get(demand_time, dict())
            demand_for_time[demand_name] = demand_value

            # Update the dict with the new demand data, as the get returns a copy and it is not updated in place
            demand_data[demand_time] = demand_for_time

    df = DataFrame.from_dict(demand_data, orient='index')
    return df


def throttle_request_dates(start_date: str | datetime,
                           end_date: str | datetime) -> List[Tuple[str, str]]:
    """
    Throttle the request dates to be in given intervals.

    :param start_date: date to start the request.
    :param end_date: date to end the request.
    :return: list of start and end dates to be requested.
    """
    start_date = isoparse(start_date)
    end_date = isoparse(end_date)
    max_days_per_request = settings.ree.max_days_per_request

    # Get the number of days between the start and end date
    delta = end_date - start_date

    # If the delta is less than the max days per request, return the original dates
    if delta.days <= max_days_per_request:
        return [(
            start_date.isoformat(timespec='minutes'),
            end_date.isoformat(timespec='minutes')
        )]

    else:
        # Get the number of requests to be made
        num_requests = delta.days // max_days_per_request
        # Get the remaining days
        remaining_days = delta.days % max_days_per_request

        # List of dates to be requested
        dates = list()
        for _ in range(num_requests):
            # Get the end date for the request
            end_date_request = start_date + timedelta(days=max_days_per_request)
            dates.append((
                start_date.isoformat(timespec='minutes'),
                end_date_request.isoformat(timespec='minutes')
            ))
            logger.debug('A request will be generated from {} to {}', start_date, end_date_request)
            # Update the start date for the next request
            start_date = end_date_request

        # If there are remaining days, add them to the last request
        if remaining_days > 0:
            dates.append((
                start_date.isoformat(timespec='minutes'),
                end_date.isoformat(timespec='minutes')
            ))
            logger.debug('A request will be generated from {} to {}', start_date, end_date)

        return dates


class REEDataAPI:

    def __init__(self, language: str = 'es'):
        self.host = settings.ree_data.url
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Host': self.host
        }

        if language not in ['es', 'en']:
            language = 'es'
            logger.warning('Language `{}` not supported. Using Spanish as default.', language)

        self.url = f'https://{self.host}/{language}/datos'

    def get_data(self,
                 category: str,
                 widget: str,
                 start_date: str | datetime,
                 end_date: str | datetime,
                 time_trunc: str,
                 geo_trunc: Optional[str],
                 geo_limit: Optional[str],
                 geo_ids: Optional[int]) -> Dict:
        """
        Get data from the REEData API. https://www.ree.es/en/apidatos

        :param category: Defines the general category.
        :param widget: Defines the particular widget to be retrieved.
        :param start_date: Defines the starting date in ISO 8601 format. Example: 2021-01-01T00:00.
        :param end_date: Defines the ending date in ISO 8601 format. Example: 2021-01-01T00:10.
        :param time_trunc: Defines the time aggregation of the requested data. Valid values are: hour, day, month, year.
        :param geo_trunc: Optional. Defines the geographical scope of the requested data.
          Currently, the only allowed value is: electric_system.
        :param geo_limit: Optional. Defines the electrical system of the requested data.
          Valid values are: peninsular, canarias, baleares, ceuta, melilla, ccaa.
        :param geo_ids: Optional. Defines the ID of the previously defined autonomous community/electrical system.

        :return: the response in a dict from the JSON response.
        """
        # Get endpoint is formed with the category and widget
        endpoint = f'{self.url}/{category}/{widget}'
        logger.debug('Requesting data from {}', endpoint)

        # Params to be sent in the request
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
        if time_trunc not in ['hour', 'day', 'month', 'year']:
            raise ValueError('Time trunc must be hour, day, month or year.')

        params = {
            'start_date': start_date,
            'end_date': end_date,
            'time_trunc': time_trunc
        }

        if geo_trunc:
            if geo_trunc != 'electric_system':
                raise ValueError('Geo trunc must be electric_system.')
            else:
                params['geo_trunc'] = geo_trunc

        if geo_limit:
            if geo_limit not in ['peninsular', 'canarias', 'baleares', 'ceuta', 'melilla', 'ccaa']:
                raise ValueError('Geo limit must be peninsular, canarias, baleares, ceuta, melilla or ccaa.')

            if not geo_ids:
                raise ValueError('If geo limit is used, geo ids must be provided.')

            params['geo_limit'] = geo_limit
            params['geo_ids'] = geo_ids

        res = requests.get(endpoint,
                           headers=self.headers,
                           params=params)
        logger.info('Request status code: {}', res.status_code)
        res.raise_for_status()

        data = res.json()
        return data

    def get_demand(self,
                   start_date: str | datetime,
                   end_date: str | datetime,
                   time_trunc: str,
                   geo_trunc: Optional[str],
                   geo_limit: Optional[str],
                   geo_ids: Optional[int]) -> DataFrame:
        """ Get the demand data from the REE API.

        :param start_date: Defines the starting date in ISO 8601 format. Example: 2021-01-01T00:00.
        :param end_date: Defines the ending date in ISO 8601 format. Example: 2021-01-01T00:10.
        :param time_trunc: Defines the time aggregation of the requested data. Valid values are: hour, day, month, year.
        :param geo_trunc: Optional. Defines the geographical scope of the requested data.
          Currently, the only allowed value is: electric_system.
        :param geo_limit: Optional. Defines the electrical system of the requested data.
          Valid values are: peninsular, canarias, baleares, ceuta, melilla, ccaa.
        :param geo_ids: Optional. Defines the ID of the previously defined autonomous community/electrical system.
        :return: DataFrame with the demand data.
        """
        logger.debug('Getting demand data from REE API from {} to {} in {}.', start_date, end_date, time_trunc)
        data = self.get_data(category='demanda',
                             widget='demanda-tiempo-real',
                             start_date=start_date,
                             end_date=end_date,
                             time_trunc=time_trunc,
                             geo_trunc=geo_trunc,
                             geo_limit=geo_limit,
                             geo_ids=geo_ids)
        data = parse_response(data)
        return data
