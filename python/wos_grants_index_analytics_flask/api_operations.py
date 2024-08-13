"""
Retrieve data from Web of Science Grants Index with Web of Science
Starter API, retrieve exchange rates data with Ope Exchange Rates
API.
"""

from datetime import date, datetime
import requests


def retrieve_rates_via_api():
    """Get the exchange rates from the open exchange rates API:
    https://open.er-api.com/v6/latest/USD.

    :return: dict.
    """
    rates = requests.get(url='https://open.er-api.com/v6/latest/USD', timeout=16).json()['rates']
    with open('currencies.csv', 'w', encoding='utf-8') as writing:
        writing.writelines(f'Updated,{datetime.strftime(date.today(), "%m/%d/%Y")}\n\n'
                           f'Currency,Rate VS USD\n')
        for key, value in rates.items():
            writing.writelines(f'{key},{value}\n')
    return rates


def validate_search_query(apikey, query):
    """Check if the search query is valid, returns the number of grants documents found in the
    query.

    :param apikey: str.
    :param query: str.
    :return: int.
    """
    test_request = requests.get(
        url=f'https://wos-api.clarivate.com/api/wos/?databaseId=GRANTS&usrQuery={query}&'
            f'count=0&firstRecord=1',
        headers={'X-ApiKey': apikey},
        timeout=16
    )
    if test_request.status_code == 200:
        test_json = test_request.json()
        return test_request.status_code, test_json['QueryResult']['RecordsFound']
    return test_request.status_code, test_request.json()['message'].split(':')[-1]


def retrieve_wos_metadata_via_api(apikey, query, rpp, first_record=1):
    """Retrieve Web of Science documents metadata through Web of Science
    Expanded API.

    :param apikey: str.
    :param query: str.
    :param rpp: int.
    :param first_record: int.
    :return: dict.
    """
    params = {
        'databaseId': 'GRANTS',
        'usrQuery': query,
        'count': rpp,
        'firstRecord': first_record
    }
    initial_request = requests.get(
        url='https://wos-api.clarivate.com/api/wos',
        params=params,
        headers={'X-ApiKey': apikey},
        timeout=16
    )
    return initial_request.json()
