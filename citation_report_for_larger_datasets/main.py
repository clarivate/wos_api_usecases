"""
This is a very simple script to reproduce the key metrics available in the Citation Report function of the
Web of Science platform user interface. These metrics are:
- Number of Publications
- Times Cited
- Average Citations Per Item
- H-Index

This script also allows to calculate these metrics for datasets of up to 50,000 Web of Science records

HOW TO USE IT:

Edit the SEARCH_QUERY field in the code below to any search query that you'd like to analyze for citations
Create another python file in the project folder named 'apikey.py' containing a constant STARTER_APIKEY equal
to the value of your Web of Science Starter API key. If you don't have it, you can request one free of charge at:
https://developer.clarivate.com/apis/wos-starter (Web of Science subscription is required)

Finally, launch the script. The script will retrieve the documents metadata using Web of Science Starter API,
process the data, and print the answers in the Run window / terminal / console.
"""

import requests
from apikey import STARTER_APIKEY

# Search query for which to calculate the citation report
SEARCH_QUERY = 'OG=The World Bank'


def retrieve_key_fields(document):
    """This function retrieves key metadata fields from the Web of Science document records retrieved through the
    API. For reproducing the citation report, we only need the Times Cited, but for logging/debugging purposes
    we can also retrieve the document unique ID (or UT) and the document title.

    :param document: dict containing all document metadata fields available in Web of Science Starter API and
    imported from the JSON object
    :return: None, appends selected fields to records list
    """
    try:
        records.append({'UT': document['uid'],
                        'Title': document['title'],
                        'Times Cited': document['citations'][0]['count']})
    except IndexError:
        records.append({'UT': document['uid'],
                        'Title': document['title'],
                        'Times Cited': 0})


documents = []
records = []

# Initial API request to get the first 50 records and check how many API requests in total will be required to
# retrieve all the data
initial_request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents?q={SEARCH_QUERY}'
                               f'&limit=50&page=1&db=WOS',
                               headers={'X-ApiKey': STARTER_APIKEY})
initial_json = initial_request.json()
documents_found = initial_json['metadata']['total']
print(f'Total Web of Science documents found: {documents_found}')
requests_required = ((documents_found - 1) // 50) + 1
print(f'Web of Science Starter API requests required to retrieve them: {requests_required}')
for wos_document in initial_json['hits']:
    retrieve_key_fields(wos_document)

# If the number of required API requests is more than 1, subsequent API requests are being sent
if requests_required > 1:
    for i in range(1, requests_required):
        subsequent_request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents?q={SEARCH_QUERY}'
                                          f'&limit=50&page={i+1}&db=WOS',
                                          headers={'X-ApiKey': STARTER_APIKEY})
        subsequent_json = subsequent_request.json()
        for wos_document in subsequent_json['hits']:
            retrieve_key_fields(wos_document)
        print(f'{i+1} of {requests_required} processed')

# The total citations amount is going to be stored here
total_citations = 0

# Calculating H-index
records.sort(reverse=True, key=lambda r: r['Times Cited'])
h_index = len(records)
for record in records:
    if records.index(record) + 1 > record['Times Cited']:
        h_index = records.index(record)
        break

# Calculating total citations
for record in records:
    total_citations += record['Times Cited']

# Calculating average citations per item
average_citations_per_item = total_citations / documents_found

# Printing results
print(f"Total Documents: {documents_found}")
print(f"Sum of the Times Cited: {total_citations}")
print(f"H-Index: {h_index}")
print(f"Average Citations Per Item: {average_citations_per_item}")

# Saving results into a .csv file
with open('documents.csv', 'w') as writer:
    writer.writelines(f"Document UT,Times Cited\n")
    for line in records:
        writer.writelines(f"{line['UT']},{line['Times Cited']}\n")
