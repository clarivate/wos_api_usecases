"""
Retrieve data from Web of Science Core Collection and Policy Citation
Index through Web of Science Expanded API.
"""

import requests
from apikeys import EXPANDED_APIKEY


def validate_search_query_wos(query: str) -> tuple:
    """Check if the Web of Science Core Collection search query is
    valid, return the number of documents found in the query or the
    error message.
    """

    params = {
        'databaseId': 'WOS',
        'usrQuery': query,
        'count': 0,
        'firstRecord': 1
    }
    test_request = requests.get(
        url='https://api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': EXPANDED_APIKEY},
        timeout=16
    )
    if test_request.status_code == 200:
        test_json = test_request.json()

        return (test_request.status_code,
                test_json['QueryResult']['RecordsFound'])

    return (test_request.status_code,
            test_request.json()['message'].split(':')[-1])


def validate_search_query_pci(query: str) -> tuple:
    """Check if the Policy Citation Index search query is valid,
    returns the number of documents found in the query or the error
    message."""

    params = {
        'databaseId': 'PCI',
        'usrQuery': query,
        'count': 0,
        'firstRecord': 1
    }
    test_request = requests.get(
        url='https://api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': EXPANDED_APIKEY},
        timeout=16
    )
    if test_request.status_code == 200:
        test_json = test_request.json()

        return (test_request.status_code,
                test_json['QueryResult']['RecordsFound'])

    return (test_request.status_code,
            test_request.json()['message'].split(':')[-1])


def base_records_api_call(search_query: str, first_record=1) -> dict:
    """Retrieve Web of Science base record metadata through Web of
    Science Expanded API.
    """

    params = {
        'databaseId': 'WOS',
        'usrQuery': search_query,
        'count': 100,
        'firstRecord': first_record
    }
    try:
        response = requests.get(
            url='https://api.clarivate.com/api/wos',
            params=params,
            headers={'X-ApiKey': EXPANDED_APIKEY},
            timeout=16
        )
        if response.status_code == 200:
            result = response.json()
        else:
            print(f'Oops, error {response.status_code} - resending...')
            result = base_records_api_call(search_query, first_record)

    except(requests.ReadTimeout, requests.ConnectionError, requests.JSONDecodeError):
        result = {'Data': {'Records': {'records': {'REC': []}}}}
        params['count'] = 10
        for i in range(10):
            first_record += i * 10
            request = requests.get(
                url='https://api.clarivate.com/api/wos',
                params=params,
                headers={'X-ApiKey': EXPANDED_APIKEY},
                timeout=32
            )

            rec_json = request.json()['Data']['Records']['records']['REC']
            result['Data']['Records']['records']['REC'].extend(rec_json)

    return result


def citing_policy_docs_empty_query(rec: dict) -> dict:
    """An API call to retrieve the query number and the quantity of
    citing policy documents to be reused in the next API call managed
    by citing_policy_ids_api_call function.
    """

    params = {
        'databaseId': 'WOK',
        'uniqueId': rec['ut'],
        'count': 0,
        'firstRecord': 1
    }
    response = requests.get(
        url='https://api.clarivate.com/api/wos/citing',
        params=params,
        headers={'X-ApiKey': EXPANDED_APIKEY},
        timeout=16
    )
    if response.status_code == 200:
        result = response.json()
    else:
        print(f'Oops, error {response.status_code} - resending...')
        result = citing_policy_docs_empty_query(rec)

    return result


def citing_policy_ids_api_call(query_id: str, first_record=1) -> dict:
    """Make API call to retrieve the ids of the citing policy
    documents."""

    params = {
        'count': 100,
        'firstRecord': first_record,
    }
    response = requests.get(
        f'https://api.clarivate.com/api/wos/recordids/{query_id}',
        params=params,
        headers={'X-APIKey': EXPANDED_APIKEY},
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
    else:
        print(f'Oops, error {response.status_code} - resending...')
        result = citing_policy_ids_api_call(query_id, first_record)

    return result


def policy_docs_api_call_by_ids(doc_ids_batch: list) -> dict:
    """Send API calls for policy document IDs in batches of 100 via Web
    of Science Expanded API to get the metadata."""

    params = {
        'databaseId': 'PCI',
        'usrQuery': f'UT={" ".join(doc_ids_batch)}',
        'count': 100,
        'firstRecord': 1,
    }
    result = requests.get(
        url='https://api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': EXPANDED_APIKEY},
        timeout=30
    )

    return result.json()


def policy_docs_api_call_by_query(search_query: str, first_record=1) -> dict:
    """Retrieve Policy Citation Index document records through Web of
    Science Expanded API.
    """

    params = {
        'databaseId': 'PCI',
        'usrQuery': search_query,
        'count': 100,
        'firstRecord': first_record
    }
    response = requests.get(
        url='https://api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': EXPANDED_APIKEY},
        timeout=16
    )
    if response.status_code == 200:
        result = response.json()
    else:
        print(f'Oops, error {response.status_code} - resending...')
        result = base_records_api_call(search_query, first_record)

    return result


def wos_pubyear_call(search_query: str, first_record=1) -> dict:
    """Retrieve Web of Science Core Collection document records
    publication metadata section through Web of Science Expanded API.
    """

    params = {
        'databaseId': 'WOS',
        'usrQuery': search_query,
        'count': 100,
        'firstRecord': first_record,
        'viewField': 'pub_info'
    }
    response = requests.get(
        url='https://api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': EXPANDED_APIKEY},
        timeout=16
    )
    if response.status_code == 200:
        result = response.json()
    else:
        print(f'Oops, error {response.status_code} - resending...')
        result = base_records_api_call(search_query, first_record)

    return result


def pci_pubyear_call(search_query: str, first_record=1) -> dict:
    """Retrieve Policy Citation Index records publication information
    metadata section through Web of Science Expanded API.
    """

    params = {
        'databaseId': 'PCI',
        'usrQuery': search_query,
        'count': 100,
        'firstRecord': first_record,
        'viewField': 'pub_info'
    }
    response = requests.get(
        url='https://api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': EXPANDED_APIKEY},
        timeout=16
    )
    if response.status_code == 200:
        result = response.json()
    else:
        print(f'Oops, error {response.status_code} - resending...')
        result = base_records_api_call(search_query, first_record)

    return result
