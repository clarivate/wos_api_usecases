import requests
import os

apikey = os.environ('WOSEXPANDEDAPIKEY')  # Your API key, it's better to keep it in your environment variables
our_org = 'HSE University (National Research University Higher School of Economics)'  # Enter your organization profile here
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
            fractional_counting_paper, our_authors = singe_address_record_check(paper, authors, our_authors, total_au_input)
        else:  # Standard case
            fractional_counting_paper, our_authors = standard_case_paper_check(paper, authors, our_authors, total_au_input)
        csv_string = f"{paper['UID']},{our_authors},{fractional_counting_paper}\n"  # Preparing the output for a .csv
        csv_output += csv_string
    return csv_output


# When there is only one affiliation in the paper
def singe_address_record_check(paper, authors, our_authors, total_au_input):
    authors = single_address_persons_check(paper, authors)
    fractional_counting_paper, our_authors = single_address_org_check(paper, authors, our_authors, total_au_input)
    return fractional_counting_paper, our_authors


def single_address_persons_check(paper, authors):
    for person in paper['static_data']['summary']['names']['name']:  # A person may have a status different from an "author", i.e., "editor". For the purpose of this code, we are only using the "author" type
        try:
            if person['role'] == "author":
                authors += 1
        except TypeError:  # When there is only one name on the paper, it's going to be the author
            authors = 1
    return authors


def single_address_org_check(paper, authors, our_authors, fractional_counting_paper):
    try:
        if our_org == (paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization'][1]['content']):  # Checking if the org profile in the paper is your org profile
            fractional_counting_paper = 1  # And if it is - doesn't matter how many authors, the whole paper is counted
            our_authors = authors
        else:
            fractional_counting_paper = 0
    except KeyError:  # The chances that this paper won't be linked to your org-enhanced are tiny
        pass  # you can add the following code insted of "pass" for checking: print(f"Record {paper['UID']}: address not linked to an Affiliation: {paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization'][0]['content']}")
    except IndexError:  # In case the record contains your organization affiliation in the corresponding address
        print((f"Record {paper['UID']}: the org profile is only in corresponding address: {paper['static_data']['fullrecord_metadata']['reprint_addresses']['address_name']['address_spec']['organizations']['organization'][0]['content']}"))
    return fractional_counting_paper, our_authors


def standard_case_paper_check(paper, authors, our_authors, total_au_input):
    total_au_input, authors, our_authors = standard_case_person_check(paper, authors, our_authors, total_au_input)
    fractional_counting_paper = total_au_input / authors  # Calculating fractional counting for every paper
    return fractional_counting_paper, our_authors


def standard_case_person_check(paper, authors, our_authors, total_au_input):
    try:
        for person in paper['static_data']['summary']['names']['name']:  # Again, checking if the person is actually an author
            if person['role'] == "author":
                authors += 1
                au_input = 0
                au_affils = str(person['addr_no']).split(' ')  # Counting the number of author's affiliations
                for c1 in au_affils:  # For every affiliation, a check is made whether it's your affiliation
                    try:
                        affil = (paper['static_data']['fullrecord_metadata']['addresses']['address_name'][int(c1) - 1]['address_spec']['organizations']['organization'][1]['content'])
                        if affil == our_org:
                            au_input += 1 / len(au_affils)
                    except IndexError:  # In case the address is not linked to an org profile
                        pass  # you can add the following code insted of "pass" for checking: print(f"Record {paper['UID']}: address not linked to an Affiliation: {paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization'][0]['content']}")
                total_au_input += au_input  # Calculating the total input of all of our authors
                if au_input != 0:
                    our_authors += 1
    except TypeError:  # When there is only one name on the paper, it's going to be the author, but his record is going to be imported from json as a list not as a dictionary
        authors = 1
        au_input = 0
        try:
            au_affils = str(paper['static_data']['summary']['names']['name']['addr_no']).split(' ')  # Counting the number of author's affiliations
            au_input = standard_case_single_author_org_check(paper, au_affils, au_input)
        except TypeError:  # In case the address is not linked to an org profile
            pass  # you can add the following code insted of "pass" for checking: print(f"Record {paper['UID']}: address not linked to an Affiliation: {paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization'][0]['content']}")
        total_au_input += au_input  # Calculating the total input of each of our authors
        if au_input != 0:
            our_authors += 1
    except KeyError:  # Exception for the cases then the author might not have a link to an org affiliation in a Web of Science record
        pass  # ou can add the following code insted of "pass" for checking: print(f"Record {paper['UID']}: author {person['full_name']} is not linked to any affiliations")
    return total_au_input, authors, our_authors


def standard_case_single_author_org_check(paper, au_affils, au_input):
    for c1 in au_affils:  # For every affiliation, a check is made whether it's your affiliation
        try:
            affil = (paper['static_data']['fullrecord_metadata']['addresses']['address_name'][int(c1) - 1]['address_spec']['organizations']['organization'][1]['content'])
            if affil == our_org:
                au_input += 1 / len(au_affils)
        except IndexError:  # In case the address is not linked to an org profile
            pass  # you can add the following code insted of "pass" for checking: print(f"Record {paper['UID']}: address not linked to an Affiliation: {paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization'][0]['content']}")
        except KeyError:  # In case the address doesn't contain organization component at all, i.e. "129 Bralyev Kashirinykh Str, Chelyabinsk 454001, Russia"
            pass  # you can add the following code insted of "pass" for checking: print(f"Record {paper['UID']}: address not linked to an Affiliation: {paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization'][0]['content']}")
    return au_input


initial_response = requests.get(f'{endpoint}?databaseId=WOS&usrQuery=OG=({our_org}) and PY={pub_years}&count=100&firstRecord=1', headers = headers)  # This is the initial API request

data = initial_response.json()  # First 100 records received
output = fracount()
with open('papers.csv', 'w') as writing:
    writing.write(csv_header + output)

for i in range(((data['QueryResult']['RecordsFound']) - 1) // 100):  # from the first response, extractng the total number of records found and calculating the number of requests required.
    subsequent_response = requests.get(f'{endpoint}?databaseId=WOS&usrQuery=OG=({our_org}) and PY={pub_years}&count=100&firstRecord={((100*(i+1)+1))}', headers = headers)
    data = subsequent_response.json()
    output = fracount()
    with open('papers.csv', 'a') as writing:
        writing.write(output)
    print(f"{((i+2)*100) // ((data['QueryResult']['RecordsFound']) // 100)}% complete")  # the process can take up to 10 minutes depending on the number of the papers being analyzed