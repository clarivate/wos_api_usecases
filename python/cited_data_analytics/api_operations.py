"""
Retrieve data from Web of Science Core Collection with Web of Science
Expanded API.
"""

import urllib.parse
import requests
import time


def validate_search_query(apikey, query):
    """Check if the search query is valid, returns the number of grants documents found in the
    query.

    :param apikey: str.
    :param query: str.
    :return: int.
    """
    test_request = requests.get(
        url=f'https://api.clarivate.com/api/wos/?databaseId=WOS&usrQuery='
            f'{urllib.parse.quote(query)}&count=0&firstRecord=1',
        headers={'X-ApiKey': apikey},
        timeout=16
    )
    if test_request.status_code == 200:
        test_json = test_request.json()
        return test_request.status_code, test_json['QueryResult']['RecordsFound']
    return test_request.status_code, test_request.json()['message'].split(':')[-1]


def base_record_ids_request(apikey, query_id, first_record):
    """Retrieve the list of base Web of Science document records
    through Web of Science Expanded API.

    :param apikey: str.
    :param query_id: int.
    :param first_record: int.
    :return: dict.
    """
    params = {
        'count': 100,
        'firstRecord': first_record
    }

    response = requests.get(
        url=f'https://api.clarivate.com/api/wos/recordids/{query_id}',
        params=params,
        headers={'X-ApiKey': apikey},
        timeout=16
    )

    if response.status_code == 500:
        return base_record_ids_request(apikey, query_id, first_record)

    return response


def cited_references_request(apikey, ut, first_record=1):
    """Retrieve Web of Science cited reference metadata through Web of
    Science Expanded API.

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

    response = requests.get(
        url='https://api.clarivate.com/api/wos/references',
        params=params,
        headers={'X-ApiKey': apikey},
        timeout=16
    )

    if response.headers['x-req-reqpersec-remaining'] == 0:
        time.sleep(.2)

    return response


def fullrecord_request(apikey, uts):
    """Retrieve Web of Science full record metadata through Web of
    Science Expanded API.

    :param apikey: str.
    :param uts: str.
    :return: dict.
    """
    params = {
        'databaseId': 'WOS',
        'usrQuery': f'UT=({uts})',
        'count': 20,
        'firstRecord': 1,
        'viewField': 'publishers'
    }
    response = requests.get(
        url='https://api.clarivate.com/api/wos/',
        params=params,
        headers={'X-ApiKey': apikey},
        timeout=16
    )
    if response.status_code == 500:
        return fullrecord_request(apikey, uts)

    return response
