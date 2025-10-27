"""
Retrieve data from Web of Science Core Collection with Web of Science
Expanded API.
"""

import requests
import time


def validate_search_query(apikey, query):
    """Check if the search query is valid, returns the number of
    Web of Science documents found in the search query.

    :param apikey: str.
    :param query: str.
    :return: int.
    """
    request = requests.get(
        url=f'https://wos-api.clarivate.com/api/wos/?databaseId=WOS&usrQuery='
            f'{query}&count=0&firstRecord=1',
        headers={'X-ApiKey': apikey},
        timeout=16
    )

    if request.status_code == 200:
        json = request.json()
        return request.status_code, json['QueryResult']['RecordsFound']
    return request.status_code, request.json()['message'].split(':')[-1]


def base_records_api_call(apikey, query, first_record=1):
    """Retrieve Web of Science documents metadata through
    Web of Science Expanded API.

    :param apikey: str.
    :param query: str.
    :param first_record: int.
    :return: dict.
    """
    params = {
        'databaseId': 'WOS',
        'usrQuery': query,
        'count': 100,
        'firstRecord': first_record
    }
    request = requests.get(
        url='https://wos-api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': apikey},
        timeout=16
    )

    if request.headers['x-req-reqpersec-remaining'] == 0:
        time.sleep(.2)

    return request.json()


def citing_records_api_call(apikey, ut, first_record=1):
    """Retrieve Web of Science citing documents metadata through
    Web of Science Expanded API.

    :param apikey: str.
    :param ut: str.
    :param first_record: int.
    :return: dict.
    """
    params = {
        'databaseId': 'WOS',
        'uniqueId': ut,
        'count': 100,
        'firstRecord': first_record
    }
    request = requests.get(
        url='https://wos-api.clarivate.com/api/wos/citing/',
        params=params,
        headers={'X-ApiKey': apikey},
        timeout=16
    )

    if int(request.headers['x-req-reqpersec-remaining']) == 0:
        time.sleep(.2)

    return request.json()
