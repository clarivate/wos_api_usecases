"""
Fetch necessary metadata fields from Grants Index records. ALso fetch
currency rates from the currency converter app or local cache, and
return them as dictionaries.
"""

from datetime import date, datetime, timedelta
import pandas as pd
from api_operations import retrieve_rates_via_api, retrieve_wos_metadata_via_api
from visualizations import visualize_data


def run_button(apikey, search_query):
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations

    :param apikey: str.
    :param search_query: str.
    :return: str, tuple.
    """
    grants_list = []
    usd_rates = get_usd_rates()
    initial_json = retrieve_wos_metadata_via_api(
        apikey,
        search_query,
    )

    for record in initial_json['Data']['Records']['records']['REC']:
        grants_list.append(fetch_data(record, usd_rates))
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // 100) + 1
    max_requests = min(requests_required, 1000)
    print(f'Total Web of Science API requests required: {requests_required}.')
    for i in range(1, max_requests):
        first_record = int(f'{i}01')
        subsequent_json = retrieve_wos_metadata_via_api(
            apikey,
            search_query,
            first_record
        )
        for record in subsequent_json['Data']['Records']['records']['REC']:
            grants_list.append(fetch_data(record, usd_rates))
        print(f'Request {i + 1} of {max_requests} complete.')

    df = pd.DataFrame(grants_list)
    safe_query = search_query.replace('*', '').replace('"', '')
    safe_filename = f'{safe_query} - {date.today()}.xlsx'
    df2 = pd.DataFrame({'Search Query': [search_query]}, index=None)
    with pd.ExcelWriter(f'downloads/{safe_filename}') as writer:
        df.to_excel(writer, sheet_name='Grants Data', index=False)
        df2.to_excel(writer, sheet_name='Search Query', index=False)

    plots = visualize_data(df, search_query)
    return safe_filename, plots


def retrieve_rates_from_table():
    """Get the exchange rates from the locally cached .csv file in case
    the API endpoint doesn't return data.

    :return: dict.
    """
    rates_df = pd.read_csv(filepath_or_buffer='currencies.csv',
                           skiprows=2,
                           index_col='Currency')

    return rates_df.to_dict(orient='dict')['Rate VS USD']


def get_usd_rates():
    """Retrieve exchange rates to convert various currencies into USD.

    :return: dict.
    """
    tod = date.today()
    with open('currencies.csv', 'r', encoding='utf-8') as reading:
        updated = datetime.strptime(
            reading.readline().split(',')[1][:-1], '%m/%d/%Y'
        ).date()
    if tod - updated < timedelta(days=1):
        return retrieve_rates_from_table()
    return retrieve_rates_via_api()


def fetch_names(names_json):
    """Retrieve the names of the principal investigator and other grant
    participants, if any.

    :param names_json: dict.
    :return: str, str.
    """
    pr_inv = ''
    other_nms = ''
    if names_json['count'] > 0:
        if names_json['count'] == 1 and names_json['name']['role'] == \
                'principal_investigator':
            pr_inv = names_json['name']['full_name']
        elif names_json['count'] == 1 and names_json['name']['role'] != \
                'principal_investigator':
            other_nms = names_json['name']['full_name']
        else:
            non_pis = []
            for name in names_json['name']:
                if name['role'] == 'principal_investigator':
                    pr_inv = name['full_name']
                else:
                    non_pis.append(name['full_name'])
            other_nms = ', '.join(non_pis)
    return pr_inv, other_nms


def fetch_grant_agency(item):
    """Retrieve the name(s) of the grant agencies, if any.

    :param item: dict.
    :return: str.
    """
    agencies = []
    if isinstance(item['grant_agency_names'], list):
        for funder in item['grant_agency_names']:
            if funder['pref'] == 'Y' and funder['content'] not in agencies:
                agencies.append(funder['content'])
        return ', '.join(agencies)
    return item['grant_agency_names']['content']


def fetch_grant_country(item):
    """Return country of the funding agency

    :param item: dict.
    :return: str.
    """
    if 'grant_agencies' in item.keys():
        funders_json = item['grant_agencies']['grant_agency']
        if isinstance(funders_json, list):
            return ', '.join(list(set(f['country'] for f in funders_json)))
        return funders_json['country']
    return ''


def fetch_pi_institution(item):
    """Retrieve the name(s) of the principal investigator's
    institution, if any. Due to the complexity of the JSON nesting,
    this function will call itself to get the necessary fields.

    :param item: dict.
    :return: str.
    """
    if isinstance(item, dict):
        if 'pref' in item.keys():
            if item['pref'] == 'Y':
                return item['content']
        for key in item.keys():
            return fetch_pi_institution(item[key])
    if isinstance(item, list):
        names_list = []
        for element in item:
            names_list.append(fetch_pi_institution(element))
        return ', '.join(n for n in set(names_list) if n)
    return ''


def fetch_fin_year(item):
    """Retrieve the financial year value, if present in the grant
    record.

    :param item: dict.
    :return: int or str.
    """
    if 'financial_year' in item.keys():
        return item['financial_year']
    return ''


def fetch_related_records(item):
    """Retrieve the associated Web of Science records list, if present
    in the grant record.

    :param item: dict.
    :return: str, int.
    """
    if 'related_records' in item.keys():
        if isinstance(item['related_records']['record'], list):
            records_list = [r['uid'] for r in item['related_records']['record']]
            return ', '.join(records_list), len(records_list)
        return item['related_records']['record']['uid'], 1
    return '', 0


def fetch_document_title(item):
    """Retrieve the grant title.

    :param item: dict.
    :return: str.
    """
    if isinstance(item['title'], list):
        for title in item['title']:
            if title['type'] == 'item':
                return title['content']
    return item['title']['content']


def fetch_keywords(item):
    """Retrieve grant keywords.

    :param item: dict.
    :return: str.
    """
    keywords_list = []
    if 'keywords' in item:
        if isinstance(item['keywords']['keyword'], list):
            for keyword in item['keywords']['keyword']:
                if 'content' in keyword.keys():
                    keywords_list.append(str(keyword['content']))
            return ', '.join(keywords_list)
        if 'content' in item['keywords']['keyword'].keys():
            return item['keywords']['keyword']['content']
    return ''


def fetch_abstract(item):
    """Retrieve grant description.

    :param item: dict.
    :return: str.
    """
    if isinstance(item['abstracts'], list):
        return [', '.join(a['abstract_text']['p']) for a in
                item['abstracts']['abstract']]
    if 'abstract' in item['abstracts'].keys():
        return item['abstracts']['abstract']['abstract_text']['p']
    return ''


def convert_to_usd(amount, currency, rates):
    """Converts grant amount into USD.

    :param amount: int or float.
    :param currency: str.
    :param rates: dict.
    :return: str or float.
    """
    if amount != '':
        if currency == 'USD':
            return amount
        if currency in rates.keys():
            return amount / rates[f'{currency}']
    return ''


def fetch_data(rec, rates):
    """Parse the JSON file retrieved by the API for required metadata
    fields.

    :param rec: dict.
    :param rates: dict.
    :return: dict.
    """
    ut = rec['UID']
    print(ut)
    principal_investigator, other_names = fetch_names(rec['static_data']['summary']['names'])
    doctitle = fetch_document_title(rec['static_data']['summary']['titles'])
    related_wos_records, related_wos_records_count = fetch_related_records(rec['static_data']
                                                                           ['fullrecord_metadata'])
    grant = rec['static_data']['fullrecord_metadata']['fund_ack']['grants']['grant']
    grant_source = grant['grant_source']
    grant_data_item = grant['grant_data']['grantDataItem']
    grant_pi_institution = fetch_pi_institution(grant_data_item['principalInvestigators'])
    grant_amount = grant_data_item['totalAwardAmount']
    grant_currency = grant_data_item['currency']
    grant_amount_in_usd = convert_to_usd(grant_amount, grant_currency, rates)

    return {
        'UT': ut,
        'Publication Year': rec['static_data']['summary']['pub_info']['pubyear'],
        'Financial Year': fetch_fin_year(rec['static_data']['item']),
        'Principal Investigator': principal_investigator,
        'Other Names': other_names,
        'Document Type': rec['static_data']['summary']['doctypes']['doctype'],
        'Document Title': str(doctitle),
        'Keywords': fetch_keywords(rec['static_data']['fullrecord_metadata']),
        'Grant Description': fetch_abstract(rec['static_data']['fullrecord_metadata']),
        'Related WoS Records': related_wos_records,
        'Related WoS Records Count': related_wos_records_count,
        'Funding Agency': fetch_grant_agency(grant),
        'Funding Country': fetch_grant_country(rec['static_data']['item']),
        'Grant Source': grant_source,
        'Principal Investigator Institution': grant_pi_institution,
        'Grant Amount': grant_amount,
        'Currency': grant_currency,
        'Grant Amount, USD': grant_amount_in_usd
    }
