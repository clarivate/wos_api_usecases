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
    citing_patents_empty_query,
    citing_patents_ids_api_call,
    patents_api_call_by_ids,
    patents_api_call_by_query,
    wos_pubyear_call,
    dii_pubyear_call
)
from visualizations import (
    visualize_wos_data,
    visualize_dii_data,
    visualize_trends_data
)


def run_button_wos(search_query: str) -> tuple[str, tuple]:
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations - Scholarly Documents tab."""

    # Send initial API call to get the number of requests to paginate
    base_records = retrieve_base_records(search_query)

    # Retrieve citing patent ids
    for i, record in enumerate(base_records):
        if record['times_cited'] != 0:
            print(
                f'Retrieving citing patent IDs for the record '
                f'{record['ut']}: {i+1} of {len(base_records)}'
            )
            record['citing_inventions'] = retrieve_citing_patent_ids(record)

    # Retrieve patent metadata
    complete_patent_id_list = []
    for record in base_records:
        if 'citing_inventions' in record:
            complete_patent_id_list.extend(record['citing_inventions'])
            record['citing_inventions'] = ' '.join(record['citing_inventions'])
    complete_patent_id_list = list(set(complete_patent_id_list))

    patents_metadata = retrieve_patents_metadata_from_ids(complete_patent_id_list)

    base_records.sort(key=lambda x: x['times_cited'], reverse=True)

    df = pd.DataFrame(base_records)
    df2 = pd.DataFrame(patents_metadata)

    # Save the data to a file
    df3 = pd.DataFrame({'Search Query': [search_query]}, index=None)
    safe_search_query = (search_query.replace("*", "").replace("?", "")
                         .replace('"', ''))
    safe_filename = f'{safe_search_query} - {date.today()}.xlsx'
    with pd.ExcelWriter(f'downloads/woscc/{safe_filename}') as writer:
        df.to_excel(writer, sheet_name='Base Records', index=False)
        df2.to_excel(writer, sheet_name='Citing Inventions', index=False)
        df3.to_excel(writer, sheet_name='Search Query', index=False)

    # Create the plot
    plots = visualize_wos_data(df, df2, search_query)

    return safe_filename, plots


def run_button_dii(search_query: str) -> tuple[str, tuple]:
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations - Inventions tab."""

    # Retrieve patent metadata
    inventions = retrieve_patents_metadata_from_search(search_query)

    df = pd.DataFrame(inventions)

    # Save the data to a file
    df2 = pd.DataFrame({'Search Query': [search_query]}, index=None)
    safe_search_query = (search_query.replace("*", "").replace("?", "")
                         .replace('"', ''))
    safe_filename = f'{safe_search_query} - {date.today()}.xlsx'
    with pd.ExcelWriter(f'downloads/dii/{safe_filename}') as writer:
        df.to_excel(writer, sheet_name='Patent Families', index=False)
        df2.to_excel(writer, sheet_name='Search Query', index=False)

    # Create the plot
    plots = visualize_dii_data(df, search_query)

    return safe_filename, plots


def run_button_trends(search_query: str) -> tuple[str, tuple]:
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations - Trends tab."""

    # Retrieve trends data
    wos_years, dii_pubyears, dii_prtyyears = retrieve_trends_data(search_query)

    df = pd.DataFrame(wos_years)
    df2 = pd.DataFrame(dii_pubyears)
    df3 = pd.DataFrame(dii_prtyyears)

    df = df.merge(df2, how='outer', on='year')
    df = df.merge(df3, how='outer', on='year')
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


def retrieve_patents_metadata_from_ids(patents_ids: list) -> list:
    """Manage API calls and parsing patent metadata from a list of
    their IDs."""

    patents_metadata = []
    requests_required = ((len(patents_ids) - 1) // 100) + 1
    for i in range(requests_required):
        patents_json = patents_api_call_by_ids(patents_ids[i*100:(i+1)*100])
        for patent_rec in patents_json['Data']['Records']['records']['REC']:
            patents_metadata.append(fetch_patents_metadata(patent_rec))
        print(f'Finally, retrieving full patent metadata: request {i+1} of '
              f'{requests_required}')

    return patents_metadata


def retrieve_patents_metadata_from_search(search_query: str) -> list:
    """Manage API calls and parsing patent metadata from a search
    query."""

    patent_records = []
    initial_json = patents_api_call_by_query(search_query)
    for record in initial_json['Data']['Records']['records']['REC']:
        patent_records.append(fetch_patents_metadata(record))
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // 100) + 1
    max_requests = min(requests_required, 1000)
    print(f'Web of Science API requests required: {requests_required}.')

    # Send actual API calls to get the base documents metadata
    for i in range(1, max_requests):
        subsequent_json = patents_api_call_by_query(search_query, 100*i+1)
        for record in subsequent_json['Data']['Records']['records']['REC']:
            patent_records.append(fetch_patents_metadata(record))
        print(f'Request {i + 1} of {max_requests} complete.')

    return patent_records


def retrieve_trends_data(search_query: str) -> tuple:
    """Send API calls to both Web of Science Core Collection for
    scholarly document records and to Derwent Innovations Index for
    patent records, analyze their publication dates and return as a
    list."""

    wos_years = retrieve_wos_trend(search_query)
    dii_pub_years, dii_prty_years = retrieve_dii_trend(search_query)

    return wos_years, dii_pub_years, dii_prty_years


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


def retrieve_dii_trend(search_query: str) -> tuple[list, list]:
    """Retrieve the number of patent documents by their earliest priority
    and publication years."""

    pub_years = []
    prty_years = []
    initial_dii_json = dii_pubyear_call(search_query)
    if initial_dii_json['Data']['Records']['records']:
        for record in initial_dii_json['Data']['Records']['records']['REC']:
            print(record['UID'])
            patent_typ_section = record['static_data']['item']['PatentTyp1']
            pub_years.extend(fetch_patent_pub_year(patent_typ_section))
            prty_years.extend(fetch_earliest_priority_year(patent_typ_section))
        total_results = initial_dii_json['QueryResult']['RecordsFound']
        requests_required = ((total_results - 1) // 100) + 1
        max_requests = min(requests_required, 1000)
        print(f'Derwent Innovations Index API requests required: '
              f'{requests_required}.')

        for i in range(1, max_requests):
            subsequent_dii_json = dii_pubyear_call(search_query, i * 100 + 1)
            for record in subsequent_dii_json['Data']['Records']['records']['REC']:
                patent_typ_section = record['static_data']['item']['PatentTyp1']
                pub_years.extend(fetch_patent_pub_year(patent_typ_section))
                prty_years.extend(fetch_earliest_priority_year(patent_typ_section))
            print(f'DII request {i + 1} of {max_requests} complete.')

    return (
        [{'year': k, 'dii_pubyear': v} for k, v in Counter(pub_years).items()],
        [{'year': k, 'dii_prtyyear': v} for k, v in Counter(prty_years).items()]
    )


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
        if database['coll_id'] == 'DIIDW':
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


def retrieve_citing_patent_ids(rec: str) -> list[str]:
    """Retrieve the CITING document IDs for each of the CITED documents
    that have at least 1 citation, save the ID of each of them that
    belongs to Derwent Innovations Index database."""

    citing_data = citing_patents_empty_query(rec)
    citing_query_id = citing_data['QueryResult']['QueryID']
    total_citing_records = citing_data['QueryResult']['RecordsFound']
    citing_requests_required = ((total_citing_records - 1) // 100) + 1
    citing_patents_ids = []
    for i in range(citing_requests_required):
        citing_uts = citing_patents_ids_api_call(citing_query_id, 100*i+1)
        for citing_ut in citing_uts:
            if citing_ut.split(':')[0] == 'DIIDW':
                citing_patents_ids.append(citing_ut)

    return citing_patents_ids


def fetch_patents_metadata(patent_rec: dict) -> dict:
    """Parse patent metadata for required fields."""

    ut = patent_rec['UID']
    title = fetch_patent_title(patent_rec['static_data']['summary']['titles'])
    names_section = patent_rec['static_data']['summary']['names']['name']
    patent_typ_section = patent_rec['static_data']['item']['PatentTyp1']
    inventor_names, assignee_names = fetch_names(names_section)
    numbers_section = (
        patent_rec['dynamic_data']['cluster_related']['identifiers']
        ['identifier']
    )
    patent_numbers = fetch_patent_numbers(numbers_section)
    granted_patents = ', '.join(
        number for number in patent_numbers.split(', ')
        if number.split('-')[1][0] != "A"
    )
    countries_applied = ', '.join(set(
        number.split('-')[0][:2] for number in patent_numbers.split(', '))
    )
    countries_granted = ''
    if granted_patents:
        countries_granted = ', '.join(set(
            number.split('-')[0][:2] for number in granted_patents.split(', ')
            if number.split('-')[1] != ('W' or 'U' or 'S')
        ))
    quadrilateral_countries = ['US', 'EP', 'CN', 'JP']
    is_quadrilateral = all(
        country in countries_granted for country in quadrilateral_countries
    )

    pub_years = fetch_patent_pub_year(patent_typ_section)
    if pub_years:
        pub_year = min(pub_years)
    else:
        pub_year = None

    earliest_priority_years = fetch_earliest_priority_year(patent_typ_section)
    if earliest_priority_years:
        earliest_priority_year = min(earliest_priority_years)
    else:
        earliest_priority_year = None

    return {
        'UT': ut,
        'title': title,
        'inventor_names': inventor_names,
        'assignee_names': assignee_names,
        'patent_numbers': patent_numbers,
        'granted_patents': granted_patents,
        'countries_applied': countries_applied,
        'countries_granted': countries_granted,
        'is_quadrilateral': is_quadrilateral,
        'publication_year': pub_year,
        'earliest_priority': earliest_priority_year
    }


def fetch_patent_title(title_json: dict) -> str:
    """Fetch the patent title from the relevant json section."""

    if 'content' in title_json['title']:
        patent_title = title_json['title']['content']
        while '  ' in patent_title:
            patent_title = patent_title.replace('  ', ' ')

        return patent_title

    return ''


def fetch_names(names_json: dict) -> tuple:
    """Fetch the inventors and assignees names from the relevant json
    section."""

    return (
        ', '.join(name['display_name'] for name in names_json if name['role'] == 'inventor'),
        ', '.join(name['display_name'] for name in names_json if name['role'] == 'assignee')
    )


def fetch_patent_numbers(numbers_json: dict) -> str:
    """Fetch patent numbers from the relevant json section."""

    return ', '.join(number['value'] for number in numbers_json if (
            number['type'] == 'patent_no' and number['value']
    ))


def fetch_patent_pub_year(patent_typ_json) -> list[int]:
    """Fetch the earliest publication year from the relevant JSON
    section."""

    if isinstance(patent_typ_json, list):
        pub_years = []
        for typ in patent_typ_json:
            if 'BiblioPtTyp1' in typ:
                if 'dt' in typ['BiblioPtTyp1']:
                    pub_years.append(typ['BiblioPtTyp1']['dt']//10000)

        return pub_years

    if 'BiblioPtTyp1' in patent_typ_json:
        if 'dt' in patent_typ_json['BiblioPtTyp1']:
            return [patent_typ_json['BiblioPtTyp1']['dt']//10000]

    return []


def fetch_earliest_priority_year(patent_typ_json) -> list:
    """Fetch the earliest priority year from the relevant JSON
    section."""

    if isinstance(patent_typ_json, list):
        earliest_priorities = []
        for typ in patent_typ_json:
            if 'BiblioPtTyp1' in typ:
                earliest_priorities.extend(
                    parse_patent_type_section(typ['BiblioPtTyp1'])
                )

        return earliest_priorities

    if 'BiblioPtTyp1' in patent_typ_json:
        return parse_patent_type_section(patent_typ_json['BiblioPtTyp1'])

    return []


def parse_patent_type_section(biblio_pt_typ1_json: dict) -> list[int]:
    """Parse the BiblioPtTyp1 section of the patent document's JSON
    record for the earliest priority year."""

    if 'Pris' in biblio_pt_typ1_json:
        priority = biblio_pt_typ1_json['Pris']
        priorities = []
        if 'PriLat' in priority:
            priorities.extend(fetch_pridt_field(priority['PriLat']))
        if 'PriEst' in priority:
            priorities.extend(fetch_pridt_field(priority['PriEst']))
        if 'PriLocs' in priority:
            priorities.extend(
                fetch_irregular_priorities(priority['PriLocs']['PriLoc'])
            )
        if 'PriOths' in priority:
            priorities.extend(
                fetch_irregular_priorities(priority['PriOths']['PriOth'])
            )

        if priorities:
            return [min(priorities)]

    return []


def fetch_irregular_priorities(priority_json) -> list[int]:
    """Parse the PriOths or PriLocs sections for priority date."""

    if isinstance(priority_json, list):
        priorities = []
        for priority in priority_json:
            priorities.extend(fetch_pridt_field(priority))
        return priorities

    return fetch_pridt_field(priority_json)


def fetch_pridt_field(pri_json: dict) -> list:
    """Parse the PriSe JSON object for priority year."""

    if 'PriSe' in pri_json:
        if 'PriDt' in pri_json['PriSe']:
            return [int(pri_json['PriSe']['PriDt'])//10000]

    return []
