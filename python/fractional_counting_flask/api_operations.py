"""
Retrieve data from Web of Science Core Collection with Web of Science
Expanded API.
"""

import urllib.parse
import requests


def validate_search_query(apikey, query):
    """Check if the search query is valid, returns the number of
    documents found in the query.

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

        return (test_request.status_code,
                test_json['QueryResult']['RecordsFound'])

    return (test_request.status_code,
            test_request.json()['message'].split(':')[-1])


def retrieve_wos_metadata(apikey, search_query, first_record=1):
    """Retrieve Web of Science full record metadata through Web of
    Science Expanded API.

    :param apikey: str.
    :param search_query: str.
    :param first_record: int.
    :return: dict.
    """
    params = {
        'databaseId': 'WOS',
        'usrQuery': search_query,
        'count': 100,
        'firstRecord': first_record,
    }
    try:
        result = requests.get(
            url='https://api.clarivate.com/api/wos',
            params=params,
            headers={'X-ApiKey': apikey},
            timeout=16
        ).json()

    # In case of hyper-authored papers in API response resulting in enormous JSON size
    except (requests.ReadTimeout, requests.ConnectionError, requests.JSONDecodeError):
        result = {'Data': {'Records': {'records': {'REC': []}}}}
        params['count'] = 10
        for i in range(10):
            first_record += i*10
            request = requests.get(
                url='https://api.clarivate.com/api/wos',
                params=params,
                headers={'X-ApiKey': apikey},
                timeout=64
            )

            rec_json = request.json()['Data']['Records']['records']['REC']
            result['Data']['Records']['records']['REC'].extend(rec_json)

    return result
