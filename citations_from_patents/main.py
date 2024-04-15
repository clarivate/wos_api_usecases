"""
This code allows creating a patent citation report for any Web of Science Core Collection search
query.

To use the program, enter the search query into the SEARCH_QUERY constant using Web of Science
advanced search syntax, and run the code.

The program prints out the total citations from patents to all documents in the search results,
and also generates a .csv file containing a list of Web of Science documents from your search query,
the number of times each of them has been cited by patents, and the list of citing patent IDs which
can be fed into the Derwent Innovations Index search for further analysis.
"""

import time
import urllib.parse
import requests
from apikey import WOSEXPANDED_KEY

# Enter your search query here
SEARCH_QUERY = 'OG=Clarivate'

HEADERS = {'X-APIKey': WOSEXPANDED_KEY}

# A request to Expanded API to calculate the total number of records and total number
# of requests required to retrieve them
initial_request = requests.get(f'https://api.clarivate.com/api/wos?databaseId=WOS&'
                               f'usrQuery={urllib.parse.quote(SEARCH_QUERY)}'
                               f'&count=0&firstRecord=1',
                               headers=HEADERS,
                               timeout=16)
data = initial_request.json()
query_id = data['QueryResult']['QueryID']
total_records = data['QueryResult']['RecordsFound']
requests_required = ((total_records - 1) // 100) + 1
cited_records = []
total_tc_from_patents = 0

# Actual Expanded API requests to retrieve documents metadata
for i in range(requests_required):
    ids_request = requests.get(f'https://api.clarivate.com/api/wos?databaseId=WOS&'
                               f'usrQuery={urllib.parse.quote(SEARCH_QUERY)}'
                               f'&count=100&firstRecord={i}01',
                               headers=HEADERS,
                               timeout=16)
    data = ids_request.json()
    for document in data['Data']['Records']['records']['REC']:
        ut = document['UID']
        tc = 0
        for database in document['dynamic_data']['citation_related']['tc_list']['silo_tc']:
            if database['coll_id'] == 'DIIDW':
                tc = database['local_count']
                break
        cited_records.append([ut, tc])
        total_tc_from_patents += tc
    print(f"Request for cited items #{i+1} of {requests_required} processed")


def check_citing_records(rec):
    """Retrieve the CITING documents for each of the CITED documents that have at least 1 citation,
    and analyze them for which Web of Science platform database they belong to.

    :param rec: list.
    :return: int, updated figure of total_tc_from_patents
    """
    citing_request = requests.get(f'https://api.clarivate.com/api/wos/citing?databaseId=WOK&'
                                  f'uniqueId={rec[0]}&count=0&firstRecord=1',
                                  headers=HEADERS,
                                  timeout=16)
    citing_data = citing_request.json()
    try:
        citing_query_id = citing_data['QueryResult']['QueryID']
        total_citing_records = citing_data['QueryResult']['RecordsFound']
        citing_requests_required = ((total_citing_records - 1) // 100) + 1
        citing_patents_ids = []
        for j in range(citing_requests_required):
            citing_ids_request = requests.get(f'https://api.clarivate.com/api/wos/recordids/'
                                              f'{citing_query_id}?count=100&'
                                              f'firstRecord={j}01',
                                              headers=HEADERS,
                                              timeout=16)
            citing_ids_data = citing_ids_request.json()
            for citing_ut in citing_ids_data:
                if citing_ut.split(':')[0] == 'DIIDW':
                    citing_patents_ids.append(citing_ut)
        rec.append(' '.join(citing_patents_ids))

    # We are exploring why a KeyError might occur in very rare cases, and we will update the code
    # accordingly once we localize the potential issue
    except KeyError:
        print(f'KeyError in the record {rec}')

    # A small block of code to prevent the whole program to terminate in case a single API
    # requests doesn't connect
    except (requests.exceptions.ConnectionError,
            requests.exceptions.JSONDecodeError,
            ConnectionAbortedError):
        print(f'Resending request #{cited_records.index(rec) + 1}')
        time.sleep(2)
        check_citing_records(rec)
    print(f"{cited_records.index(rec) + 1} of {len(cited_records)} cited documents processed")


# Launching the function above for every document record that was identified to have citations
# from Derwent Innovations Index.
for record in cited_records:
    if record[1] != 0:
        check_citing_records(record)

# Next thing is sorting the records by times cited from patents.
cited_records.sort(reverse=True, key=lambda x: x[1])

safe_search_query = SEARCH_QUERY.replace('*', '').replace('?', '').replace('"', '')

# Saving the data to a .csv file
with open(f'citations from patents - {safe_search_query}.csv', 'w', encoding='utf-8') as writing:
    writing.write(f'Search query:,{SEARCH_QUERY}\n'
                  f'\nCited UT,Number of Citing Patents,List of Citing Patents\n')
    for cited_record in cited_records:
        writing.writelines(f"{cited_record[0]},{cited_record[1]},"
                           f"{cited_record[2] if len(cited_record) == 3 else ''}\n")

# And finally, printing out the number of documents found and total citations from patents
print(f'{len(cited_records)} Documents found')
print(f'Citations from patents: {total_tc_from_patents}')
