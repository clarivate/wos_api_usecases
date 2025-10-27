"""
Manage all the data operations: the main function that gets executed
after the 'run' button is pressed, data retrieval through the APIs
and parsing the required metadata fields.
"""

from datetime import date
import state
import urllib.parse
import requests
import pandas as pd
from api_operations import (
    base_record_ids_request,
    cited_references_request,
    fullrecord_request
)
from visualizations import visualize_data


def run_button(apikey, search_query):
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations

    :param apikey: str.
    :param search_query: str.
    :return: str, tuple.
    """

    # Retrieve base document IDs
    base_record_ids = get_base_records_ids(apikey, search_query)

    # Retrieve cited references
    cited_refs = get_cited_references(apikey, base_record_ids)

    # Retrieve additional WoS record metadata
    addtl_fields_list = enrich_with_wos_metadata(apikey, cited_refs)

    # Arrange the data into a single dataframe
    df = pd.DataFrame(cited_refs, index=None)
    df['TimesCited'] = pd.to_numeric(df['TimesCited'])
    df2 = pd.DataFrame(addtl_fields_list, index=None)
    df = pd.merge(df, df2, on='UID', how='left')

    safe_search_query = search_query.replace('*', '').replace('"', '')
    filename = f'downloads/{safe_search_query} - {date.today()}.csv'

    with open(filename, 'w', encoding='utf-8', newline='') as f:
        f.write(f"Search Query:,{search_query}\n\n")
        df.to_csv(f, index=False)

    plots = visualize_data(df, search_query)

    state.progress = 0
    state.current_task = ""

    return f'{safe_search_query} - {date.today()}.csv', plots


def get_base_records_ids(apikey: str, search_query: str) -> list[str]:
    """Manage API calls and parsing to get the list of base record ids.

    """
    state.progress = 0
    state.current_task = "Retrieving Base Records IDs"
    ids_list = []
    initial_json = requests.get(
        url=f'https://api.clarivate.com/api/wos/?databaseId=WOS&usrQuery='
            f'{urllib.parse.quote(search_query)}&count=0&firstRecord=1',
        headers={'X-Apikey': apikey},
        timeout=16
    ).json()
    query_id = initial_json['QueryResult']['QueryID']
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // 100) + 1
    max_requests = min(requests_required, 1000)
    for i in range(max_requests):
        first_record = int(f'{i}01')
        ids_request = base_record_ids_request(
            apikey,
            query_id,
            first_record
        )
        ids_json = ids_request.json()
        ids_list.extend(ids_json)
        state.progress = (i + 1) / max_requests * 100

    return ids_list


def get_cited_references(apikey, ids):
    """Manage API calls and parsing to get the list of cited references.

    :param apikey: str.
    :param ids: list[str].
    :return: list[dict].
    """
    state.progress = 0
    state.current_task = "Retrieving Cited References"
    cited_refs = []
    for i, document in enumerate(ids):
        initial_cited_refs_response = cited_references_request(apikey, document)
        # Worst (but rare) case of receiving an internal server error
        if initial_cited_refs_response.status_code == 500:
            initial_cited_refs_json = {
                "Data": [],
                "QueryResult": {"RecordsFound": 0}
            }
        else:
            initial_cited_refs_json = initial_cited_refs_response.json()
        for cited_ref in initial_cited_refs_json['Data']:
            cited_refs.append(cited_ref)
        total_results = initial_cited_refs_json['QueryResult']['RecordsFound']
        requests_required = ((total_results - 1) // 100) + 1

        if requests_required > 1:
            for j in range(1, requests_required):
                first_record = int(f'{j}01')
                subsequent_cited_refs_response = cited_references_request(
                    apikey,
                    document,
                    first_record
                )
                subsequent_cited_refs_json = subsequent_cited_refs_response.json()
                cited_refs.extend(subsequent_cited_refs_json['Data'])
        state.progress = (i + 1) / len(ids) * 100

    return cited_refs


def enrich_with_wos_metadata(apikey, refs_list):
    """Manage API calls and parsing to get the full record metadata
    fields.

    :param apikey: str.
    :param refs_list: list[str].
    :return: list[dict].
    """
    state.progress = 0
    state.current_task = "Enriching cited references metadata"
    ut_list = [ref['UID'] for ref in refs_list if 'WOS' in ref['UID']]
    requests_required = ((len(ut_list) - 1) // 100) + 1
    addtl_fields_list = []
    for i in range(requests_required):
        ut_batch = ' '.join(ut_list[i*100:i*100+100])
        wos_record_response = fullrecord_request(apikey, ut_batch)
        wos_record_json = wos_record_response.json()
        for record in wos_record_json['Data']['Records']['records']['REC']:
            addtl_fields_list.append(parse_metadata(record))
        state.progress = (i + 1) / requests_required * 100

    return addtl_fields_list


def parse_metadata(record):
    """Parse JSON for required metadata fields.

    :param record: dict.
    :return: dict.
    """
    ut = record['UID']
    if isinstance(record['static_data'], dict):
        if isinstance(record['static_data']['summary'], dict):
            if 'publishers' in record['static_data']['summary']:
                publisher = parse_publisher(
                    record['static_data']['summary']['publishers']
                )
    else:
        publisher = ''

    return {
        'UID': ut,
        'Publisher': publisher
    }


def parse_publisher(publisher_json):
    """Fetch specifically the publisher name out of the relevant JSON
    fragment.

    :param publisher_json: dict.
    :return: str.
    """
    if isinstance(publisher_json['publisher']['names']['name'], dict):
        return publisher_json['publisher']['names']['name']['full_name']
    return ','.join(name['full_name'] for name in publisher_json['publisher']['names']['name'])
