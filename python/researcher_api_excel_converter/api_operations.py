"""
Retrieve data from Web of Science Core Collection with Web of Science
Researcher API.
"""

import urllib.parse
import requests
from apikeys import RESEARCHER_APIKEY


def validate_search_query(query: str) -> tuple:
    """Check if the search query is valid, returns the number of
    documents found in the query."""

    test_request = requests.get(
        url=f'https://api.clarivate.com/apis/wos-researcher/researchers?'
            f'q={urllib.parse.quote(query)}&page=1',
        headers={'X-ApiKey': RESEARCHER_APIKEY},
        timeout=16
    )
    if test_request.status_code == 200:
        test_json = test_request.json()

        return (test_request.status_code,
                test_json['metadata']['total'],
                test_request.headers['X-RateLimit-Remaining-Day'])

    if test_request.status_code == 400:
        test_json = test_request.json()

        return (test_request.status_code,
                test_json['error']['details'])

    return test_request.status_code, test_request.json()['detail']


def researcher_api_request(query: str, page=1) -> dict:
    """Send an API call to the default Researcher API endpoint."""

    return requests.get(
        url=f'https://api.clarivate.com/apis/wos-researcher/researchers?q='
            f'{urllib.parse.quote(query)}&page={page}&limit=50',
        headers={'X-APIKey': RESEARCHER_APIKEY},
        timeout=16
    ).json()


def researcher_api_profile_request(rid: str) -> dict:
    """Send an API call to the /researchers endpoint of Researcher
    API."""

    return requests.get(
        url=f'https://api.clarivate.com/apis/wos-researcher/researchers/{rid}',
        headers={'X-APIKey': RESEARCHER_APIKEY},
        timeout=16
    ).json()


def researcher_api_doc_request(rid: str, page=1) -> dict:
    """Send an API call to the /documents endpoint of Researcher
    API."""

    return requests.get(
        url=f'https://api.clarivate.com/apis/wos-researcher/researchers/{rid}'
            f'/documents?limit=50&page={page}',
        headers={'X-APIKey': RESEARCHER_APIKEY},
        timeout=16
    ).json()


def peer_review_api_request(rid: str, page=1) -> dict:
    """Send an API call to the /peer_reviews endpoint of Researcher
    API."""

    return requests.get(
        url=f'https://api.clarivate.com/apis/wos-researcher/researchers/{rid}'
            f'/peer-reviews?page={page}',
        headers={'X-APIKey': RESEARCHER_APIKEY},
        timeout=16
    ).json()
