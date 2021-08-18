import requests
import os

apikey = os.environ['WOSEXPANDEDAPIKEY']  # Your API key, it's better not to store it in the program
UT = "WOS:000258733400004"  # Enter the WoS unique record identifier to evaluate its self-citation percentage


headers = {
    'X-APIKey': apikey
}

endpoint = "https://api.clarivate.com/api/wos"


def cited_paper():
    data = cited_request()
    cited_author_names, cited_author_dais, cited_author_rids, cited_author_orcids = get_author_list(data)
    cited_org_names = get_org_list(data)
    cited_source_names = get_source_list(data)
    times_cited = get_times_cited(data)
    return cited_author_names, cited_author_dais, cited_author_rids, cited_author_orcids, cited_org_names, cited_source_names, times_cited


def citing_papers():
    data = citing_request()
    citing_author_names, citing_author_dais, citing_author_rids, citing_author_orcids = get_author_list(data)
    citing_org_names = get_org_list(data)
    citing_source_names = get_source_list(data)
    return citing_author_names, citing_author_dais, citing_author_rids, citing_author_orcids, citing_org_names, citing_source_names


def get_author_list(data):
    author_names = []
    author_dais = []
    author_rids = []
    author_orcids = []
    i = 0
    for paper in data['Data']['Records']['records']['REC']:
        author_names.append(set())
        author_dais.append(set())
        author_rids.append(set())
        author_orcids.append(set())
        if paper['static_data']['summary']['names']['count'] == 1:
            author_names[i].add(paper['static_data']['summary']['names']['name']['wos_standard'])
        else:
            for person_name in paper['static_data']['summary']['names']['name']:
                try:
                    author_names[i].add(person_name['wos_standard'])
                except KeyError:
                    pass  # No author name data in this contributor record - i.e., it can be a group author
                try:
                    author_dais[i].add(person_name['daisng_id'])
                except KeyError:
                    pass  # No DAIS data in this author record
                try:
                    for rid in person_name['data-item-ids']['data-item-id']:
                        if rid['id-type'] == 'PreferredRID':
                            author_rids[i].add(rid['content'])
                except KeyError:
                    pass  # No RID data in this author record
                except TypeError:
                    pass  # A rare case when the RID is linked to the author, but the record isn't claimed
                try:
                    author_orcids[i].add(person_name['orcid_id'])
                except KeyError:
                    pass  # No ORCID data in this author record
        i += 1
    return author_names, author_dais, author_rids, author_orcids


def get_org_list(data):
    org_names = []
    i = 0
    for paper in (data['Data']['Records']['records']['REC']):
        org_names.append(set())
        try:
            if paper['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
                for org in paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization']:
                    if org['pref'] == 'Y':
                        org_names[i].add(org['content'])
            else:
                for affiliation in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
                    for org in affiliation['address_spec']['organizations']['organization']:
                        if org['pref'] == 'Y':
                            org_names[i].add(org['content'])
        except KeyError:
            pass  # When there is no address data on the paper record at all
        i += 1
    return org_names


def get_source_list(data):
    source_list = []
    i = 0
    for paper in (data['Data']['Records']['records']['REC']):
        source_list.append(set())
        for title in paper['static_data']['summary']['titles']['title']:
            if title['type'] == 'source_abbrev':
                source_list[i].add(title['content'])
        i += 1
    return source_list


def get_times_cited(data):
    times_cited = 0
    for paper in (data['Data']['Records']['records']['REC']):
        times_cited = paper['dynamic_data']['citation_related']['tc_list']['silo_tc']['local_count']
    return times_cited


def self_citations():
    cited_author_names, cited_author_dais, cited_author_rids, cited_author_orcids, cited_org_names, cited_source_names, times_cited = cited_paper()
    citing_author_names, citing_author_dais, citing_author_rids, citing_author_orcids, citing_org_names, citing_source_names = citing_papers()
    author_name_self_citation = calculation(cited_author_names, citing_author_names, times_cited)
    print(f'Author name-level self citation: {author_name_self_citation * 100}%')
    author_dais_self_citation = calculation(cited_author_dais, citing_author_dais, times_cited)
    print(f'Author DAIS-level self citation: {author_dais_self_citation * 100}%')
    author_rids_self_citation = calculation(cited_author_rids, citing_author_rids, times_cited)
    print(f'Author RID-level self citation: {author_rids_self_citation * 100}%')
    author_orcids_self_citation = calculation(cited_author_orcids, citing_author_orcids, times_cited)
    print(f'Author ORCID-level self citation: {author_orcids_self_citation * 100}%')
    org_self_citation = calculation(cited_org_names, citing_org_names, times_cited)
    print(f'Organization-level self citation: {org_self_citation * 100}%')
    source_self_citation = calculation(cited_source_names, citing_source_names, times_cited)
    print(f'Publication Source-level self citation: {source_self_citation * 100}%')


def calculation(cited, citing, times_cited):
    self_citations_count = 0
    for cited_record in cited:
        for citing_record in citing:
            if len(cited_record.intersection(citing_record)) > 0:
                self_citations_count += 1
    self_citation = self_citations_count / times_cited
    return self_citation


def org_calculation (cited, citing, times_cited):
    self_citations_count = 0
    for i in range(len(cited)):
        for j in range(len(citing)):
            if cited[i].intersection(citing[j]) == True:
                self_citations_count += 1
    self_citation = self_citations_count / times_cited
    return self_citation


def cited_request():
    api_response = requests.get(f'{endpoint}?databaseId=WOS&usrQuery=UT={UT}&count=100&firstRecord=1', headers=headers)
    data = api_response.json()
    return data


def citing_request():
    initial_response = requests.get(f'{endpoint}/citing?databaseId=WOS&uniqueId={UT}&count=100&firstRecord=1', headers=headers)
    data = initial_response.json()
    for i in range(((data['QueryResult']['RecordsFound'] - 1) // 100)):
        subsequent_response = requests.get(f'{endpoint}/citing?databaseId=WOS&uniqueId={UT}&count=100&firstRecord={(100*(i+1)+1)}', headers=headers)
        addtl_data = subsequent_response.json()
        for paper in range(len(addtl_data['Data']['Records']['records']['REC'])):
            data['Data']['Records']['records']['REC'].append(addtl_data['Data']['Records']['records']['REC'][paper])
    return data


self_citations()
