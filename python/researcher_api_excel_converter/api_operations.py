"""
Retrieve data from Web of Science Core Collection with Web of Science
Researcher API.
"""

import urllib.parse
import requests


def validate_search_query(apikey: str, query: str) -> tuple:
    """Check if the search query is valid, returns the number of
    documents found in the query."""

    test_request = requests.get(
        url=f'https://api.clarivate.com/apis/wos-researcher/researchers?'
            f'q={urllib.parse.quote(query)}&page=1',
        headers={'X-ApiKey': apikey},
        timeout=16
    )
    if test_request.status_code == 200:
        test_json = test_request.json()

        return (test_request.status_code,
                test_json['metadata']['total'])

    if test_request.status_code == 400:
        test_json = test_request.json()

        return (test_request.status_code,
                test_json['error']['details'])

    return test_request.status_code, test_request.json()['detail']


def researcher_api_request(apikey: str, query: str, page=1) -> dict:
    """Send an API call to the default Researcher API endpoint."""

    result = requests.get(
        url=f'https://api.clarivate.com/apis/wos-researcher/researchers?q='
            f'{urllib.parse.quote(query)}&page={page}&limit=50',
        headers={'X-APIKey': apikey},
        timeout=16
    ).json()

    return result


def researcher_api_profile_request(apikey: str, rid: str) -> dict:
    """Send an API call to the /researchers endpoint of Researcher
    API."""

    result = requests.get(
        url=f'https://api.clarivate.com/apis/wos-researcher/researchers/{rid}',
        headers={'X-APIKey': apikey},
        timeout=16
    ).json()

    return result
