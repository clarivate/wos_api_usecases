"""Calculate the percentage and absolute values of self-citation at the following levels:
- Coauthor self-citation (when both cited and citing documents come from the same author), defined by:
    - Coauthor name
    - ResearcherID
    - ORCID
- Organization-level self-citation (when both cited and citing documents are affiliated with the same organization)
- Country-level self-citation (when both cited and citing documents come from the same country)
- Source-level self-citation (when both cited and citing documents come from the same journal, conference, or book)

To use the code, just enter any Web of Science Advanced Search Query in the constant "SEARCH_QUERY" and
launch the code"""

import urllib.parse
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly import offline
from apikey import APIKEY  # Your API key, it's better not to store it in the main python file

# Enter the WoS search query to evaluate its self-citation percentage:
SEARCH_QUERY = 'AI=A-5224-2009'

HEADERS = {'X-APIKey': APIKEY}
BASEURL = "https://api.clarivate.com/api/wos"


def get_times_cited(tc_json):
    """Fetch the times cited counts from the document metadata.

    :param tc_json: dict.
    :return: int or str.
    """
    for database in tc_json:
        if database['coll_id'] == 'WOS':
            return database['local_count']
    return 0


def fetch_rids(name_json):
    """Retrieve Researcher ID data from the name dictionary/JSON object.

    :param name_json: dict.
    :return: str.
    """
    if 'data-item-ids' in name_json:
        if isinstance(name_json['data-item-ids']['data-item-id'], dict):
            if name_json['data-item-ids']['data-item-id']['id-type'] == 'PreferredRID':
                return name_json['data-item-ids']['data-item-id']['content']
        else:
            for data_item_id in name_json['data-item-ids']['data-item-id']:
                if data_item_id['id-type'] == 'PreferredRID':
                    return data_item_id['content']
    return set()


def fetch_author_fields(record):
    """Retrieve required author metadata fields from each WoS document
    record obtained via API.

    :param record: dict from API JSON.
    :return: sets of str.
    """
    au_names = set()  # Author names field, which can be spelled differently for the same person
    au_rids = set()  # This set relies on author ResearcherID
    au_orcids = set()  # This set relies on author ORCID
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


# noinspection PyTypeChecker
def get_organizations(address_json):
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


def get_countries(record):
    """Retrieve country metadata fields from each WoS document record obtained via API.

    :param record: dict from API JSON.
    :return: set of str.
    """
    cu_names = set()
    try:
        if record['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
            cu_names.add(
                record['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['country']
            )
        else:
            for affiliation in record['static_data']['fullrecord_metadata']['addresses']['address_name']:
                cu_names.add(affiliation['address_spec']['country'])
    except KeyError:
        pass  # When there is no address data on the paper record at all
    return cu_names


def get_source(record):
    """Retrieve source title metadata field from each WoS document record obtained via API.

    :param record: dict from API JSON.
    :return: str.
    """
    src_name = ""
    for title in record['static_data']['summary']['titles']['title']:
        if title['type'] == 'source':
            src_name = title['content']
            break
    return src_name


# This will save several API queries/records by storing the already checked citing papers locally
checked_citing_papers = [('ut', 'cited_paper')]


def self_citation_crs_calc(citing_record, citing_records_list):
    """Perform the self-citation calculation for every cited reference
    if the self-citation event has been identified. If that happens,
    then the citing document is analyzed for the number of references
    to that particular cited document. This is required because the
    number of citations and the number of citing documents are not the
    same thing. One citing document can have multiple cited references
    leading to the cited one, so the total amount of citations to a
    paper can sometimes be significantly higher than the number of
    citing records.

    :param citing_record: dict representing the citing document.
    :param citing_records_list: list containing all citing documents.
    :return: None, sets the value of ['self_citation_references'] key of the citing paper.
    """
    for checked_citing_paper in checked_citing_papers:  # Checking if the paper has already been extracted via API
        if checked_citing_paper[0] == citing_record['citing_ut']:
            cr_data = checked_citing_paper[1]
            break
    else:  # If it hasn't - the code will send a request to Web of Science API for cited references of that paper
        initial_cited_response = requests.get(
            f"{BASEURL}/references?databaseId=WOS&uniqueId="
            f"{citing_record['citing_ut']}&count=100&firstRecord=1",
            headers=HEADERS,
            timeout=16
        )
        initial_cited_data = initial_cited_response.json()
        cr_data = initial_cited_data['Data']
        print(f'Oops, seems like a self-citation found: cited paper {citing_record["cited_ut"]}, '
              f'citing paper {citing_record["citing_ut"]}, ({citing_records_list.index(citing_paper) + 1} of '
              f'{len(citing_records_list)} citing articles processed)')
        if initial_data['QueryResult']['RecordsFound'] > 100:
            for j in range(1, ((initial_cited_data['QueryResult']['RecordsFound'] - 1) // 100) + 1):
                subsequent_cited_response = requests.get(
                    f"{BASEURL}/references?databaseId=WOS&uniqueId="
                    f"{citing_record['citing_ut']}&count=100&firstRecord={j}01",
                    headers=HEADERS,
                    timeout=16
                )
                addtl_cited_data = subsequent_cited_response.json()
                for cited_reference in addtl_cited_data['Data']:
                    cr_data.append(cited_reference)
            checked_citing_papers.append((citing_record['citing_ut'], cr_data))
    for cited_reference in cr_data:  # Checking if the ID of a paper in cited reference matches the ID of a cited paper
        if cited_reference['UID'] == citing_record['cited_ut']:
            citing_record['self_citation_references'] += 1  # If it does, the self-citation count is increased by 1


# First we create a list of cited papers based on a search query specified in the start of the code
cited_data = []
initial_response = requests.get(
    f'{BASEURL}?databaseId=WOS&usrQuery={urllib.parse.quote(SEARCH_QUERY)}&'
    f'count=0&firstRecord=1',
    headers=HEADERS,
    timeout=16
)
initial_data = initial_response.json()
requests_required = (((initial_data['QueryResult']['RecordsFound'] - 1) // 10) + 1)
for i in range(requests_required):
    subsequent_response = requests.get(
        f'{BASEURL}?databaseId=WOS&usrQuery={urllib.parse.quote(SEARCH_QUERY)}'
        f'&count=10&firstRecord={i}1',
        headers=HEADERS,
        timeout=16
    )
    print(f"Getting cited papers data: {i+1} of {requests_required}")
    addtl_data = subsequent_response.json()
    for cited_paper in addtl_data['Data']['Records']['records']['REC']:
        cited_data.append(cited_paper)
cited_papers_list = []
citing_papers_list = []

# Fetching the required metadata fields for each paper in the received JSON data.
for paper in cited_data:
    ut = paper['UID']
    print(ut)  # Uncomment for debugging
    author_names, author_rids, author_orcids = fetch_author_fields(paper)
    organizations_names = get_organizations(paper['static_data']['fullrecord_metadata']['addresses'])
    country_names = get_countries(paper)
    source_name = get_source(paper)
    times_cited = get_times_cited(paper['dynamic_data']['citation_related']['tc_list']['silo_tc'])
    cited_papers_list.append({
        'ut': ut, 'author_names': author_names, 'author_rids': author_rids,
        'author_orcids': author_orcids, 'org_names': organizations_names, 'country_names': country_names,
        'source_name': source_name, 'times_cited': times_cited})

# Second, based on the cited paper list we create a list of the documents which cite it
print('Now getting citing papers data for each of them that were cited at least once:')
for paper in cited_papers_list:
    if paper['times_cited'] > 0:
        print(f"    {paper['ut']}, {cited_papers_list.index(paper) + 1} of {len(cited_papers_list)}")
        citing_data = []
        try:
            initial_response = requests.get(
                f"{BASEURL}/citing?databaseId=WOS&uniqueId={paper['ut']}&"
                f"count=100&firstRecord=1",
                headers=HEADERS,
                timeout=16
            )
            initial_data = initial_response.json()
            for citing_paper in initial_data['Data']['Records']['records']['REC']:
                citing_data.append(citing_paper)
            if initial_data['QueryResult']['RecordsFound'] > 100:
                requests_required = (((initial_data['QueryResult']['RecordsFound'] - 1) // 100) + 1)
                for i in range(1, requests_required):
                    subsequent_response = requests.get(
                        f"{BASEURL}/citing?databaseId=WOS&uniqueId={paper['ut']}"
                        f"&count=100&firstRecord={i}01",
                        headers=HEADERS,
                        timeout=16
                    )
                    addtl_data = subsequent_response.json()
                    for citing_paper in addtl_data['Data']['Records']['records']['REC']:
                        citing_data.append(citing_paper)
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
            initial_response = requests.get(
                f"{BASEURL}/citing?databaseId=WOS&uniqueId={paper['ut']}&"
                f"count=10&firstRecord=1",
                headers=HEADERS,
                timeout=16
            )
            initial_data = initial_response.json()
            for citing_paper in initial_data['Data']['Records']['records']['REC']:
                citing_data.append(citing_paper)
            if initial_data['QueryResult']['RecordsFound'] > 10:
                requests_required = (((initial_data['QueryResult']['RecordsFound'] - 1) // 10) + 1)
                for i in range(1, requests_required):
                    subsequent_response = requests.get(
                        f"{BASEURL}/citing?databaseId=WOS&uniqueId="
                        f"{paper['ut']}&count=10&firstRecord={i}1",
                        headers=HEADERS,
                        timeout=16
                    )
                    addtl_data = subsequent_response.json()
                    for citing_paper in addtl_data['Data']['Records']['records']['REC']:
                        citing_data.append(citing_paper)
        for item in citing_data:
            citing_ut = item['UID']
            print(f'Citing paper ID: {citing_ut}')  # Uncomment for debugging
            citing_author_names, citing_author_rids, citing_author_orcids = fetch_author_fields(item)
            citing_org_names = get_organizations(item['static_data']['fullrecord_metadata']['addresses'])
            citing_country_names = get_countries(item)
            citing_source_name = get_source(item)
            citing_papers_list.append({
                'cited_ut': paper['ut'], 'cited_author_names': paper['author_names'],
                'cited_author_rids': paper['author_rids'], 'cited_author_orcids': paper['author_orcids'],
                'cited_org_names': paper['org_names'], 'cited_country_names': paper['country_names'],
                'cited_source_name': paper['source_name'],
                'citing_ut': item['UID'], 'citing_author_names': citing_author_names,
                'citing_author_rids': citing_author_rids, 'citing_author_orcids': citing_author_orcids,
                'citing_org_names': citing_org_names, 'citing_country_names': citing_country_names,
                'citing_source_name': citing_source_name, 'self_citation_references': 0
                                 })

# Finally, we calculate the self-citations at each of the levels
author_name_self_citation = 0
author_dais_self_citation = 0
author_rids_self_citation = 0
author_orcids_self_citation = 0
org_self_citation = 0
country_self_citation = 0
source_self_citation = 0

# Every citing paper is checked for set.intersection(). If at least 1
# match is found, a calculation of references from citing to cited
# document is made.
for citing_paper in citing_papers_list:
    if len(citing_paper['cited_author_names'].intersection(citing_paper['citing_author_names'])) > 0:
        self_citation_crs_calc(citing_paper, citing_papers_list)
        author_name_self_citation += citing_paper['self_citation_references']
    if len(citing_paper['cited_author_rids'].intersection(citing_paper['citing_author_rids'])) > 0:
        if citing_paper['self_citation_references'] == 0:
            self_citation_crs_calc(citing_paper, citing_papers_list)
        author_rids_self_citation += citing_paper['self_citation_references']
    if len(citing_paper['cited_author_orcids'].intersection(citing_paper['citing_author_orcids'])) > 0:
        if citing_paper['self_citation_references'] == 0:
            self_citation_crs_calc(citing_paper, citing_papers_list)
        author_orcids_self_citation += citing_paper['self_citation_references']
    if len(citing_paper['cited_org_names'].intersection(citing_paper['citing_org_names'])) > 0:
        if citing_paper['self_citation_references'] == 0:
            self_citation_crs_calc(citing_paper, citing_papers_list)
        org_self_citation += citing_paper['self_citation_references']
    if len(citing_paper['cited_country_names'].intersection(citing_paper['citing_country_names'])) > 0:
        if citing_paper['self_citation_references'] == 0:
            self_citation_crs_calc(citing_paper, citing_papers_list)
        country_self_citation += citing_paper['self_citation_references']
    if citing_paper['cited_source_name'] == citing_paper['citing_source_name']:
        if citing_paper['self_citation_references'] == 0:
            self_citation_crs_calc(citing_paper, citing_papers_list)
        source_self_citation += citing_paper['self_citation_references']

# Printing the results
print('\nCoauthor self-citation:')
print(f'    Name-level: {(author_name_self_citation/len(citing_papers_list) * 100):.2f}% '
      f'({author_name_self_citation} self-citations, {len(citing_papers_list) - author_name_self_citation} external, '
      f'{len(citing_papers_list)} total)')
print(f'    ResearcherID-level: {(author_rids_self_citation / len(citing_papers_list) * 100):.2f}% '
      f'({author_rids_self_citation} self-citations, {len(citing_papers_list) - author_rids_self_citation} external, '
      f'{len(citing_papers_list)} total)')
print(f'    ORCID-level: {(author_orcids_self_citation / len(citing_papers_list) * 100):.2f}% '
      f'({author_orcids_self_citation} '
      f'self-citations, {len(citing_papers_list) - author_orcids_self_citation} external, '
      f'{len(citing_papers_list)} total)')
print(f'Organization-level self-citation: {(org_self_citation / len(citing_papers_list) * 100):.2f}% '
      f'({org_self_citation} '
      f'self-citations, {len(citing_papers_list) - org_self_citation} external, {len(citing_papers_list)} total)')
print(f'Country-level self-citation: {(country_self_citation / len(citing_papers_list) * 100):.2f}% '
      f'({country_self_citation} '
      f'self-citations, {len(citing_papers_list) - country_self_citation} external, {len(citing_papers_list)} total)')
print(f'Publication Source-level self-citation: {(source_self_citation / len(citing_papers_list) * 100):.2f}% '
      f'({source_self_citation} self-citations, {len(citing_papers_list) - source_self_citation} external, '
      f'{len(citing_papers_list)} total)')

df = pd.DataFrame(citing_papers_list)

non_set_cols = [
    'cited_ut',
    'self_citation_references',
    'cited_source_name',
    'citing_ut',
    'citing_source_name']

for col in df.drop(non_set_cols, axis=1).columns:
    df[col] = df[col].apply(lambda x: '; '.join(x))


df2 = pd.DataFrame({'Coauthor Name': [author_name_self_citation,
                                      len(citing_papers_list) - author_name_self_citation,
                                      len(citing_papers_list),
                                      f'{((author_name_self_citation / len(citing_papers_list)) * 100):.1f}%'],
                    'ResearcherID': [author_rids_self_citation,
                                     len(citing_papers_list) - author_rids_self_citation,
                                     len(citing_papers_list),
                                     f'{((author_rids_self_citation / len(citing_papers_list)) * 100):.1f}%'],
                    'ORCID': [author_orcids_self_citation,
                              len(citing_papers_list) - author_orcids_self_citation,
                              len(citing_papers_list),
                              f'{((author_orcids_self_citation / len(citing_papers_list)) * 100):.1f}%'],
                    'Organization': [org_self_citation,
                                     len(citing_papers_list) - org_self_citation,
                                     len(citing_papers_list),
                                     f'{((org_self_citation / len(citing_papers_list)) * 100):.1f}%'],
                    'Country': [country_self_citation,
                                len(citing_papers_list) - country_self_citation,
                                len(citing_papers_list),
                                f'{((country_self_citation / len(citing_papers_list)) * 100):.1f}%'],
                    'Publication Source': [source_self_citation,
                                           len(citing_papers_list) - source_self_citation,
                                           len(citing_papers_list),
                                           f'{((source_self_citation / len(citing_papers_list)) * 100):.1f}%']},
                   index=['Self-citations', 'External Citations', 'Total Citations', '% Self-Citations'])


# Saving data to Excel
safe_query = SEARCH_QUERY.replace('?', '').replace('*', '').replace('"', '')
df.to_excel(excel_writer=f'self-citations - {safe_query}.xlsx',
            sheet_name='Citation links', index=False)
df2.to_excel(excel_writer=f'self-citations - {safe_query}.xlsx',
             sheet_name='Self-citation rates')


# Visualizing the data
fig = make_subplots(rows=3, cols=2, specs=[[{'type': 'domain'}, {'type': 'domain'}],
                                           [{'type': 'domain'}, {'type': 'domain'}],
                                           [{'type': 'domain'}, {'type': 'domain'}]])

colors = ['#B175E1', '#18A381']

fig.add_trace(go.Pie(labels=df2.index[[0, 1]], values=df2['Coauthor Name'][0:], name='Coauthor Name'), 1, 1)
fig.add_trace(go.Pie(labels=df2.index[[0, 1]], values=df2['ResearcherID'][0:], name='ResearcherID'), 2, 1)
fig.add_trace(go.Pie(labels=df2.index[[0, 1]], values=df2['ORCID'][0:], name='ORCID'), 3, 1)
fig.add_trace(go.Pie(labels=df2.index[[0, 1]], values=df2['Organization'][0:], name='Organization'), 1, 2)
fig.add_trace(go.Pie(labels=df2.index[[0, 1]], values=df2['Country'][0:], name='Country'), 2, 2)
fig.add_trace(go.Pie(labels=df2.index[[0, 1]], values=df2['Publication Source'][0:], name='Publication Source'), 3, 2)

fig.update_traces(hole=.83,
                  direction='clockwise',
                  sort=False,
                  marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)))

fig.update_layout(
    title_text=f"Self-citations analysis for: {SEARCH_QUERY}",
    # Add annotations in the center of the donut pies.
    annotations=[dict(text='Coauthor Name', x=0, y=0.89, font_size=16, showarrow=False),
                 dict(text='Coauthor RID', x=0.02, y=0.5, font_size=16, showarrow=False),
                 dict(text='Coauthor ORCID', x=0, y=0.13, font_size=16, showarrow=False),
                 dict(text='Organization', x=0.62, y=0.89, font_size=16, showarrow=False),
                 dict(text='Country', x=0.64, y=0.5, font_size=16, showarrow=False),
                 dict(text='Publication Source', x=0.6, y=0.13, font_size=16, showarrow=False)])

offline.plot(fig)
