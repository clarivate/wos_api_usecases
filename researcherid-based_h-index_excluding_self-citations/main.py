import requests
import time
from apikey import apikey   # Your API key, it's better not to store it in the program

search_query = 'AI=B-7347-2013'  # Enter the WoS search query here

headers = {'X-APIKey': apikey}

baseurl = "https://api.clarivate.com/api/wos"
papers = []  # All the relevant article data required for calculations inside this code will be stored in this list


# This function gets the JSON data from the API response, extracts the 3 main metadata fields: UT (string), times cited
# (integer), and ResearcherIDs (set), and saves them to the papers list
def analyze_core_papers(data):
    for wos_record in data['Data']['Records']['records']['REC']:
        ut = wos_record['UID']
        times_cited = wos_record['dynamic_data']['citation_related']['tc_list']['silo_tc']['local_count']
        author_rids = extract_rids_from_record(wos_record)
        papers.append({'UT': ut, 'rids': author_rids, 'times_cited': times_cited, 'citing_papers': []})


# This is a general function that extracts the ResearcherID sets from WoS records, we will reuse it later when making
# the citing papers requests
def extract_rids_from_record(wos_record):
    rids = set()
    if wos_record['static_data']['summary']['names']['count'] == 1:
        try:
            for rid in wos_record['static_data']['summary']['names']['name']['data-item-ids']['data-item-id']:
                if rid['id-type'] == 'PreferredRID':
                    rids.add(rid['content'])
        except (KeyError, TypeError):
            # A rare case when the RID is linked to the author, but the record isn't claimed
            try:
                if wos_record['static_data']['contributors']['count'] == 1:
                    rids.add(wos_record['static_data']['contributors']['contributor']['name']['r_id'])
                else:
                    for contributor in wos_record['static_data']['contributors']['contributor']:
                        rids.add(contributor['name']['r_id'])
            except KeyError:
                pass  # This would mean there's just no ResearcherID data in the paper
    else:
        for person_name in wos_record['static_data']['summary']['names']['name']:
            try:
                for rid in person_name['data-item-ids']['data-item-id']:
                    if rid['id-type'] == 'PreferredRID':
                        rids.add(rid['content'])
            except KeyError:
                pass  # No RID data in this author record
            except TypeError:
                # A rare case when the RID is linked to the author, but the record isn't claimed
                try:
                    if wos_record['static_data']['contributors']['count'] == 1:
                        rids.add(
                            wos_record['static_data']['contributors']['contributor']['name']['r_id'])
                    else:
                        for contributor in wos_record['static_data']['contributors']['contributor']:
                            rids.add(contributor['name']['r_id'])
                except KeyError:
                    pass  # Okay, there's just no ResearcherID data in the paper
    return rids


# First step. Sending Get-requests to Web of Science Expanded API to get all the core papers (the documents for which
# we want to calculate the H-index) based on the search query stored in the search_query variable above.
# Initial request to the API is made to figure out the total amount of requests required
request_start = time.time()
initial_response = requests.get(
    f'{baseurl}?databaseId=WOS&usrQuery={search_query}&count=0&firstRecord=1', headers=headers)
data = initial_response.json()
total_records = data['QueryResult']['RecordsFound']
# From the first response, extracting the total number of records found and calculating the number of requests required.
# The program can take up to a few dozen minutes, depending on the number of records being analyzed
requests_required = ((total_records - 1) // 100) + 1
if requests_required > 1:
    print(f'API requests required to get all the author papers data: {requests_required}')
for i in range(requests_required):
    subsequent_response = requests.get(
        f'{baseurl}?databaseId=WOS&usrQuery={search_query}&count=100&firstRecord={100 * i}01',
        headers=headers
    )
    data = subsequent_response.json()
    analyze_core_papers(data)  # Every batch of data received via API is sent to analyze_core_papers function


# This function is just required for the papers.sort below to work
def tc(papers):
    return papers['times_cited']


# Next thing is calculation of the standard H-index (which includes the self-citations).
papers.sort(reverse=True, key=tc)
h_index_including_sc = 0
for paper in papers:
    if papers.index(paper) + 1 > paper['times_cited']:
        h_index_including_sc = papers.index(paper)
        break
print(f'\nThe H-index including self-citations is: {h_index_including_sc}. '
      f'Now finding self-citations and excluding them.\n')

#  H-index and the list of papers with their numbers of times cited - including self-citations, is saved to a .csv-file
with open('h-index.csv', 'w') as writing:
    writing.write(f"H-index including self-citations:, {h_index_including_sc}\n\n")
    writing.write("UT,Times Cited\n")
with open('h-index.csv', 'a') as writing:
    for paper in papers:
        writing.writelines(f"{paper['UT']},{paper['times_cited']}\n")


# This function  gets the citing paper data via API. The comments to next small block of code explain
# why this is important
def citing_request(paper):
    citing_papers = []
    initial_response = requests.get(f"{baseurl}/citing?databaseId=WOS&uniqueId={paper['UT']}&count=0&firstRecord=1",
                                    headers=headers)
    initial_data = initial_response.json()
    total_records = initial_data['QueryResult']['RecordsFound']
    requests_required = ((total_records - 1) // 100) + 1
    if requests_required > 1:
        print(f'API requests required to get all the citing papers data: {requests_required}')
    for i in range(requests_required):
        subsequent_response = requests.get(
            f"{baseurl}/citing?databaseId=WOS&uniqueId={paper['UT']}&count=100&firstRecord={(100 * i + 1)}",
            headers=headers
        )
        data = subsequent_response.json()
        for wos_record in data['Data']['Records']['records']['REC']:
            citing_rids = extract_rids_from_record(wos_record)
            citing_papers.append({'UT': wos_record['UID'], 'rids': citing_rids})
    return citing_papers


# The second important step of the algorithm is to get the data on the citing articles. The required data fields for the
# citing articles are their UTs (string) and ResearcherIDs (set), and for each cited paper they are stored in the
# dictionary of the core (cited) paper to which they belong
for paper in papers:
    print(f'Checking papers that cite paper {papers.index(paper) + 1} of {len(papers)}')
    paper['citing_papers'] = citing_request(paper)


# This function gets the cited references from the citing papers in which self-citation has been identified. Every
# cited reference that leads from citing paper to cited paper is excluded from the citation counts of the cited (core)
# document. The comments to the next block of code explain why this is important
def cited_reference_request(cited_ut, citing_paper):
    self_citation_references = 0
    initial_response = requests.get(
        f"{baseurl}/references?databaseId=WOS&uniqueId={citing_paper['UT']}&count=0&firstRecord=1",
        headers=headers
    )
    initial_data = initial_response.json()
    total_records = initial_data['QueryResult']['RecordsFound']
    requests_required = ((total_records - 1) // 100) + 1
    if requests_required > 1:
        print(f'API requests required to get all the cited references data: {requests_required}')
    for i in range(requests_required):
        subsequent_response = requests.get(
            f"{baseurl}/references?databaseId=WOS&uniqueId={citing_paper['UT']}&count=100&firstRecord={(100 * i + 1)}",
            headers=headers)
        data = subsequent_response.json()
        for cited_reference in data['Data']:
            if cited_reference['UID'] == cited_ut:
                self_citation_references += 1
    if self_citation_references > 1:
        print(f"The number of coauthor self-citations between these papers is {self_citation_references}\n")
    return self_citation_references


# This block of code applies set.intersection() method to find identical ResearcherIDs in the core and citing Web of
# Science records. If those are found, it counts as a self-citation for the purpose of this algorithm. In this case,
# it is mandatory to check the CITED references of the CITING document to calculate how many citations got affected by
# the self-citation event. Their number for any particular self-citation event might be more than one, that's why we
# need this block of code to make sure the result of the algorithm is correct. For more information on the algorithm
# business logic and associated limitations of use, please refer to the readme.md file.
for paper in papers:
    for citing_paper in paper['citing_papers']:
        if len(citing_paper['rids'].intersection(paper['rids'])) > 0:
            print(f"Oops, a coauthor self-citation has been found: {citing_paper['UT']} is citing {paper['UT']}, "
                  f"both with ResearcherID: {citing_paper['rids'].intersection(paper['rids'])}.")
            paper['times_cited'] -= cited_reference_request(paper['UT'], citing_paper)

# Finally, we've got enough data to calculate the H-index without self-citation
papers.sort(reverse=True, key=tc)
h_index_excluding_sc = 0
for paper in papers:
    if papers.index(paper) + 1 > paper['times_cited']:
        h_index_excluding_sc = papers.index(paper)
        break
print(f"\nThe H-index is:\n"
      f"    Including self-citations: {h_index_including_sc}\n"
      f"    Excluding self-citations: {h_index_excluding_sc}\n"
      f"Please check details in 'H-index.csv' file")

# The same data is then written into the .csv file
with open('h-index.csv', 'a') as writing:
    writing.write(f"\nH-index excluding self-citations:, {h_index_excluding_sc}\n")
    writing.write("UT,Times Cited\n")
    for paper in papers:
        writing.writelines(f"{paper['UT']},{paper['times_cited']}\n")
