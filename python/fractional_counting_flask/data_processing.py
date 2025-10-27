"""
Manage all the data operations: the main function that gets executed
after the 'run' button is pressed, data retrieval through the APIs
and parsing the required metadata fields.
"""

from datetime import date
import state
import pandas as pd
from api_operations import retrieve_wos_metadata
from visualizations import visualize_data


def run_button(apikey, search_query, org_name):
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations

    :param apikey: str.
    :param search_query: str.
    :param org_name: str.
    :return: str, tuple.
    """

    records = []

    state.progress = 0
    state.current_task = "Retrieving Web of Science Documents"

    # Send initial API call to get the number of requests to paginate
    initial_json = retrieve_wos_metadata(apikey, search_query)
    records.extend(initial_json['Data']['Records']['records']['REC'])
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // 100) + 1
    max_requests = min(requests_required, 1000)

    # Send actual API calls
    for i in range(1, max_requests):
        subsequent_json = retrieve_wos_metadata(apikey, search_query, 100*i+1)

        records.extend(subsequent_json['Data']['Records']['records']['REC'])
        state.progress = (i + 1) / max_requests * 100

    # Calculate fractions
    frac_counts = count_fractions(records, org_name)

    # Create dataframes and output file name
    df2, safe_filename = output(frac_counts, search_query, org_name)

    # Create the plot
    plots = visualize_data(df2, search_query, org_name)

    state.progress = 0
    state.current_task = ""

    return f'{safe_filename}.xlsx', plots


def count_fractions(records, our_org):
    """Extract the publication year from the document, check if there
    is one or multiple affiliations in it, and launch one of two
    address analysis functions based on that, then append the results
    to the frac_count list.

    :param records: list.
    :param our_org: str.
    """
    result = []
    for record in records:
        pub_info = record['static_data']['summary']['pub_info']
        addresses = record['static_data']['fullrecord_metadata']['addresses']
        if 'early_access_year' in pub_info:
            pub_year = pub_info['early_access_year']
        else:
            pub_year = pub_info['pubyear']
        if addresses['count'] == 1:
            doc_level_fraction, our_authors_input = \
                single_address_doc_check(record, our_org)
        else:
            doc_level_fraction, our_authors_input = \
                multiaddress_doc_check(record, our_org)
        result.append({
            'UT': record['UID'],
            'Publication_year': pub_year,
            'Our_authors': our_authors_input,
            'Fractional_value': doc_level_fraction})

    return result


def single_address_doc_check(paper, our_org):
    """When there is only one affiliation in the paper. Call the
    function for calculating the author numbers and count our
    organization's fractional output for a given document.

    :param paper: dict.
    :param our_org: str.
    :return: float, list.
    """

    address_dict = paper['static_data']['fullrecord_metadata']['addresses']
    authors = authors_check(paper['static_data']['summary']['names'])
    if not authors:
        return 0, 0
    our_authors = 0
    if 'address_name' in address_dict:
        for org in (
                address_dict['address_name']['address_spec']['organizations']
                ['organization']
        ):
            if 'content' in org:
                if org['content'].lower() == our_org.lower():
                    if 'names' in address_dict['address_name']:
                        our_authors = address_dict['address_name']['names']['count']
    doc_level_fraction = our_authors / authors

    return doc_level_fraction, our_authors


def authors_check(authors_json):
    """Calculate the number of the authors in the document

    :param authors_json: dict.
    :return: int.
    """

    if isinstance(authors_json['name'], dict):
        if authors_json['name']['role'] == "author":
            return 1
        return 0

    return sum(person['role'] == 'author' for person in authors_json['name'])


def multiaddress_doc_check(paper, our_org):
    """Check for a rare case when the number of authors in the document
    is 0, launch the standard_case_address_check function, calculate
    the fractional counting value for the document from the
    total_au_input and authors values returned by that function.

    :param paper: dict.
    :param our_org: str.
    :return fractional_counting_paper: float.
    :return our_authors: int.
    """

    authors = authors_check(paper['static_data']['summary']['names'])
    # A rare case with no authors (i.e., only the "group author")
    if authors == 0:
        doc_level_fraction = 0
        our_authors_input = 0
    else:
        total_au_input, authors, our_authors_input = \
            address_check(paper, authors, our_org)
        doc_level_fraction = total_au_input / authors

    return doc_level_fraction, our_authors_input


def address_check(paper, authors, our_org):
    """Figure out who of the authors are affiliated with our
    organization, launch the standard_case_affiliation_check function,
    calculate the total author input value from individual author input
    values returned by it.

    :param paper: dict.
    :param authors: int.
    :param our_org: str.
    :return: float, int, int.
    """

    our_authors_seq_numbers = set()
    doc_level_fraction = 0
    addresses = paper['static_data']['fullrecord_metadata']['addresses']
    if 'address_name' in addresses:
        for affiliation in addresses['address_name']:
            if 'organizations' in affiliation['address_spec']:
                for org in affiliation['address_spec']['organizations']['organization']:
                    for seq_no in fetch_seq_numbers(affiliation, org, our_org):
                        our_authors_seq_numbers.add(seq_no)

    our_authors = len(our_authors_seq_numbers)
    names = paper['static_data']['summary']['names']
    addresses = paper['static_data']['fullrecord_metadata']['addresses']
    if names['count'] == 1:
        if "addr_no" in names['name']:
            au_affils = str(names['name']['addr_no']).split(' ')
            doc_level_fraction = affiliation_check(addresses, au_affils, our_org)

    else:
        for author in our_authors_seq_numbers:
            au_affils = str(names['name'][int(author)-1]['addr_no']).split(' ')
            doc_level_fraction += affiliation_check(addresses, au_affils, our_org)

    return doc_level_fraction, authors, our_authors


def fetch_seq_numbers(affiliation, org, our_org):
    """Get the sequence number of our organization's authors.

    :params affiliation: dict.
    :params org: dict.
    :params our_org: str.
    :return: list.
    """

    name_match = (org['pref'] == 'Y' and org['content'].lower() ==
                  our_org.lower())

    if 'names' in affiliation:
        if name_match and affiliation['names']['count'] == 1 and \
                affiliation['names']['name']['role'] == 'author':

            return [affiliation['names']['name']['seq_no']]

        if name_match and affiliation['names']['count'] > 1:

            return [
                our_author['seq_no'] for our_author in
                affiliation['names']['name'] if our_author['role'] == 'author'
            ]

    return []


def affiliation_check(addresses_json, au_affils, our_org):
    """For every affiliation, check if it's our organization's
    affiliation, and calculate the individual author's inputs (or, in
    other words, their fractional values of the document).

    :param addresses_json: dict.
    :param au_affils: list.
    :param our_org: str.
    :return au_input: float.
    """

    our_input = 0
    for c_1 in au_affils:
        if 'address_name' in addresses_json:
            affiliation = addresses_json['address_name'][int(c_1) - 1]
            if 'organizations' in affiliation['address_spec']:
                for org in affiliation['address_spec']['organizations']['organization']:
                    if org['pref'] == 'Y' and org['content'].lower() == our_org.lower():
                        our_input += 1 / len(au_affils)

    return our_input


def output(frac_counts, search_query, org_name):
    """Create dataframes, create a safe filename and save data into an
    Excel file.

    :param frac_counts: list[dict].
    :param search_query: str.
    :param org_name: str.
    :return: pd.DataFrame, str.

    """
    # Creating dataframes
    df = pd.DataFrame(frac_counts)
    df2 = (df[['UT', 'Publication_year']].groupby('Publication_year').count())
    df2.rename(columns={'UT': 'Whole Counting'}, inplace=True)
    df2['Fractional Counting'] = (df[['Fractional_value', 'Publication_year']].
                                  groupby('Publication_year').sum())
    df2.reset_index(inplace=True)
    df3 = pd.DataFrame(
        {'Search Query': [search_query], 'Affiliation': [org_name]},
        index=None
    )

    # Save results to an Excel file
    safe_search_query = search_query.replace('"', '').replace('*', '')
    filename = f'fractional counting - {safe_search_query} - {date.today()}'
    if len(filename) > 218:
        safe_filename = filename[:218]
    else:
        safe_filename = filename

    with pd.ExcelWriter(f'downloads/{safe_filename}.xlsx') as writer:
        df.to_excel(writer, sheet_name='Document-level Data', index=False)
        df2.to_excel(writer, sheet_name='Annual Dynamics', index=False)
        df3.to_excel(writer, sheet_name='Query Parameters', index=False)

    return df2, safe_filename
