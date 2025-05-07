"""
Manage all the data operations: the main function that gets executed
after the 'run' button is pressed, data retrieval through the APIs
and parsing the required metadata fields.
"""

from datetime import date
from collections import Counter
import pandas as pd
from api_operations import (
    base_records_api_call,
    citing_policy_docs_empty_query,
    citing_policy_ids_api_call,
    policy_docs_api_call_by_ids,
    wos_pubyear_call,
    pci_pubyear_call
)
from visualizations import (
    visualize_wos_data,
    visualize_trends_data
)


def run_button_wos(search_query: str) -> tuple[str, tuple]:
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations - Scholarly Documents tab."""

    # Send initial API call to get the number of requests to paginate
    base_records = retrieve_base_records(search_query)

    # Retrieve citing policy document ids
    for i, record in enumerate(base_records):
        if record['times_cited'] != 0:
            print(f'Retrieving citing policy document IDs for the record '
                  f'{record['ut']}: {i+1} of {len(base_records)}')
            record['citing_policy_documents'] = retrieve_citing_policy_docs_ids(record)

    # Retrieve policy documents metadata
    complete_policy_docs_list = []
    for record in base_records:
        if 'citing_policy_documents' in record:
            complete_policy_docs_list.extend(record['citing_policy_documents'])
            record['citing_policy_documents'] = ' '.join(record['citing_policy_documents'])
    complete_policy_docs_list = list(set(complete_policy_docs_list))

    policy_metadata = retrieve_policy_docs_from_ids(complete_policy_docs_list)

    base_records.sort(key=lambda x: x['times_cited'], reverse=True)

    df = pd.DataFrame(base_records)
    df2 = pd.DataFrame(policy_metadata)

    # Save the data to a file
    df3 = pd.DataFrame({'Search Query': [search_query]}, index=None)
    safe_search_query = (search_query.replace("*", "").replace("?", "")
                         .replace('"', ''))
    safe_filename = f'{safe_search_query} - {date.today()}.xlsx'
    with pd.ExcelWriter(f'downloads/woscc/{safe_filename}') as writer:
        df.to_excel(writer, sheet_name='Base Records', index=False)
        df2.to_excel(writer, sheet_name='Citing Policy Documents', index=False)
        df3.to_excel(writer, sheet_name='Search Query', index=False)

    # Create the plot
    plots = visualize_wos_data(df, df2, search_query)

    return safe_filename, plots


def run_button_trends(search_query: str) -> tuple[str, tuple]:
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations - Trends tab."""

    # Retrieve trends data
    wos_years, pci_years = retrieve_trends_data(search_query)

    df = pd.DataFrame(wos_years)
    df2 = pd.DataFrame(pci_years)

    df = df.merge(df2, how='outer', on='year')
    df = df.sort_values(by='year', ascending=True)

    # Save the data to a file
    df2 = pd.DataFrame({'Search Query': [search_query]}, index=None)
    safe_search_query = (search_query.replace("*", "").replace("?", "")
                         .replace('"', '').replace("/", ''))
    safe_filename = f'{safe_search_query} - {date.today()}.xlsx'
    with pd.ExcelWriter(f'downloads/trends/{safe_filename}') as writer:
        df.to_excel(writer, sheet_name='Trends', index=False)
        df2.to_excel(writer, sheet_name='Search Query', index=False)

    # Create the plot
    plots = visualize_trends_data(df, search_query)

    return safe_filename, plots


def retrieve_base_records(search_query: str) -> list:
    """Receive a search query, return the list of Web of Science Core
    Collection documents in it."""

    records = []
    initial_json = base_records_api_call(search_query)
    records.extend(fetch_base_record_metadata(initial_json))
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // 100) + 1
    max_requests = min(requests_required, 1000)
    print(f'Web of Science API requests required: {requests_required}.')

    # Send actual API calls to get the base documents metadata
    for i in range(1, max_requests):
        subsequent_json = base_records_api_call(search_query, 100*i+1)
        records.extend(fetch_base_record_metadata(subsequent_json))
        print(f'Request {i + 1} of {max_requests} complete.')

    return records


def retrieve_policy_docs_from_ids(doc_ids: list) -> list:
    """Manage API calls and parsing policy documents metadata from a
    list of their IDs."""

    policy_docs_metadata = []
    requests_required = ((len(doc_ids) - 1) // 100) + 1
    for i in range(requests_required):
        policy_json = policy_docs_api_call_by_ids(doc_ids[i*100:(i+1)*100])
        for policy_doc in policy_json['Data']['Records']['records']['REC']:
            print(policy_doc['UID'])
            policy_docs_metadata.append(fetch_policy_docs_metadata(policy_doc))
        print(f'Finally, retrieving full policy documents metadata: request '
              f'{i+1} of {requests_required}')

    return policy_docs_metadata


def retrieve_trends_data(search_query: str) -> tuple:
    """Send API calls to both Web of Science Core Collection for
    scholarly document records and to Policy Citation Index for policy
    document records, analyze their publication dates and return as a
    list."""

    wos_years = retrieve_wos_trend(search_query)
    pci_years = retrieve_pci_trend(search_query)

    return wos_years, pci_years


def retrieve_wos_trend(search_query: str) -> list:
    """Retrieve the number of Web of Science documents by publication
    years."""

    pub_years = []
    initial_wos_json = wos_pubyear_call(search_query)
    if initial_wos_json['Data']['Records']['records']:
        pub_years.extend(
            record['static_data']['summary']['pub_info']['pubyear']
            for record
            in initial_wos_json['Data']['Records']['records']['REC']
        )
        total_results = initial_wos_json['QueryResult']['RecordsFound']
        requests_required = ((total_results - 1) // 100) + 1
        max_requests = min(requests_required, 1000)
        print(f'Web of Science Core Collection API requests required: '
              f'{requests_required}.')

        for i in range(1, max_requests):
            subsequent_wos_json = wos_pubyear_call(search_query, i * 100 + 1)
            pub_years.extend(
                record['static_data']['summary']['pub_info']['pubyear']
                for record
                in subsequent_wos_json['Data']['Records']['records']['REC']
            )
            print(f'WoS Core request {i + 1} of {max_requests} complete.')

    return [{'year': k, 'wos': v} for k, v in Counter(pub_years).items()]


def retrieve_pci_trend(search_query: str) -> list:
    """Retrieve the number of policy documents by their publication
    years."""

    pub_years = []
    initial_pci_json = pci_pubyear_call(search_query)
    if initial_pci_json['Data']['Records']['records']:
        for record in initial_pci_json['Data']['Records']['records']['REC']:
            pub_years.append(record['static_data']['summary']['pub_info']['pubyear'])
        total_results = initial_pci_json['QueryResult']['RecordsFound']
        requests_required = ((total_results - 1) // 100) + 1
        max_requests = min(requests_required, 1000)
        print(f'Policy Citation Index API requests required: '
              f'{requests_required}.')

        for i in range(1, max_requests):
            subsequent_dii_json = pci_pubyear_call(search_query, i * 100 + 1)
            for record in subsequent_dii_json['Data']['Records']['records']['REC']:
                pub_years.append(record['static_data']['summary']['pub_info']['pubyear'])
            print(f'PCI request {i + 1} of {max_requests} complete.')

    return [{'year': k, 'pci': v} for k, v in Counter(pub_years).items()]


def fetch_base_record_metadata(json: dict) -> list[dict]:
    """Fetch the UT and Times Cited fields for each of the base
    records."""

    records = []
    for record in json['Data']['Records']['records']['REC']:
        ut = record['UID']
        pub_year = record['static_data']['summary']['pub_info']['pubyear']
        silo_tc = (
            record['dynamic_data']['citation_related']['tc_list']['silo_tc']
        )
        names_section = record['static_data']['summary']['names']
        times_cited = fetch_times_cited(silo_tc)
        authors = fetch_author_names(names_section)
        records.append({
            'ut': ut,
            'pub_year': pub_year,
            'times_cited': times_cited,
            'authors': authors
        })

    return records


def fetch_times_cited(silo_tc: list) -> int:
    """Fetch the Times Cited field for each of the base records."""

    for database in silo_tc:
        if database['coll_id'] == 'PCI':
            return database['local_count']
    return 0


def fetch_author_names(names_json) -> str:
    """Retrieve the names of the authors."""

    if isinstance(names_json['name'], dict):
        if names_json['name']['role'] == 'author':
            return names_json['name']['full_name']
        return ''
    return '; '.join([n['full_name'] for n in names_json['name'] if n['role']
                      == 'author'])


def retrieve_citing_policy_docs_ids(rec: dict) -> list[str]:
    """Retrieve the CITING document IDs for each of the CITED documents
    that have at least 1 citation, save the ID of each of them that
    belongs to Policy Citation Index database."""

    citing_data = citing_policy_docs_empty_query(rec)
    citing_query_id = citing_data['QueryResult']['QueryID']
    total_citing_records = citing_data['QueryResult']['RecordsFound']
    citing_requests_required = ((total_citing_records - 1) // 100) + 1
    citing_policy_docs_ids = []
    for i in range(citing_requests_required):
        citing_uts = citing_policy_ids_api_call(citing_query_id, 100*i+1)
        for citing_ut in citing_uts:
            if citing_ut.split(':')[0] == 'PCI':
                citing_policy_docs_ids.append(citing_ut)

    return citing_policy_docs_ids


def fetch_policy_docs_metadata(policy_doc: dict) -> dict:
    """Parse policy document metadata for required fields."""

    ut = policy_doc['UID']
    summary_section = policy_doc['static_data']['summary']
    title = fetch_policy_doc_title(summary_section['titles'])
    source_name = fetch_policy_source_title(summary_section['titles'])

    doc_type = summary_section['doctypes']['doctype']
    publisher_section = summary_section['publishers']['publisher']
    source_type = fetch_policy_source_type(publisher_section)
    source_country = fetch_policy_source_country(publisher_section)
    names_section = policy_doc['static_data']['summary']['names']
    citing_author_names  = fetch_names(names_section)

    pub_year = policy_doc['static_data']['summary']['pub_info']['pubyear']

    return {
        'UT': ut,
        'title': title,
        'source_name': source_name,
        'doc_type': doc_type,
        'source_type': source_type,
        'source_country': source_country,
        'citing_author_names': citing_author_names,
        'publication_year': pub_year,
    }


def fetch_policy_doc_title(title_json: dict) -> str:
    """Fetch the policy document title from the relevant json
    section."""

    if isinstance(title_json['title'], list):
        for title in title_json['title']:
            if title['type'] == 'item':
                return title['content']

    if title_json['title']['type'] == 'item':
        return title_json['title']['content']


def fetch_policy_source_title(title_json: dict) -> str:
    """Fetch the policy source title from the relevant json
    section."""

    if isinstance(title_json['title'], list):
        for title in title_json['title']:
            if title['type'] == 'source':
                return title['content']

    if title_json['title']['type'] == 'source':
        return title_json['title']['content']


def fetch_policy_source_type(publisher_json: dict) -> str:
    """Fetch the policy source type from the relevant json
    section."""

    if 'type' in publisher_json:
        return publisher_json['type']

    return ''


def fetch_policy_source_country(publisher_json: dict) -> str:
    """Fetch the policy source country from the relevant json
    section."""

    if 'address_spec' in publisher_json:
        if 'country' in publisher_json['address_spec']:
            return publisher_json['address_spec']['country']

    return ''


def fetch_names(names_json: dict) -> str:
    """Fetch the inventors and assignees names from the relevant json
    section."""

    if 'name' in names_json:
        if isinstance(names_json['name'], list):
            return '; '.join(
                name['display_name'] for name in names_json['name']
                if name['role'] == 'author'
            )

        if names_json['name']['role'] == 'author':
            return names_json['name']['display_name']

    return ''
