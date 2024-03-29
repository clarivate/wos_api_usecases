"""
This code allows calculating an H-index for any set of Web of Science documents, both including and excluding
self-citations.

To use the program, enter the advanced search query - i.e., an author (AU=) or author identifier (AI=) search - into
the SEARCH_QUERY constant value, and run the code.

The program prints the general results but also generates a .csv file containing every document and its citation counts
- both including and excluding self-citations, making it possible to figure out which specific documents
fall out of the H-index calculation if self-citations are excluded.
"""

import requests
from apikey import APIKEY   # Your API key, it's better not to store it in the program

SEARCH_QUERY = 'AI=AAD-5677-2022'  # Enter the WoS search query here

HEADERS = {'X-APIKey': APIKEY}
BASEURL = "https://api.clarivate.com/api/wos"

papers = []  # All the relevant article data required for calculations inside this code will be stored in this list


# This function gets the JSON data from the API response, extracts the 3 main metadata fields: UT (string), times cited
# (integer), and saves them to the papers list
def analyze_core_papers(data):
    for wos_record in data['Data']['Records']['records']['REC']:
        ut = wos_record['UID']
        times_cited = wos_record['dynamic_data']['citation_related']['tc_list']['silo_tc']['local_count']
        papers.append({'UT': ut, 'times_cited': times_cited, 'tc_minus_sc': times_cited})


# First step. Sending Get-requests to Web of Science Expanded API to get all the core papers (the documents for which
# we want to calculate the H-index) based on the search query stored in the search_query variable above.
# Initial request to the API is made to figure out the total amount of requests required
initial_response = requests.get(
    f'{BASEURL}?databaseId=WOS&usrQuery={SEARCH_QUERY}&count=0&firstRecord=1', headers=HEADERS)
data = initial_response.json()
total_records = data['QueryResult']['RecordsFound']
# From the first response, extracting the total number of records found and calculating the number of requests required.
# The program can take up to a few dozen minutes, depending on the number of records being analyzed
requests_required = ((total_records - 1) // 100) + 1
if requests_required > 1:
    print(f'API requests required to get all the author papers data: {requests_required}')
for i in range(requests_required):
    subsequent_response = requests.get(
        f'{BASEURL}?databaseId=WOS&usrQuery={SEARCH_QUERY}&count=100&firstRecord={i}01', headers=HEADERS)
    data = subsequent_response.json()
    analyze_core_papers(data)  # Every batch of data received via API is sent to analyze_core_papers function


# Next thing is the calculation of standard H-index (which includes the self-citations).
papers.sort(reverse=True, key=lambda papers: papers['times_cited'])
h_index_including_sc = len(papers)
for paper in papers:
    if papers.index(paper) + 1 > paper['times_cited']:
        h_index_including_sc = papers.index(paper)
        break
print(f'\nThe H-index including self-citations is: {h_index_including_sc}. '
      f'Now finding self-citations and excluding them.\n')


# This block of code checks if any of the documents are referencing any other documents from the initial search query.
# As we apply the same criteria to the cited and citing records (appearance of the same ResearcherID in both),
# self-citation and self-referencing for this particular case can be treated as identical events.
for paper in papers:
    self_citation_references = 0
    print(f'Checking self-references in paper {papers.index(paper) + 1} of {len(papers)}')
    initial_response = requests.get(
        f"{BASEURL}/references?databaseId=WOS&uniqueId={paper['UT']}&count=0&firstRecord=1", headers=HEADERS)
    initial_data = initial_response.json()
    total_records = initial_data['QueryResult']['RecordsFound']
    requests_required = ((total_records - 1) // 100) + 1
    for i in range(requests_required):
        subsequent_response = requests.get(
            f"{BASEURL}/references?databaseId=WOS&uniqueId={paper['UT']}&count=100&firstRecord={(i)}01",
            headers=HEADERS)
        data = subsequent_response.json()
        for cited_reference in data['Data']:
            for cited_paper in papers:
                if cited_reference['UID'] == cited_paper['UT']:
                    cited_paper['tc_minus_sc'] -= 1


# Finally, we've got enough data to calculate the H-index without self-citations
papers.sort(reverse=True, key=lambda papers: papers['tc_minus_sc'])
h_index_excluding_sc = len(papers)
for paper in papers:
    if papers.index(paper) + 1 > paper['tc_minus_sc']:
        h_index_excluding_sc = papers.index(paper)
        break

print(f"\nThe H-index is:\n"
      f"    Including self-citations: {h_index_including_sc}\n"
      f"    Excluding self-citations: {h_index_excluding_sc}\n"
      f"Please check details in 'H-index.csv' file")

# The data is then written into the .csv file
csv_header = (f",Including Self-Citations,Excluding Self-Citations,\n"
              f"H-Index,{h_index_including_sc},{h_index_excluding_sc},\n\n")
with open('h-index.csv', 'w') as writing:
    writing.write(csv_header)
    writing.write("UT,Times Cited (including self-citations), Times Cited (excluding self-citations)\n")
    for paper in papers:
        writing.writelines(f"{paper['UT']},{paper['times_cited']},{paper['tc_minus_sc']}\n")
