"""
Manage all the data processing functions. These include parsing JSON
objects returned by the API for required metadata fields, calculate
self-citations, and convert them into Pandas dataframes for
visualizing.
"""

import pandas as pd
from datetime import date
from api_operations import base_records_api_call, citing_records_api_call
from visualizations import visualize_data


def run_button(apikey, search_query):
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations.

    :param apikey: str.
    :param search_query: str.
    :return: str, tuple.
    """

    # Retrieving the base records and parsing their metadata
    cited_records_list = get_cited_records(apikey, search_query)

    # Retrieving the cited records and parsing their metadata
    citation_links_list = get_citation_links(apikey, cited_records_list)

    # Calculating self-citations
    citation_links_list, self_citations = count_self_citations(
        citation_links_list
    )

    # Convert the data into dataframes
    df, df2, df3 = convert_to_df(
        citation_links_list,
        self_citations,
        search_query
    )

    # Save data to file
    safe_filename = search_query.replace('*', '').replace('"', '')
    with pd.ExcelWriter(f'downloads/{safe_filename} - {date.today()}.xlsx') as writer:
        df.to_excel(writer, sheet_name='Citation Links', index=False)
        df2.to_excel(writer, sheet_name='Self-citation rates', index=False)
        df3.to_excel(writer, sheet_name='Search query', index=False)

    # Visualise the data
    plots = visualize_data(df2, search_query)

    return f'{safe_filename} - {date.today()}.xlsx', plots


def get_cited_records(apikey, query):
    """Manage API calls and parsing to get the list of cited
    records.

    :param apikey: str.
    :param query: str.
    :return: list.
    """

    result = []
    initial_json = base_records_api_call(apikey, query)

    for record in initial_json['Data']['Records']['records']['REC']:
        result.append(fetch_cited_metadata(record))
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // 100) + 1
    max_requests = min(requests_required, 1000)
    print(f'Total Web of Science API requests required: {requests_required}.')

    for i in range(1, max_requests):
        first_record = int(f'{i}01')
        subsequent_json = base_records_api_call(
            apikey,
            query,
            first_record
        )

        for record in subsequent_json['Data']['Records']['records']['REC']:
            result.append(fetch_cited_metadata(record))
        print(f'Base Documents: Request {i + 1} of {max_requests} complete.')

    return result


def get_citation_links(apikey, cited_records):
    """Manage API calls and parsing to get the list of citation links.

    :param apikey: str.
    :param cited_records: list.
    :return: list.
    """

    result = []
    for j, cited_record in enumerate(cited_records):
        if cited_record['times_cited'] > 0:
            print(
                f'Citing Documents: retrieving {j + 1} of '
                f'{len(cited_records)}.'
            )

            initial_json = citing_records_api_call(
                apikey,
                cited_record['cited_ut']
            )

            for citing_record in initial_json['Data']['Records']['records']['REC']:
                result.append(
                    fetch_citing_metadata(cited_record, citing_record)
                )

            total_results = initial_json['QueryResult']['RecordsFound']
            requests_required = ((total_results - 1) // 100) + 1

            if requests_required > 1:
                for i in range(1, requests_required):
                    first_record = int(f'{i}01')
                    subsequent_json = citing_records_api_call(
                        apikey,
                        cited_record['cited_ut'],
                        first_record
                    )
                    for citing_record in subsequent_json['Data']['Records']['records']['REC']:
                        result.append(
                            fetch_citing_metadata(cited_record, citing_record)
                        )

    return result


def count_self_citations(links):
    """Count the total number of self-citations at various levels.

    :param links: list.
    :return: list, dict.
    """

    self_citations = {
        'author_names': 0,
        'author_rids': 0,
        'author_orcids': 0,
        'orgs': 0,
        'countries': 0,
        'source': 0
    }

    for link in links:
        for k in self_citations.keys():
            if link[f'cited_{k}'].intersection(link[f'citing_{k}']):
                if 'is_self' not in link.keys():
                    link['is_self'] = True
                self_citations[k] += 1

    return links, self_citations


def fetch_rids(name_json):
    """Retrieve Researcher ID data from the relevant JSON object.

    :param name_json: dict.
    :return: str.
    """

    if 'data-item-ids' in name_json:
        data_item_id = name_json['data-item-ids']['data-item-id']
        if isinstance(data_item_id, dict):
            if data_item_id['id-type'] == 'PreferredRID':
                return data_item_id['content']
        else:
            for item_id in data_item_id:
                if item_id['id-type'] == 'PreferredRID':
                    return item_id['content']
    return set()


def fetch_author_fields(record):
    """Retrieve required author metadata fields from relevant JSON
    section.

    :param record: dict.
    :return: tuple of sets.
    """
    au_names = set()  # Author names field, which can be ambiguous
    au_rids = set()  # Relies on ResearcherID
    au_orcids = set()  # Relies on ORCID
    names_dict = record['static_data']['summary']['names']
    if isinstance(names_dict['name'], dict):
        if 'wos_standard' in names_dict['name']:
            au_names.add(names_dict['name']['wos_standard'])
        if 'data-item-ids' in names_dict['name']:
            au_rids.add(fetch_rids(names_dict['name']))
        if 'orcid_id' in names_dict['name']:
            au_orcids.add(names_dict['name']['orcid_id'])
    else:
        for person_name in names_dict['name']:
            if 'wos_standard' in person_name:
                au_names.add(person_name['wos_standard'])
            if 'data-item-ids' in person_name:
                au_rids.add(fetch_rids(person_name))
            if 'orcid_id' in person_name:
                au_orcids.add(person_name['orcid_id'])
    return au_names, au_rids, au_orcids


def fetch_organizations(address_json):
    """Retrieve country metadata fields from each WoS document record
    obtained via API.

    :param address_json: dict from API JSON.
    :return: set of str.
    """
    org_names = set()
    if address_json['count'] == 0:
        return org_names
    if isinstance(address_json['address_name'], dict):
        org_dict = address_json['address_name']['address_spec']
        if 'organization' in org_dict:
            for org in org_dict['organizations']['organization']:
                if org['pref'] == 'Y':
                    org_names.add(org['content'])
    else:
        for affiliation in address_json['address_name']:
            if 'organization' in affiliation['address_spec']:
                for org in affiliation['address_spec']['organizations']['organization']:
                    if org['pref'] == 'Y':
                        org_names.add(org['content'])
    return org_names


def fetch_countries(address_json):
    """Retrieve country metadata fields from the relevant JSON section.

    :param address_json: dict.
    :return: set.
    """

    cu_names = set()
    if 'address_name' in address_json.keys():
        if isinstance(address_json['address_name'], dict):
            cu_names.add(address_json['address_name']['address_spec']['country'])
            return cu_names
        for affiliation in address_json['address_name']:
            cu_names.add(affiliation['address_spec']['country'])
        return cu_names
    return cu_names


def fetch_source(record):
    """Retrieve source title metadata field from relevant JSON section.

    :param record: dict.
    :return: set.
    """
    src_name = set()
    for title in record['static_data']['summary']['titles']['title']:
        if title['type'] == 'source':
            src_name.add(title['content'])
            break

    return src_name


def fetch_times_cited(tc_json):
    """Fetch the times cited counts from the document metadata.

    :param tc_json: dict.
    :return: int or str.
    """
    for database in tc_json:
        if database['coll_id'] == 'WOS':
            return database['local_count']
    return 0


def fetch_cited_metadata(rec):
    """Retrieve the necessary metadata fields of cited documents from a
    deeply nested JSON, return them as a simple dict.

    :param rec: dict.
    :return: dict.
    """
    ut = rec['UID']
    # print(ut)  # comment/uncomment for debugging
    address = rec['static_data']['fullrecord_metadata']['addresses']
    citations = rec['dynamic_data']['citation_related']['tc_list']['silo_tc']

    author_names, author_rids, author_orcids = fetch_author_fields(rec)
    organizations_names = fetch_organizations(address)
    country_names = fetch_countries(address)
    source_name = fetch_source(rec)
    times_cited = fetch_times_cited(citations)
    return {
        'cited_ut': ut,
        'cited_author_names': author_names,
        'cited_author_rids': author_rids,
        'cited_author_orcids': author_orcids,
        'cited_orgs': organizations_names,
        'cited_countries': country_names,
        'cited_source': source_name,
        'times_cited': times_cited
    }


def fetch_citing_metadata(cited_rec, citing_rec):
    """Retrieve the necessary metadata fields of citing documents from
    a deeply nested JSON, add them into the dict of the cited record.

    :param cited_rec: dict.
    :param citing_rec: dict.
    :return: dict.
    """
    result = cited_rec.copy()
    ut = citing_rec['UID']
    # print(ut)  # comment/uncomment for debugging
    address = citing_rec['static_data']['fullrecord_metadata']['addresses']

    author_names, author_rids, author_orcids = fetch_author_fields(citing_rec)
    organizations_names = fetch_organizations(address)
    country_names = fetch_countries(address)
    source_name = fetch_source(citing_rec)

    result['citing_ut'] = ut
    result['citing_author_names'] = author_names
    result['citing_author_rids'] = author_rids
    result['citing_author_orcids'] = author_orcids
    result['citing_orgs'] = organizations_names
    result['citing_countries'] = country_names
    result['citing_source'] = source_name

    return result


def convert_to_df(links, self_citations, query):
    df = pd.DataFrame(links)

    non_set_cols = [
        'cited_ut',
        'times_cited',
        'citing_ut',
        'is_self']

    for col in df.drop(non_set_cols, axis=1).columns:
        df[col] = df[col].apply(lambda x: '; '.join(x))

    df2 = pd.DataFrame(
        data={
            'Coauthor Name': [
                self_citations['author_names'],
                len(links) - self_citations['author_names'],
                len(links),
                f'{((self_citations['author_names'] / len(links)) * 100):.1f}%'
            ],
            'ResearcherID': [
                self_citations['author_rids'],
                len(links) - self_citations['author_rids'],
                len(links),
                f'{((self_citations['author_rids'] / len(links)) * 100):.1f}%'
            ],
            'ORCID': [
                self_citations['author_orcids'],
                len(links) - self_citations['author_orcids'],
                len(links),
                f'{((self_citations['author_orcids'] / len(links)) * 100):.1f}%'
            ],
            'Organization': [
                self_citations['orgs'],
                len(links) - self_citations['orgs'],
                len(links),
                f'{((self_citations['orgs'] / len(links)) * 100):.1f}%'
            ],
            'Country': [
                self_citations['countries'],
                len(links) - self_citations['countries'],
                len(links),
                f'{((self_citations['countries'] / len(links)) * 100):.1f}%'
            ],
            'Publication Source': [
                self_citations['source'],
                len(links) - self_citations['source'],
                len(links),
                f'{((self_citations['source'] / len(links)) * 100):.1f}%'
            ]
        },
        index=[
            'Self-citations',
            'External Citations',
            'Total Citations',
            '% Self-Citations']
    )

    df3 = pd.DataFrame({'Search Query': [query]}, index=None)

    return df, df2, df3
