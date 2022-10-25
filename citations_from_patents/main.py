"""
This code allows creating a patent citation report for any Web of Science Core Collection search query.

To use the program, enter the search query into the SEARCH_QUERY constant using Web of Science advanced search syntax,
and run the code.

The program prints out the total citations from patents to all documents in the search results, and also generates a
.csv file containing a list of Web of Science documents from your search query, the number of times each of them has
been cited by patents, and the list of citing patent IDs which can be fed into the Derwent Innovations Index search
for further analysis.
"""

import requests
import time
import urllib.parse
from apikey import WOSEXPANDED_KEY

SEARCH_QUERY = 'AU=Schnell, JD'  # Enter your search query here

BASEURL = 'https://api.clarivate.com/api/wos'
HEADERS = {'X-APIKey': WOSEXPANDED_KEY}

# Converting the search query into a set of Web of Science Document IDs (or UTs)
# First, a standard API request to check the number of documents in this search query and get a query number
initial_request = requests.get(f'{BASEURL}?databaseId=WOS&usrQuery={urllib.parse.quote(SEARCH_QUERY)}'
                               f'&count=0&firstRecord=1', headers=HEADERS)
data = initial_request.json()
query_id = data['QueryResult']['QueryID']
total_records = data['QueryResult']['RecordsFound']
requests_required = ((total_records - 1) // 100) + 1
cited_uts = []

# Second, a request to /recordids endpoint to gett all the document IDs for this search query
for i in range(requests_required):
    ids_request = requests.get(f'{BASEURL}/recordids/{query_id}?count=100&firstRecord={i}01', headers=HEADERS)
    data = ids_request.json()
    for ut in data:
        cited_uts.append([ut, []])
    print(f"Request for cited items #{i+1} of {requests_required} processed")

total_tc_from_patents = 0


# A function to retrieve the CITING documents for each of the CITED documents for which we obtained a list of IDs in
# the previous block of code, and analyze them for which Web of Science platform database they belong to
def check_citing_records(request_number, total_tc_from_patents):
    citing_request = requests.get(f'{BASEURL}/citing?databaseId=WOK&uniqueId={cited_uts[request_number][0]}&count=0&'
                                  f'firstRecord=1', headers=HEADERS)
    citing_data = citing_request.json()
    try:
        citing_query_id = citing_data['QueryResult']['QueryID']
        total_citing_records = citing_data['QueryResult']['RecordsFound']
        citing_requests_required = ((total_citing_records - 1) // 100) + 1
        for j in range(citing_requests_required):
            citing_ids_request = requests.get(f'{BASEURL}/recordids/{citing_query_id}?count=100&firstRecord={j}01',
                                              headers=HEADERS)
            citing_ids_data = citing_ids_request.json()
            for citing_ut in citing_ids_data:
                if citing_ut.split(':')[0] == 'DIIDW':
                    total_tc_from_patents += 1
                    cited_uts[i][1].append(citing_ut)
    # We are exploring why a KeyError might occur in very rare cases, and we will update the code accordingly once we
    # localize the potential issue
    except KeyError:
        pass
    # A small block of code to prevent the whole program to terminate in case a single API requests doesn't connect
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
        print(f'Resending request #{i+1}')
        time.sleep(2)
        check_citing_records(request_number, total_tc_from_patents)
    print(f"{i+1} of {len(cited_uts)} cited documents processed")
    return total_tc_from_patents


# The function above is launched for each of the citing documents - please be aware, the program might take long to
# process large search queries
for i in range(len(cited_uts)):
    total_tc_from_patents = check_citing_records(i, total_tc_from_patents)

# Next thing is sorting the records by times cited from patents.
cited_uts.sort(reverse=True, key=lambda cited_uts: len(cited_uts[1]))

# Saving the data to a .csv file
with open('citations from patents.csv', 'w') as writing:
    writing.write(f'Search query:,{SEARCH_QUERY}\n'
                  f'\nCited UT,Number of Citing Patents,List of Citing Patents\n')
    for cited_ut in cited_uts:
        writing.writelines(
            f"{cited_ut[0]},{len(cited_ut[1])},{' '.join(cited_ut[1])}\n"
        )

# And finally, printing out the number of documents found and total citations from patents
print(f'{len(cited_uts)} Documents found')
print(f'Citations from patents: {total_tc_from_patents}')