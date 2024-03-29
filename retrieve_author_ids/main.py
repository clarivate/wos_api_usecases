"""
This code allows checking any Web of Science organizational profile (or Affiliation) for author profiles that are
associated with it - including Web of Science Distinct Author Sets, ResearcherIDs, and ORCIDs.

To use the program, enter the organization profile name into the OUR_ORG constant value, and any additional
Web of Science Core Collection Advanced Search parameters, like publication year, source title, subject area, etc. -
and run the code.

The program generates a .csv file containing every document and every author affiliated with this organization
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
initial_json = initial_response.json()
requests_required = (((initial_json['QueryResult']['RecordsFound'] - 1) // 100) + 1)
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
    # When there are 0 org affiliations in a particular WoS record - this can sometimes happen, and then there's no
    # author data that is linked to our organizational profile
    if wos_record['static_data']['fullrecord_metadata']['addresses']['count'] == 0:
        pass
    # When there is only 1 org affiliation in the WoS record
    elif wos_record['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
        # 1 org affiliation - a case of only 1 author in this affiliation
        try:
            if wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']['count'] == 1:
                # Retrieving author first name
                try:
                    author_firstname = wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']\
                        ['names']['name']['first_name']
                except KeyError:
                    try:
                        author_firstname = wos_record['static_data']['fullrecord_metadata']['addresses']\
                                ['address_name']['names']['name']['suffix']
                    except KeyError:
                        author_firstname = '_blank_'
                # Retrieving author last name
                author_lastname = wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']\
                    ['names']['name']['last_name']
                # Retrieving author ResearcherID
                try:
                    for rid_record in wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']\
                            ['names']['name']['data-item-ids']['data-item-id']:
                        if rid_record['id-type'] == 'PreferredRID':
                            author_rid = rid_record['content']
                            break
                    else:
                        author_rid = '_blank_'
                except (KeyError, TypeError):
                    try:
                        author_rid = wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']\
                            ['names']['name']['data-item-ids']['data-item-id']['content']
                    except KeyError:
                        author_rid = '_blank_'
                # Retrieving author ORCID. It can be stored in the summary author record or in the "contributors"
                # section.
                if wos_record['static_data']['summary']['names']['count'] == 1:
                    try:
                        author_orcid = wos_record['static_data']['summary']['names']['name']['orcid_id']
                    except KeyError:
                        try:
                            if wos_record['static_data']['contributors']['count'] == 1:
                                if wos_record['static_data']['contributors']['contributor']['name']['last_name'] == \
                                        wos_record['static_data']['summary']['names']['name']['last_name']:
                                    author_orcid = wos_record['static_data']['contributors']['contributor']['name']\
                                        ['orcid_id']
                                else:
                                    author_orcid = '_blank_'
                            elif wos_record['static_data']['contributors']['count'] > 1:
                                for contributor in wos_record['static_data']['contributors']['contributor']:
                                    if contributor['name']['last_name'] == wos_record['static_data']['summary']\
                                            ['names']['name']['last_name']:
                                        author_orcid = contributor['name']['orcid_id']
                                        break
                                else:
                                    author_orcid = '_blank_'
                            else:
                                author_orcid = '_blank_'
                        except KeyError:
                            author_orcid = '_blank_'
                # And the case when there are multiple authors in the document, and we have to iterate over them
                else:
                    for summary_author in wos_record['static_data']['summary']['names']['name']:
                        if summary_author['seq_no'] == wos_record['static_data']['fullrecord_metadata']\
                                ['addresses']['address_name']['names']['name']['seq_no']:
                            try:
                                author_orcid = summary_author['orcid_id']
                                break
                            except KeyError:
                                if wos_record['static_data']['contributors']['count'] == 1:
                                    if wos_record['static_data']['contributors']['contributor']['name']['last_name'] \
                                            == summary_author['last_name']:
                                        author_orcid = wos_record['static_data']['contributors']['contributor']['name']\
                                            ['orcid_id']
                                elif wos_record['static_data']['contributors']['count'] > 1:
                                    for contributor in wos_record['static_data']['contributors']['contributor']:
                                        if contributor['name']['last_name'] == summary_author['last_name']:
                                            author_orcid = contributor['name']['orcid_id']
                                            break
                                else:
                                    author_orcid = '_blank_'
                    else:
                        author_orcid = '_blank_'
                # Retrieving author DAIS ID
                author_dais = wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']\
                    ['name']['daisng_id']
                # Checking is this record is claimed by the author
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
            # 1 org affiliation - a case where there are multiple author records in it
            else:
                for author in wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']\
                        ['name']:
                    # Retrieving author first name
                    try:
                        author_firstname = author['first_name']
                    except (KeyError, TypeError):
                        try:
                            author_firstname = author['suffix']
                        except (KeyError, TypeError):
                            author_firstname = '_blank_'
                    # Retrieving author last name
                    author_lastname = author['last_name']
                    # When there are multiple author records in one affiliation, there will only be a case of multiple
                    # authors in the whole document
                    try:
                        for rid_record in author['data-item-ids']['data-item-id']:
                            if rid_record['id-type'] == 'PreferredRID':
                                author_rid = rid_record['content']
                                break
                        else:
                            author_rid = '_blank_'
                    except (KeyError, TypeError):
                        try:
                            author_rid = author['data-item-ids']['data-item-id']['content']
                        except KeyError:
                            author_rid = '_blank_'
                    # Retrieving author ORCID
                    try:
                        for summary_author in wos_record['static_data']['summary']['names']['name']:
                            if summary_author['seq_no'] == author['seq_no']:
                                author_orcid = summary_author['orcid_id']
                                break
                        else:
                            author_orcid = '_blank_'
                    except KeyError:
                        try:
                            if wos_record['static_data']['contributors']['count'] == 1:
                                if wos_record['static_data']['contributors']['contributor']['name']['last_name'] == \
                                        author['last_name']:
                                    author_orcid = wos_record['static_data']['contributors']['contributor']['name']\
                                        ['orcid_id']
                                else:
                                    author_orcid = '_blank_'
                            elif wos_record['static_data']['contributors']['count'] > 1:
                                for contributor in wos_record['static_data']['contributors']['contributor']:
                                    if contributor['name']['last_name'] == author['last_name']:
                                        author_orcid = contributor['name']['orcid_id']
                                        break
                                else:
                                    author_orcid = '_blank_'
                            else:
                                author_orcid = '_blank_'
                        except KeyError:
                            author_orcid = '_blank_'
                    # Retrieving author DAIS ID
                    author_dais = author['daisng_id']
                    # Checking if the record has been claimed by the author
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
        # When there are multiple affiliations in the WoS record
        for address in wos_record['static_data']['fullrecord_metadata']['addresses']['address_name']:
            try:
                for org in address['address_spec']['organizations']['organization']:
                    if org['pref'] == "Y" and org['content'] == OUR_ORG:
                        # Multiple affiliations - a case of only one author record in our affiliation (but there might
                        # be other author records associated with other affiliations in the record, which we don't need
                        # for the purpose of this code)
                        if address['names']['count'] == 1:
                            # retrieving author first name
                            try:
                                author_firstname = address['names']['name']['first_name']
                            except KeyError:
                                try:
                                    author_firstname = address['names']['name']['suffix']
                                except KeyError:
                                    author_firstname = '_blank_'
                            # retrieving author last name
                            author_lastname = address['names']['name']['last_name']
                            # retrieving author ResearcherID
                            try:
                                for rid_record in address['names']['name']['data-item-ids']['data-item-id']:
                                    if rid_record['id-type'] == 'PreferredRID':
                                        author_rid = rid_record['content']
                                else:
                                    author_rid = '_blank_'
                            except (KeyError, TypeError):
                                try:
                                    author_rid = address['names']['name']['data-item-ids']['data-item-id']['content']
                                except KeyError:
                                    author_rid = '_blank_'
                            # Retrieving author ORCID. Again, this gives us two options: when there is only one author
                            # in the whole document...
                            if wos_record['static_data']['summary']['names']['count'] == 1:
                                try:
                                    author_orcid = wos_record['static_data']['summary']['names']['name']['orcid_id']
                                except KeyError:
                                    try:
                                        if wos_record['static_data']['contributors']['count'] == 1:
                                            if wos_record['static_data']['contributors']['contributor']['name']\
                                                ['last_name'] == wos_record['static_data']['summary']['names']['name']\
                                                    ['last_name']:
                                                author_orcid = wos_record['static_data']['contributors']['contributor']\
                                                    ['name']['orcid_id']
                                            else:
                                                author_orcid = '_blank_'
                                        elif wos_record['static_data']['contributors']['count'] > 1:
                                            for contributor in wos_record['static_data']['contributors']['contributor']:
                                                if contributor['name']['last_name'] == wos_record['static_data']\
                                                        ['summary']['names']['name']['last_name']:
                                                    author_orcid = contributor['name']['orcid_id']
                                            else:
                                                author_orcid = '_blank_'
                                        else:
                                            author_orcid = '_blank_'
                                    except KeyError:
                                        author_orcid = '_blank_'
                            # ...And the case when there are multiple authors
                            else:
                                for summary_author in wos_record['static_data']['summary']['names']['name']:
                                    if summary_author['seq_no'] == address['names']['name']['seq_no']:
                                        try:
                                            author_orcid = summary_author['orcid_id']
                                            break
                                        except KeyError:
                                            try:
                                                if wos_record['static_data']['contributors']['count'] == 1:
                                                    if wos_record['static_data']['contributors']['contributor']['name']\
                                                            ['last_name'] == summary_author['last_name']:
                                                        author_orcid = wos_record['static_data']['contributors']\
                                                            ['contributor']['name']['orcid_id']
                                                        break
                                                elif wos_record['static_data']['contributors']['count'] > 1:
                                                    for contributor in wos_record['static_data']['contributors']\
                                                            ['contributor']:
                                                        if contributor['name']['last_name'] == \
                                                                summary_author['last_name']:
                                                            author_orcid = contributor['name']['orcid_id']
                                                            break
                                                    else:
                                                        author_orcid = '_blank_'
                                                    break
                                                else:
                                                    author_orcid = '_blank_'
                                            except KeyError:
                                                author_orcid = '_blank_'
                                else:
                                    author_orcid = '_blank_'
                            # retrieving author DAIS ID
                            author_dais = address['names']['name']['daisng_id']
                            # checking if the author record has been claimed
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
                        # And finally, the case when there are multiple authors in our affiliation (again, there might
                        # be other affiliations in the record, which we don't need for the purpose of this code)
                        else:
                            for author in address['names']['name']:
                                # retrieving author first name
                                try:
                                    author_firstname = author['first_name']
                                except KeyError:
                                    try:
                                        author_firstname = author['suffix']
                                    except KeyError:
                                        author_firstname = '_blank_'
                                # retrieving author last name
                                author_lastname = author['last_name']
                                # retrieving author ResearcherID
                                try:
                                    for rid_record in author['data-item-ids']['data-item-id']:
                                        if rid_record['id-type'] == 'PreferredRID':
                                            author_rid = rid_record['content']
                                    else:
                                        author_rid = '_blank_'
                                except (KeyError, TypeError):
                                    try:
                                        author_rid = author['data-item-ids']['data-item-id']['content']
                                    except KeyError:
                                        author_rid = '_blank_'
                                # retrieving author ORCID
                                for summary_author in wos_record['static_data']['summary']['names']['name']:
                                    if summary_author['seq_no'] == author['seq_no']:
                                        try:
                                            author_orcid = summary_author['orcid_id']
                                            break
                                        except KeyError:
                                            try:
                                                if wos_record['static_data']['contributors']['count'] == 1:
                                                    if wos_record['static_data']['contributors']['contributor']['name']\
                                                            ['last_name'] == \
                                                            summary_author['last_name']:
                                                        author_orcid = wos_record['static_data']['contributors']\
                                                            ['contributor']['name'][
                                                                'orcid_id']
                                                        break
                                                elif wos_record['static_data']['contributors']['count'] > 1:
                                                    for contributor in wos_record['static_data']['contributors']\
                                                            ['contributor']:
                                                        if contributor['name']['last_name'] == \
                                                                summary_author['last_name']:
                                                            author_orcid = contributor['name']['orcid_id']
                                                            break
                                                        else:
                                                            author_orcid = '_blank_'
                                                    else:
                                                        author_orcid = '_blank_'
                                                    break
                                            except KeyError:
                                                author_orcid = '_blank_'
                                else:
                                    author_orcid = '_blank_'
                                # retrieving author DAIS ID
                                author_dais = author['daisng_id']
                                # checking if the author profile has been claimed
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

# saving the data into a .csv file
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
