"""
Retrieve data from Web of Science Core Collection with Web of Science
Expanded API.
"""

import requests


def validate_search_query(apikey, query):
    """Check if the search query is correct, count the number of documents
    in that search query.

    :param apikey: str.
    :param query: str.
    :return: str, str.
    """
    test_request = requests.get(
        url=f'https://wos-api.clarivate.com/api/wos/?databaseId=WOS&usrQuery={query}&'
            f'count=0&firstRecord=1',
        headers={'X-APIkey': apikey},
        timeout=16
    )
    if test_request.status_code == 200:
        return test_request.status_code, test_request.json()['QueryResult']['RecordsFound']
    return test_request.status_code, test_request.json()['message'].split(':')[-1]


def retrieve_wos_metadata_via_api(apikey, query, first_record=1):
    """Retrieve Web of Science documents metadata through Web of Science
    Expanded API.

    :param apikey: str.
    :param query: str.
    :param rpp: int.
    :param first_record: int.
    :return: dict.
    """
    params = {
        'databaseId': 'WOS',
        'usrQuery': query,
        'count': 100,
        'firstRecord': first_record
    }
    expanded_api_request = requests.get(
        url='https://wos-api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': apikey},
        timeout=16
    )

    return expanded_api_request.json()


def retrieve_cited_refs_via_api(apikey, ut):
    """Retrieve cited references metadata one by one through Web of Science
    Expanded API /references endpoint

    :param apikey: str.
    :param ut: str.
    :return: dict.
    """
    params = {
        'databaseId': 'WOS',
        'uniqueId': ut,
        'count': 100,
        'first_record': 1
    }
    refs_request = requests.get(
        url='https://api.clarivate.com/api/wos/references',
        params=params,
        headers={'X-ApiKey': apikey},
        timeout=16
    )
    refs_json = refs_request.json()
    refs_count = refs_json['QueryResult']['RecordsFound']
    while params['first_record'] + 99 < refs_count:
        params['first_record'] += 100
        subsequent_request = requests.get(
            url='https://api.clarivate.com/api/wos/references',
            params=params,
            headers={'X-ApiKey': apikey},
            timeout=16
        )
        subsequent_json = subsequent_request.json()
        for cited_ref in subsequent_json['Data']:
            refs_json['Data'].append(cited_ref)
    return refs_json
