"""
This code calculates an H-index for any set of Web of Science documents, both including and
excluding self-citations.

To use the program, enter the advanced search query - i.e., an author (AU=) or author identifier
(AI=) search - into the SEARCH_QUERY constant value, and run the code.

The program prints the general results but also generates a .csv file containing every document
and its citation counts - both including and excluding self-citations, making it possible to
figure out which specific documents fall out of the H-index calculation if self-citations are
excluded.
"""

import requests
from apikey import APIKEY   # Your API key, it's better not to store it in the program

SEARCH_QUERY = 'AI=A-5224-2009'  # Enter the WoS search query here

HEADERS = {'X-APIKey': APIKEY}


def analyze_core_papers(doc):
    """Get the JSON data from the API response, extracts the main metadata fields, and saves them
     to the papers list

    :param doc: dict.
    :return: dict.
    """
    times_cited = 0
    for database in doc['dynamic_data']['citation_related']['tc_list']['silo_tc']:
        if database['coll_id'] == 'WOS':
            times_cited = database['local_count']
            break
    return {'UT': doc['UID'], 'times_cited': times_cited, 'tc_minus_sc': times_cited}


# A list to store all required WoS document metadata
papers = []

# Initial request to the API is made to figure out the total amount of requests required
initial_response = requests.get(
    f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={SEARCH_QUERY}&'
    f'count=0&firstRecord=1',
    headers=HEADERS,
    timeout=16
)
data = initial_response.json()
total_records = data['QueryResult']['RecordsFound']

# Calculate the number of requests required.
requests_required = ((total_records - 1) // 100) + 1
if requests_required > 1:
    print(f'API requests required to get all the author papers data: {requests_required}')

# Send requests to Web of Science Expanded API to get all the core papers
for i in range(requests_required):
    subsequent_response = requests.get(
        f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={SEARCH_QUERY}&'
        f'count=100&firstRecord={i}01',
        headers=HEADERS,
        timeout=16
    )
    data = subsequent_response.json()
    for wos_record in data['Data']['Records']['records']['REC']:
        papers.append(analyze_core_papers(wos_record))

# Calculate the standard H-index (which includes the self-citations).
papers.sort(reverse=True, key=lambda x: x['times_cited'])
h_index_including_sc = len(papers)
for paper in papers:
    if papers.index(paper) + 1 > paper['times_cited']:
        h_index_including_sc = papers.index(paper)
        break
print(f'\nThe H-index including self-citations is: {h_index_including_sc}. '
      f'Now finding self-citations and excluding them.\n')

# Check if any of the documents are referencing any other documents from the initial search query.
for paper in papers:
    print(f'Checking self-references in paper {papers.index(paper) + 1} of {len(papers)}')
    initial_response = requests.get(
        f"https://api.clarivate.com/api/wos/references?databaseId=WOS&uniqueId={paper['UT']}&"
        f"count=0&firstRecord=1",
        headers=HEADERS,
        timeout=16)
    initial_cited_data = initial_response.json()
    total_records = initial_cited_data['QueryResult']['RecordsFound']
    requests_required = ((total_records - 1) // 100) + 1
    for i in range(requests_required):
        subsequent_cited_response = requests.get(
            f"https://api.clarivate.com/api/wos/references?databaseId=WOS&uniqueId={paper['UT']}&"
            f"count=100&firstRecord={i}01",
            headers=HEADERS,
            timeout=16)
        data = subsequent_cited_response.json()
        for cited_reference in data['Data']:
            for cited_paper in papers:
                if cited_reference['UID'] == cited_paper['UT']:
                    cited_paper['tc_minus_sc'] -= 1


# Calculate the H-index without self-citations
papers.sort(reverse=True, key=lambda x: x['tc_minus_sc'])
h_index_excluding_sc = len(papers)
for paper in papers:
    if papers.index(paper) + 1 > paper['tc_minus_sc']:
        h_index_excluding_sc = papers.index(paper)
        break

print(f"\nThe H-index is:\n"
      f"    Including self-citations: {h_index_including_sc}\n"
      f"    Excluding self-citations: {h_index_excluding_sc}\n"
      f"Please check details in 'H-index.csv' file")

# Save the data into a .csv file
csv_header = (f",Including Self-Citations,Excluding Self-Citations,\n"
              f"H-Index,{h_index_including_sc},{h_index_excluding_sc},\n\n")
with open('h-index.csv', 'w', encoding='utf-8') as writing:
    writing.write(csv_header)
    writing.write("UT,Times Cited (including self-citations),"
                  "Times Cited (excluding self-citations)\n")
    for paper in papers:
        writing.writelines(f"{paper['UT']},{paper['times_cited']},{paper['tc_minus_sc']}\n")
