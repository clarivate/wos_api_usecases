"""
Manage all the data operations: the main function that gets executed
after the 'run' button is pressed, data retrieval through the APIs
and parsing the required metadata fields.
"""

from datetime import date
import requests
import pandas as pd
from api_operations import base_record_ids_request, cited_references_request, fullrecord_request
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

    df = pd.DataFrame(cited_refs, index=None)
    df['TimesCited'] = pd.to_numeric(df['TimesCited'])
    df2 = pd.DataFrame(addtl_fields_list, index=None)
    df = pd.merge(df, df2, on='UID', how='left')
    df3 = pd.DataFrame({'Search Query': [search_query]}, index=None)
    safe_filename = search_query.replace('*', '').replace('"', '')

    with pd.ExcelWriter(f'downloads/{safe_filename} - {date.today()}.xlsx') as writer:
        df.to_excel(writer, sheet_name='Cited References', index=False)
        df3.to_excel(writer, sheet_name='Search Query', index=False)

    plots = visualize_data(df, search_query)

    return f'{safe_filename} - {date.today()}.xlsx', plots


def get_base_records_ids(apikey, search_query):
    """Manage API calls and parsing to get the list of base record ids.

    :param apikey: str.
    :param search_query: str.
    :return: list[str].
    """
    ids_list = []
    initial_json = requests.get(
        url=f'https://wos-api.clarivate.com/api/wos/?databaseId=WOS&usrQuery='
            f'{search_query}&count=0&firstRecord=1',
        headers={'X-Apikey': apikey},
        timeout=16
    ).json()
    query_id = initial_json['QueryResult']['QueryID']
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // 100) + 1
    max_requests = min(requests_required, 1000)
    print(f'Base document IDs API requests required: {requests_required}.')
    for i in range(max_requests):
        first_record = int(f'{i}01')
        ids_json = base_record_ids_request(
            apikey,
            query_id,
            first_record
        )
        for record in ids_json:
            ids_list.append(record)
        print(f'Base documents API request {i + 1} of {max_requests} '
              f'complete.')

    return ids_list


def get_cited_references(apikey, ids):
    """Manage API calls and parsing to get the list of cited references.

    :param apikey: str.
    :param ids: list[str].
    :return: list[dict].
    """
    cited_refs = []
    for i, document in enumerate(ids):
        print(f'Retrieving cited references for record {document}, '
              f'request {i + 1} out of {len(ids)}')
        initial_cited_refs_json = cited_references_request(apikey, document)
        for cited_ref in initial_cited_refs_json['Data']:
            cited_refs.append(cited_ref)
        total_results = initial_cited_refs_json['QueryResult']['RecordsFound']
        requests_required = ((total_results - 1) // 100) + 1

        if requests_required > 1:
            for j in range(1, requests_required):
                first_record = int(f'{j}01')
                subsequent_cited_refs_json = cited_references_request(
                    apikey,
                    document,
                    first_record
                )
                for cited_ref in subsequent_cited_refs_json['Data']:
                    cited_refs.append(cited_ref)

    return cited_refs


def enrich_with_wos_metadata(apikey, refs_list):
    """Manage API calls and parsing to get the full record metadata
    fields.

    :param apikey: str.
    :param refs_list: list[str].
    :return: list[dict].
    """
    ut_list = [ref['UID'] for ref in refs_list if 'WOS' in ref['UID']]
    requests_required = ((len(ut_list) - 1) // 100) + 1
    print(f'Finally, last {requests_required} requests to enrich the cited '
          f'references metadata with Web of Science document metadata.')
    addtl_fields_list = []
    for i in range(requests_required):
        print(f'Processing default endpoint API request {i+1} of '
              f'{requests_required}.')
        ut_batch = ' '.join(ut_list[i*100:i*100+100])
        wos_record_json = fullrecord_request(apikey, ut_batch)
        for record in wos_record_json['Data']['Records']['records']['REC']:
            print(record['UID'])
            addtl_fields_list.append(parse_metadata(record))

    return addtl_fields_list


def parse_metadata(record):
    """Parse JSON for required metadata fields.

    :param record: dict.
    :return: dict.
    """
    ut = record['UID']
    print(ut) # comment or uncomment for debugging
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
    """Fetch specificially the publisher name out of the relevant JSON
    fragment.

    :param publisher_json: dict.
    :return: str.
    """
    if isinstance(publisher_json['publisher']['names']['name'], dict):
        return publisher_json['publisher']['names']['name']['full_name']
    return ','.join(name['full_name'] for name in publisher_json['publisher']['names']['name'])
