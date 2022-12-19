"""
This code is accepting the Affiliation name and publication years and returns a table of the Web of Science Core
Collection documents affiliated with this organization for the specified period counted both using Whole Counting and
Fractional Counting approach. This data, along with a number of organization's authors per each document is saved
into an Excel table, and the comparison of the organization's output by years using Whole and Fractional counting
methods is also visualized using Plotly.
"""
import requests
import urllib.parse
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date
from apikey import APIKEY  # Your API key, it's better not to store it in the program;

OUR_ORG = "Clarivate"  # Enter your organization profile name here
PUB_YEARS = '2008-2022'  # Enter publication years

HEADERS = {'X-APIKey': APIKEY}
BASEURL = "https://api.clarivate.com/api/wos"

frac_counts = []


# When there is only one affiliation in the paper
def singe_address_record_check(paper, authors, our_authors):
    authors = single_address_person_check(paper, authors)
    fractional_counting_paper, our_authors = single_address_org_check(paper, authors, our_authors)
    return fractional_counting_paper, our_authors


# A person may have a status different from an "author", i.e.: "editor". For the purpose of this code,
# we are only using the "author" type
def single_address_person_check(paper, authors):
    if paper['static_data']['summary']['names']['count'] == 1:  # A case when there's only one name on the paper
        if paper['static_data']['summary']['names']['name']['role'] == "author":
            authors = 1
    else:
        for person in paper['static_data']['summary']['names']['name']:
            if person['role'] == "author":
                authors += 1
    return authors


# Checking if the org profile in the paper is our org profile
def single_address_org_check(paper, authors, our_authors):
    fractional_counting_paper = 0
    try:
        for org in (
                paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec'][
                    'organizations']['organization']
        ):
            if org['content'] == OUR_ORG:
                fractional_counting_paper = 1  # If it is - doesn't matter how many authors, the whole paper is counted
                our_authors = authors  # Just for reference, we'll store the number of authors from our org in the csv
            else:
                pass
    except (IndexError, KeyError):  # The chances that this paper won't be linked to your org-enhanced profile are tiny
        pass
        """ You can add the following code instead of "pass" for checking:
        print(f"Record {paper['UID']}: address not linked to an Affiliation:
        {affiliation['address_spec']['organizations']['organization'][0]['content']}")"""
    return fractional_counting_paper, our_authors


# When there are multiple affiliations in the paper (that's where we really need this whole algorithm)
def standard_case_paper_check(paper, authors, total_au_input):
    if paper['static_data']['summary']['names']['count'] == 1:  # Again, checking if the person is actually an author
        if paper['static_data']['summary']['names']['name']['role'] == "author":
            authors = 1
    else:
        for person in paper['static_data']['summary']['names']['name']:
            if person['role'] == "author":
                authors += 1
    if authors == 0:  # A very rare case when there are no authors in the paper (i.e., only the "group author")
        fractional_counting_paper = 0
        our_authors = 0
    else:
        total_au_input, authors, our_authors = standard_case_address_check(paper, authors, total_au_input)
        fractional_counting_paper = total_au_input / authors  # Calculating fractional counting for every paper
    return fractional_counting_paper, our_authors


#  Identifying which authors in the paper are affiliated with our organization
def standard_case_address_check(paper, authors, total_au_input):
    our_authors_seq_numbers = set()  # Building a set of sequence numbers of authors from our org
    try:  # Checking every address in the paper
        for affiliation in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
            for org in affiliation['address_spec']['organizations']['organization']:
                if org['pref'] == 'Y' and org['content'] == OUR_ORG:  # Checking every org the address is linked to
                    if affiliation['names']['count'] == 1:  # Filling in the set with our authors' sequence numbers
                        if affiliation['names']['name']['role'] == 'author':
                            our_authors_seq_numbers.add(affiliation['names']['name']['seq_no'])
                    else:
                        for our_author in affiliation['names']['name']:
                            if our_author['role'] == 'author':
                                our_authors_seq_numbers.add(our_author['seq_no'])
    except (IndexError, KeyError,
            TypeError):  # In case the address doesn't contain organization component at all, i.e. street address only
        pass
        """ You can add the following code instead of "pass" for checking:
        print(f"Record {paper['UID']}:
        organization field {affiliation['address_spec']['organizations']['organization'][1]['content']}
        is not linked to any author fields")"""
    our_authors = len(our_authors_seq_numbers)  # The number of our authors in the paper is the length of our set
    if paper['static_data']['summary']['names']['count'] == 1:  # The case when the total number of authors is one
        au_input = 0
        try:
            au_affils = str(paper['static_data']['summary']['names']['name']['addr_no']).split(' ')
            authors = 1
            au_input = standard_case_affiliation_check(paper, au_affils, au_input)
            total_au_input = au_input
        except KeyError:
            pass  # Very rare cases when there is no link between author and affiliation record
    else:  # The case when the total number of authors is more than one - just calling their affiliations differently
        for author in our_authors_seq_numbers:
            au_input = 0
            au_affils = str(paper['static_data']['summary']['names']['name'][int(author) - 1]['addr_no']).split(' ')
            au_input = standard_case_affiliation_check(paper, au_affils, au_input)
            total_au_input += au_input  # The total input of our authors is the sum of individual author inputs
    return total_au_input, authors, our_authors


# For every affiliation, a check is made whether it's our organization's affiliation
def standard_case_affiliation_check(paper, au_affils, au_input):
    for c1 in au_affils:
        try:
            affiliation = (paper['static_data']['fullrecord_metadata']['addresses']['address_name'][int(c1) - 1])
            for org in affiliation['address_spec']['organizations']['organization']:
                if org['pref'] == 'Y' and org['content'] == OUR_ORG:
                    au_input += 1 / len(au_affils)
        except (KeyError, IndexError, TypeError):  # In case the address is not linked to an org profile
            pass
            """You can add the following code instead of "pass" for checking:
            print(f"Record {paper['UID']}: address not linked to an Affiliation:
            {paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']
            ['organization'][0]['content']}")
            """
    return au_input


# Initial request to the API is made to figure out the total amount of requests required
initial_request = requests.get(
    f'{BASEURL}?databaseId=WOS&usrQuery=OG=({urllib.parse.quote(OUR_ORG)}) and PY={PUB_YEARS}&count=0&firstRecord=1',
    headers=HEADERS)  # This is the initial API request
data = initial_request.json()  # First 100 records received
requests_required = ((data['QueryResult']['RecordsFound'] - 1) // 100) + 1
records = []

# From the first response, extracting the total number of records found and calculating the number of requests required.
# The program can take up to a few dozen minutes, depending on the number of records being analyzed
for i in range(requests_required):
    request = requests.get(
        f'{BASEURL}?databaseId=WOS&usrQuery=OG=({urllib.parse.quote(OUR_ORG)}) and PY={PUB_YEARS}&count=100'
        f'&firstRecord={i}01', headers=HEADERS)
    data = request.json()
    for wos_record in data['Data']['Records']['records']['REC']:
        records.append(wos_record)
    print(f"{((i + 1) * 100) // requests_required:.1f}% complete")

for record in records:
    total_au_input = 0  # Total input of the authors from your org into this paper, it's going to be the numerator
    authors = 0  # Total number of authors in the paper, it's going to be the denominator
    our_authors = 0  # The number of authors from your org, it will be saved into the .csv file for every record
    pub_year = record['static_data']['summary']['pub_info']['pubyear']
    if record['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
        fractional_counting_paper, our_authors = singe_address_record_check(record, authors, our_authors)
    else:  # Standard case
        fractional_counting_paper, our_authors = standard_case_paper_check(record, authors, total_au_input)
    frac_counts.append({'UT': record['UID'], 'Publication_year': pub_year,
                        'Our_authors': our_authors, 'Fractional_value': fractional_counting_paper})

# Saving the collected data to a dataframe
df = pd.DataFrame(frac_counts)

# Gathering document counts by years
df2 = (df[['UT', 'Publication_year']].groupby('Publication_year').count())
df2.rename(columns={'UT': 'Whole Counting'}, inplace=True)
df2['Fractional Counting'] = (df[['Fractional_value', 'Publication_year']].groupby('Publication_year').sum())
df2.reset_index(inplace=True)

# The results are saved to an Excel file
with pd.ExcelWriter(f'fractional counting - {OUR_ORG} - {PUB_YEARS} - {date.today()}.xlsx') as writer:
    df2.to_excel(writer, sheet_name='Annual Dynamics', index=False)
    df.to_excel(writer, sheet_name='Document-level Data', index=False)

# Plotting the data on a bar plot
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=df2['Publication_year'], y=df2['Whole Counting'], offset=0.0005, name='Whole Counting',
                     marker=dict(color='#5E33BF')),
              secondary_y=False)
fig.add_trace(go.Bar(x=df2['Publication_year'], y=df2['Fractional Counting'], name='Fractional Counting',
                     marker=dict(color='#16AB03')),
              secondary_y=False)

fig.update_traces(marker=dict(line=dict(width=3, color='white')))

# Adding the fractional/whole ratio as a line above the bar plot
fig.add_trace(go.Scatter(x=df2['Publication_year'], y=(df2['Fractional Counting']/df2['Whole Counting']),
                         line=dict(color="black"),
                         name='Average Fractional Value (Research Involvement)'),
              secondary_y=True)

# Making cosmetic edits to the plot
fig.update_layout({'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
                  barmode='group',
                  bargroupgap=.5,
                  font_family='Calibri',
                  font_color='#646363',
                  font_size=18,
                  title_font_family='Calibri',
                  title_font_color='#646363',
                  title=f'Whole and Fractional Research Output Comparison for {OUR_ORG}, '
                        f'publication years: {PUB_YEARS}',
                  legend_title_text=None,
                  legend=dict(
                      yanchor="bottom",
                      y=-0.4,
                      xanchor="center",
                      x=0.5
                  ))
fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C', secondary_y=False)
fig.update_yaxes(range=[0, 1], showgrid=False, tickformat=',.0%', secondary_y=True)
fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

fig.show()
