"""
Fetch necessary metadata fields from Web of Science records.
"""

import state
from datetime import date
from api_operations import retrieve_wos_metadata_via_api, retrieve_cited_refs_via_api


def run_button(apikey, search_query, cited_refs):
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations

    :param apikey: str.
    :param search_query: str.
    :param cited_refs: bool.
    :return: str.
    """

    documents_list = []

    state.progress = 0
    state.current_task = "Retrieving Web of Science documents"

    initial_json = retrieve_wos_metadata_via_api(
        apikey,
        search_query,
    )

    for record in initial_json['Data']['Records']['records']['REC']:
        documents_list.append(fetch_expanded_metadata(record))
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // 100) + 1
    max_requests = min(requests_required, 1000)
    for i in range(1, max_requests):
        subsequent_json = retrieve_wos_metadata_via_api(
            apikey,
            search_query,
            int(f'{i}01')
        )
        for record in subsequent_json['Data']['Records']['records']['REC']:
            documents_list.append(fetch_expanded_metadata(record))
        state.progress = (i + 1) / max_requests * 100

    safe_search = search_query.replace('*', '').replace('"', '')

    if cited_refs:
        documents_list = enrich_with_cited_references(apikey, documents_list)
        safe_filename = (f'{safe_search} - with cited references -'
                         f'{date.today()}.txt')
    else:
        safe_filename = f'{safe_search} - {date.today()}.txt'

    with open(f'downloads/{safe_filename}', 'w', encoding='UTF8') as writer:
        writer.write('\t'.join(documents_list[0].keys()))
        writer.write('\n')
        for doc in documents_list:
            writer.write(f"{'\t'.join([str(v) for v in doc.values()])}\n")

    state.progress = 0
    state.current_task = ""

    return f'{safe_filename}'


def fetch_author_names(names_json):
    """Retrieve the names of the authors.

    :param names_json: dict.
    :return: str.
    """
    if isinstance(names_json['name'], dict):
        if names_json['name']['role'] == 'author':
            return names_json['name']['full_name']
        return ''
    return ', '.join([n['full_name'] for n in names_json['name'] if n['role']
                      == 'author'])


def fetch_author_affiliation_links(address_json):
    """Retrieve the author names, but for the 'C1' field that stores
    them in relation to specific affiliations.

    :param address_json: dict.
    :return: str.
    """
    address = address_json['address_spec']['full_address']
    if 'names' not in address_json.keys():
        return f'[] {address}'
    if isinstance(address_json['names']['name'], list):
        names_list = []
        for name in address_json['names']['name']:
            try:
                names_list.append(name['full_name'])
            except KeyError:
                # Uncomment the following string for debugging:if
                # print('Missing Author Full name in the record: {address_json}')
                pass
        return f"[{'; '.join(names_list)}] {address}"
    name = address_json['names']['name']['full_name']
    return f"[{name}] {address}"


def fetch_affiliations(address_json):
    """Retrieve the names of the authors-affiliations links.

    :param address_json: dict.
    :return: str.
    """

    # When there are no address fields on the record
    if address_json['count'] == 0:
        return ''

    # When there are multiple address fields on the record
    if isinstance(address_json['address_name'], list):
        au_affil_list = []
        for address_subfield in address_json['address_name']:
            au_affil_list.append(
                fetch_author_affiliation_links(address_subfield)
            )
        return '; '.join(au_affil_list)

    # When there is only one address field on the record
    return fetch_author_affiliation_links(address_json['address_name'])


def fetch_titles(titles_json):
    """Retrieve the source title and document title.

    :param titles_json: dict.
    :return: str, str.
    """
    return ([t['content'] for t in titles_json if t['type'] == 'source'][0],
            [t['content'] for t in titles_json if t['type'] == 'item'][0])


def fetch_keywords(keywords_json):
    """Retrieve the author keywords and keywords plus

    :param keywords_json: dict.
    :return: str.
    """
    if isinstance(keywords_json['keyword'], str):
        return keywords_json['keyword']
    return '; '.join(str(e) for e in keywords_json['keyword'])


def fetch_abstract(fr_metadata):
    """Retrieve the abstract of the document.

    :param fr_metadata: dict.
    :return: str.
    """
    if 'abstracts' in fr_metadata.keys():
        abstract = fr_metadata['abstracts']['abstract']['abstract_text']
        if 'p' in abstract.keys():
            if isinstance(abstract['p'], list):
                return "  ".join(abstract['p'])
            return abstract['p']
        return ''
    return ''


def fetch_times_cited(tc_json):
    """Retrieve the times cited counts.

    :param tc_json: dict
    :return: str or int.
    """
    for database in tc_json:
        if database['coll_id'] == 'WOS':
            return database['local_count']
    return ''


def fetch_expanded_metadata(record):
    """Parse the metadata fields required for VOSviewer that are
    available via Web of Science Expanded API

    :param record: dict.
    :return: dict.
    """
    ut = record['UID']
    py = record['static_data']['summary']['pub_info']['pubyear']
    fullrecord_metadata = record['static_data']['fullrecord_metadata']
    authors = fetch_author_names(record['static_data']['summary']['names'])
    c1 = fetch_affiliations(fullrecord_metadata['addresses'])
    source_title, doc_title = fetch_titles(
        record['static_data']['summary']['titles']['title']
    )
    if 'keywords' in fullrecord_metadata:
        keywords = fetch_keywords(fullrecord_metadata['keywords'])
    else:
        keywords = ''
    if 'keywords_plus' in record['static_data']['item'].keys():
        keywords_plus = fetch_keywords(
            record['static_data']['item']['keywords_plus']
        )
    else:
        keywords_plus = ''
    abstract = fetch_abstract(fullrecord_metadata)
    tc = fetch_times_cited(
        record['dynamic_data']['citation_related']['tc_list']['silo_tc']
    )

    return {
        'UT': ut,
        'PY': py,
        'AU': authors,
        'SO': source_title,
        'C1': c1,
        'TI': doc_title,
        'DE': keywords,
        'ID': keywords_plus,
        'AB': abstract,
        'TC': tc
    }


def enrich_with_cited_references(apikey, records):
    """Adds cited references metadata to each of the records.

    :param apikey: str.
    :param records: list.
    :return: list.
    """

    state.progress = 0
    state.current_task = "Retrieving Cited References metadata"

    for i, record in enumerate(records):
        cited_ref_data = retrieve_cited_refs_via_api(apikey, record['UT'])
        record['CR'] = '; '.join(fetch_cited_refs_metadata(cited_ref) for
                                 cited_ref in cited_ref_data['Data'])
        state.progress = (i + 1) / len(records) * 100

    return records


def fetch_cited_refs_metadata(cited_ref):
    """Retrieves cited reference metadata that's compatible with
    VOSviewer.

    :param cited_ref: dict.
    :return: str.
    """
    cited_ref_list = []
    if 'CitedAuthor' in cited_ref:
        cited_ref_list.append(cited_ref['CitedAuthor'].replace(',', ''))
    if 'Year' in cited_ref:
        cited_ref_list.append(cited_ref['Year'])
    if 'CitedWork'in cited_ref:
        cited_ref_list.append(cited_ref['CitedWork'])
    if 'Volume' in cited_ref:
        cited_ref_list.append(f'V{cited_ref["Volume"]}')
    if 'Page' in cited_ref:
        cited_ref_list.append(f'P{cited_ref["Page"]}')
    if 'DOI' in cited_ref:
        cited_ref_list.append(f'DOI {cited_ref["DOI"]}')
    return ', '.join(cited_ref_list)
