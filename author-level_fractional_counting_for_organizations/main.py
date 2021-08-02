import requests
import os

apikey = os.environ['WOSEXPANDEDAPIKEY']  # Your API key, it's better not to store it in the program
our_org = 'ITMO University'  # Enter your organization profile here
pub_years = "2016-2020"  # Enter publication years

headers = {
    'X-APIKey': apikey
}

endpoint = "https://api.clarivate.com/api/wos"
csv_header = "UT,Author_count,Fractional_count\n"  # Final output will be placed in a .csv file


def fracount():  # Fractional counting function for every 100 WoS records received via WoS Expanded API
    csv_output = ""
    for paper in (data['Data']['Records']['records']['REC']):  # Checking every paper in the output
        total_au_input = 0  # Total input of the authors from your org into this paper, it's going to be the numerator
        authors = 0  # Total number of authors in the paper, it's going to be the denominator
        our_authors = 0  # The number of authors from your org, it will be saved into the .csv file for every record
        if paper['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
            fractional_counting_paper, our_authors = singe_address_record_check(paper, authors, our_authors)
        else:  # Standard case
            fractional_counting_paper, our_authors = standard_case_paper_check(paper, authors, total_au_input)
        csv_string = f"{paper['UID']},{our_authors},{fractional_counting_paper}\n"  # Preparing the output for a .csv
        csv_output += csv_string
    return csv_output


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
        if our_org == (paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization'][1]['content']):
            fractional_counting_paper = 1  # And if it is - doesn't matter how many authors, the whole paper is counted
            our_authors = authors  # But just for reference, we will store the number of authors from our org in the csv
        else:
            pass
    except (IndexError, KeyError):  # The chances that this paper won't be linked to your org-enhanced profile are tiny
        pass
        """ You can add the following code insted of "pass" for checking:
        print(f"Record {paper['UID']}: address not linked to an Affiliation:
        {affiliation['address_spec']['organizations']['organization'][0]['content']}")"""
    return fractional_counting_paper, our_authors


# When there are multiple affiliations in the paper, that's where we really need this code
def standard_case_paper_check(paper, authors, total_au_input):
    if paper['static_data']['summary']['names']['count'] == 1:    # Again, checking if the person is actually an author
        if paper['static_data']['summary']['names']['name']['role'] == "author":
            authors = 1
    else:
        for person in paper['static_data']['summary']['names']['name']:
            if person['role'] == "author":
                authors += 1
    total_au_input, authors, our_authors = standard_case_address_check(paper, authors, total_au_input)
    fractional_counting_paper = total_au_input / authors  # Calculating fractional counting for every paper
    return fractional_counting_paper, our_authors


#  Identifying which authors in the paper are affiliated with our organization
def standard_case_address_check(paper, authors, total_au_input):
    our_authors_seq_numbers = set()  # Building a set of sequence numbers of authors from our org
    for affiliation in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
        try:  # Checking every address in the paper
            for org in affiliation['address_spec']['organizations']['organization']:
                try:  # Checking evey organization profile to which the address is linked
                    if org['content'] == our_org:
                        try:  # Filling in the set with our authors' sequence numbers
                            if affiliation['names']['count'] == 1:
                                our_authors_seq_numbers.add(affiliation['names']['name']['seq_no'])
                            else:
                                for our_author in affiliation['names']['name']:
                                    our_authors_seq_numbers.add(our_author['seq_no'])
                        except (IndexError, KeyError):  # When a specific author record is not linked to an affiliation
                            pass
                            """ You can add the following code insted of "pass" for checking:
                            print(f"Record {paper['UID']}:
                            organization field {affiliation['address_spec']['organizations']['organization'][1]['content}
                            is not linked to any author fields")"""
                except TypeError:  # When the org doesn't have a "content" or "pref" attribute
                    pass
        except KeyError:  # In case the address doesn't contain organization component at all, i.e. street address only
            pass
            """ You can add the following code insted of "pass" for checking:
            print(f"Record {paper['UID']}:
            organization field {affiliation['address_spec']['organizations']['organization'][1]['content}
            is not linked to any author fields")"""
    our_authors = len(our_authors_seq_numbers)  # The number of our authors in the paper is the length of our set
    if paper['static_data']['summary']['names']['count'] == 1:  # The case when the total number of authors is one
        au_input = 0
        au_affils = str(paper['static_data']['summary']['names']['name']['addr_no']).split(' ')
        authors = 1
        au_input = standard_case_affiliation_check(paper, au_affils, au_input)
        total_au_input = au_input
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
            affil = (paper['static_data']['fullrecord_metadata']['addresses']['address_name'][int(c1) - 1]['address_spec']['organizations']['organization'][1]['content'])
            if affil == our_org:  # And if it is, the individual author's input increases
                au_input += 1 / len(au_affils)
        except (IndexError, KeyError):  # In case the address is not linked to an org profile
            pass
            """You can add the following code instead of "pass" for checking:
            print(f"Record {paper['UID']}: address not linked to an Affiliation:
            {paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization'][0]['content']}")
            """
    return au_input


# Initial request to the API is made to figure out the total amount of requests required
initial_response = requests.get(f'{endpoint}?databaseId=WOS&usrQuery=OG=({our_org}) and PY={pub_years}&count=100&firstRecord=1', headers=headers)  # This is the initial API request
data = initial_response.json()  # First 100 records received
output = fracount()
with open('papers.csv', 'w') as writing:
    writing.write(csv_header + output)

# From the first response, extractng the total number of records found and calculating the number of requests required.
# The program can take up to a few dozen minutes, depending on the number of records being analyzed
for i in range(((data['QueryResult']['RecordsFound']) - 1) // 100):
    subsequent_response = requests.get(f'{endpoint}?databaseId=WOS&usrQuery=OG=({our_org}) and PY={pub_years}&count=100&firstRecord={(100*(i+1)+1)}', headers=headers)
    data = subsequent_response.json()
    output = fracount()
    with open('papers.csv', 'a') as writing:
        writing.write(output)
    print(f"{((i+1)*100) // ((data['QueryResult']['RecordsFound']) // 100)}% complete")
