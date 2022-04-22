"""
This code allows checking any Web of Science organizational profile (or Affiliation) for author profiles that are
associated with it - including Web of Science Distinct Author Sets, ResearcherIDs, and ORCIDs.

To use the program, enter the organization profile name into the OUR_ORG constant value, and any additional
Web of Science Core Collection Advanced Search parameters, like publication year, source title, subject area, etc. -
and run the code.

The program generates a .csv file containing evey document and every author affiliated with this organization
"""

import urllib.parse
import requests
from apikey import APIKEY  # Create a separate apikey.py file in the project folder to store your API key there

OUR_ORG = 'Clarivate'  # Enter the organization that you would like to analyze for existing author profiles
ADDTL_PARAMS = 'PY=2008-2022'  # Enter additional search parameters, such as publication year

HEADERS = {'X-APIKey': APIKEY}
BASEURL = "https://api.clarivate.com/api/wos"

# Getting all the necessary records via API requests
initial_response = requests.get(f'{BASEURL}?databaseId=WOS&usrQuery=OG={urllib.parse.quote(OUR_ORG)} '
                                f'AND {ADDTL_PARAMS}&count=0&firstRecord=1', headers=HEADERS)
data = initial_response.json()
requests_required = (((data['QueryResult']['RecordsFound'] - 1) // 100) + 1)
data = []
for i in range(requests_required):
    subsequent_response = requests.get(
        f'{BASEURL}?databaseId=WOS&usrQuery=OG={urllib.parse.quote(OUR_ORG)} AND {ADDTL_PARAMS}&count=100&'
        f'firstRecord={i}01', headers=HEADERS)
    for wos_record in subsequent_response.json()['Data']['Records']['records']['REC']:
        data.append(wos_record)
    print(f"{(((i + 1) * 100) / requests_required):.1f}% of API requests complete")

authors_list = []
for wos_record in data:
    ut = wos_record['UID']
    # A rare case of 0 org affiliations in a particular WoS record - this can sometimes happen, and then there's no
    # author data that will be linked to our organizational profile
    if wos_record['static_data']['fullrecord_metadata']['addresses']['count'] == 0:
        pass
    # A case of only 1 org affiliation in the WoS record
    elif wos_record['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
        # A case of only 1 author in this affiliation
        try:
            if wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']['count'] == 1:
                try:
                    author_firstname = wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']\
                        ['names']['name']['first_name']
                except KeyError:
                    try:
                        author_firstname = wos_record['static_data']['fullrecord_metadata']['addresses']\
                                ['address_name']['names']['name']['suffix']
                    except KeyError:
                        author_firstname = '_blank_'
                author_lastname = wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']\
                    ['names']['name']['last_name']
                try:
                    for rid_record in wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']\
                            ['names']['name']['data-item-ids']['data-item-id']:
                        if rid_record['id-type'] == 'PreferredRID':
                            author_rid = rid_record['content']
                            break
                except (KeyError, TypeError):
                    author_rid = '_blank_'
                # ORCID ID is stored in the summary author record. Again, first we try the case when there's only one
                # author in the summary field (meaning, there is only 1 author in the whole document)
                if wos_record['static_data']['summary']['names']['count'] == 1:
                    try:
                        author_orcid = wos_record['static_data']['summary']['names']['name']['orcid_id']
                    except KeyError:
                        author_orcid = '_blank_'
                # And the case when there are multiple authors in the document, and we have to iterate over them
                else:
                    try:
                        for summary_author in wos_record['static_data']['summary']['names']['name']:
                            if summary_author['seq_no'] == wos_record['static_data']['fullrecord_metadata']\
                                    ['addresses']['address_name']['names']['name']['seq_no']:
                                author_orcid = summary_author['orcid_id']
                                break
                    except KeyError:
                        author_orcid = '_blank_'
                author_dais = wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']\
                    ['name']['daisng_id']
                try:
                    claim_status = str(wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']\
                                           ['names']['name']['claim_status']).upper()
                except KeyError:
                    claim_status = 'FALSE'
                authors_list.append({
                    'ut': ut,
                    'author_firstname': author_firstname,
                    'author_lastname': author_lastname,
                    'author_rid': author_rid,
                    'author_orcid': author_orcid,
                    'author_dais': author_dais,
                    'claim_status': claim_status
                })
            # A case where there are multiple author records in a single affiliation
            else:
                for author in wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']\
                        ['name']:
                    try:
                        author_firstname = author['first_name']
                    except (KeyError, TypeError):
                        try:
                            author_firstname = author['suffix']
                        except (KeyError, TypeError):
                            author_firstname = '_blank_'
                    author_lastname = author['last_name']
                    # When there are multiple author records in one affiliation, there will only be a case of multiple
                    # authors in the whole document
                    try:
                        for rid_record in author['data-item-ids']['data-item-id']:
                            if rid_record['id-type'] == 'PreferredRID':
                                author_rid = rid_record['content']
                    except (KeyError, TypeError):
                        author_rid = '_blank_'
                    try:
                        for summary_author in wos_record['static_data']['summary']['names']['name']:
                            if summary_author['seq_no'] == author['seq_no']:
                                author_orcid = summary_author['orcid_id']
                    except KeyError:
                        author_orcid = '_blank_'
                    author_dais = author['daisng_id']
                    try:
                        claim_status = str(author['claim_status']).upper()
                    except KeyError:
                        claim_status = 'FALSE'
                    authors_list.append({
                        'ut': ut,
                        'author_firstname': author_firstname,
                        'author_lastname': author_lastname,
                        'author_rid': author_rid,
                        'author_orcid': author_orcid,
                        'author_dais': author_dais,
                        'claim_status': claim_status
                    })
        except KeyError:
            pass
    else:
        # A case of multiple affiliations in the WoS record
        for address in wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']:
            try:
                for org in address['address_spec']['organizations']['organization']:
                    if org['pref'] == "Y" and org['content'] == OUR_ORG:
                        # A case of only one author record among multiple affiliations
                        if address['names']['count'] == 1:
                            try:
                                author_firstname = address['names']['name']['first_name']
                            except KeyError:
                                try:
                                    author_firstname = address['names']['name']['suffix']
                                except KeyError:
                                    author_firstname = '_blank_'
                            author_lastname = address['names']['name']['last_name']
                            try:
                                for rid_record in address['names']['name']['data-item-ids']['data-item-id']:
                                    if rid_record['id-type'] == 'PreferredRID':
                                        author_rid = rid_record['content']
                            except (KeyError, TypeError):
                                author_rid = '_blank_'
                            # Again, this gives us two options: when there is only one author in the whole document...
                            if wos_record['static_data']['summary']['names']['count'] == 1:
                                try:
                                    author_orcid = wos_record['static_data']['summary']['names']['name']['orcid_id']
                                except KeyError:
                                    author_orcid = '_blank_'
                            # ...And the case when there are multiple authors
                            else:
                                try:
                                    for summary_author in wos_record['static_data']['summary']['names']['name']:
                                        if summary_author['seq_no'] == address['names']['name']['seq_no']:
                                            author_orcid = summary_author['orcid_id']
                                except KeyError:
                                    author_orcid = '_blank_'
                            author_dais = address['names']['name']['daisng_id']
                            try:
                                claim_status = str(address['names']['name']['claim_status']).upper()
                            except KeyError:
                                claim_status = 'FALSE'
                            authors_list.append({
                                'ut': ut,
                                'author_firstname': author_firstname,
                                'author_lastname': author_lastname,
                                'author_rid': author_rid,
                                'author_orcid': author_orcid,
                                'author_dais': author_dais,
                                'claim_status': claim_status
                            })
                        # And finally, the case when there are multiple authors
                        else:
                            for author in address['names']['name']:
                                try:
                                    author_firstname = author['first_name']
                                except KeyError:
                                    try:
                                        author_firstname = author['suffix']
                                    except KeyError:
                                        author_firstname = '_blank_'
                                author_lastname = author['last_name']
                                try:
                                    for rid_record in author['data-item-ids']['data-item-id']:
                                        if rid_record['id-type'] == 'PreferredRID':
                                            author_rid = rid_record['content']
                                except (KeyError, TypeError):
                                    author_rid = '_blank_'
                                try:
                                    for summary_author in wos_record['static_data']['summary']['names']['name']:
                                        if summary_author['seq_no'] == author['seq_no']:
                                            author_orcid = summary_author['orcid_id']
                                except KeyError:
                                    author_orcid = '_blank_'
                                author_dais = author['daisng_id']
                                try:
                                    claim_status = str(author['claim_status']).upper()
                                except KeyError:
                                    claim_status = 'FALSE'
                                authors_list.append({
                                    'ut': ut,
                                    'author_firstname': author_firstname,
                                    'author_lastname': author_lastname,
                                    'author_rid': author_rid,
                                    'author_orcid': author_orcid,
                                    'author_dais': author_dais,
                                    'claim_status': claim_status
                                })
            except KeyError:
                pass

with open('authors.csv', 'w') as writing:
    writing.write(f'Organization:,{OUR_ORG}\n'
                  f'Additional Search Parameters:,{ADDTL_PARAMS}\n'
                  f'\nUT,Firstname,Lastname,ResearcherID,ORCID,Author profile link,Claimed\n')
    for author in authors_list:
        writing.writelines(
        f'{author["ut"]},{author["author_firstname"]},{author["author_lastname"]},{author["author_rid"]} ,'
        f'{author["author_orcid"]} ,https://www.webofscience.com/wos/author/record/{author["author_dais"]},'
        f'{author["claim_status"]}\n'
        )
