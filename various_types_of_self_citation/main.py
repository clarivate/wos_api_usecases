import requests
from paper import Paper
from apikey import apikey   # Your API key, it's better not to store it in the program

# Enter the WoS search query to evaluate its self-citation percentage:
search_query = 'AI=A-3080-2009'

headers = {
    'X-APIKey': apikey
}

baseurl = "https://api.clarivate.com/api/wos"

# This will save several API queries/records by storing the already checked citing papers locally
checked_citing_papers = [('ut', 'cited_paper')]


class CitedPaper(Paper):
    def __init__(self, ut, author_names, author_dais, author_rids, author_orcids, org_names, country_names,
                 source_name, times_cited, citing_papers_list):
        super().__init__(ut, author_names, author_dais, author_rids, author_orcids, org_names, country_names,
                 source_name)
        self.times_cited = times_cited
        self.citing_papers_list = citing_papers_list


class CitingPaper(Paper):
    def __init__(self, ut, author_names, author_dais, author_rids, author_orcids, org_names, country_names,
                 source_name, self_citation_crs):
        super().__init__(ut, author_names, author_dais, author_rids, author_orcids, org_names, country_names,
                 source_name)
        self.self_citation_crs = self_citation_crs


def cited_papers():  # This is how we create a list of cited papers based on a search query specified in the start
    data = cited_request()  # Getting the data from Web of Science API
    cited_papers_list = []
    for paper in data:  # Breaking the received JSON data into separate instances of cited_paper class
        ut = paper['UID']
        author_names, author_dais, author_rids, author_orcids = get_author_list(paper)
        org_names = get_org_list(paper)
        country_names = get_country_list(paper)
        source_name = get_source_name(paper)
        times_cited = get_times_cited(paper)
        citing_papers_list = []
        cited_papers_list.append(CitedPaper(ut, author_names, author_dais, author_rids, author_orcids, org_names,
                                            country_names, source_name, times_cited, citing_papers_list))
    return cited_papers_list


def cited_request():  # This function actually gets the cited paper data via API
    cited_data = []
    initial_response = requests.get(f'{baseurl}?databaseId=WOS&usrQuery={search_query}&count=0&firstRecord=1',
                                    headers=headers)
    initial_data = initial_response.json()
    for i in range(((initial_data['QueryResult']['RecordsFound'] - 1) // 100) + 1):
        subsequent_response = requests.get(
            f'{baseurl}?databaseId=WOS&usrQuery={search_query}&count=100&firstRecord={(100 * i + 1)}',
            headers=headers)
        print(f"Getting cited papers data: {i+1} of {((initial_data['QueryResult']['RecordsFound'] - 1) // 100) + 1}")
        addtl_data = subsequent_response.json()
        for j in range(len(addtl_data['Data']['Records']['records']['REC'])):
            cited_data.append(addtl_data['Data']['Records']['records']['REC'][j])
    return cited_data


def citing_papers(cited_papers_list):  # Based on the list of cited papers, we get a list of the records which cite them
    for paper in cited_papers_list:
        data = citing_request(paper)
        print(f"Now getting citing papers data for each of them: {cited_papers_list.index(paper) + 1} of {len(cited_papers_list)}")
        paper.citing_papers_list = []
        for record in data:
            ut = record['UID']
            author_names, author_dais, author_rids, author_orcids = get_author_list(record)
            org_names = get_org_list(record)
            country_names = get_country_list(record)
            source_name = get_source_name(record)
            self_citation_crs = 0
            paper.citing_papers_list.append(CitingPaper(ut, author_names, author_dais, author_rids, author_orcids,
                                                        org_names, country_names, source_name, self_citation_crs))
            #  Please pay attention to the line above: every object of CitingPaper class is an item of
            #  citing_papers_list, an attribute of specific cited paper. By this, we establish links between cited and
            #  citing records. This allows finding self-citations only in the records that reference each other, not
            #  just arbitrary records in the cited and citing dataset. This would be extremely helpful for coauthor
            #  self-citation evaluation
    return cited_papers_list


def citing_request(paper):  # This function  gets the citing paper data via API
    citing_data = []
    initial_response = requests.get(f'{baseurl}/citing?databaseId=WOS&uniqueId={paper.ut}&count=0&firstRecord=1',
                                    headers=headers)
    initial_data = initial_response.json()
    for i in range(((initial_data['QueryResult']['RecordsFound'] - 1) // 100) + 1):
        subsequent_response = requests.get(f'{baseurl}/citing?databaseId=WOS&uniqueId={paper.ut}&count=100&firstRecord={(100*i+1)}', headers=headers)
        addtl_data = subsequent_response.json()
        for j in range(len(addtl_data['Data']['Records']['records']['REC'])):
            citing_data.append(addtl_data['Data']['Records']['records']['REC'][j])
    return citing_data


def get_author_list(paper):  # This function gets lists of authors (and coauthors) for every paper
    author_names = set()  # This set uses the author name field, which can be spelled differently for the same person
    author_dais = set()  # This uses Web of Science record sets made by Clarivate author name disambiguation algorithm
    author_rids = set()  # This set relies on author ResearcherID
    author_orcids = set()  # This set relies on author ORCID
    if paper['static_data']['summary']['names']['count'] == 1:
        author_names.add(paper['static_data']['summary']['names']['name']['wos_standard'])
        author_dais.add(paper['static_data']['summary']['names']['name']['daisng_id'])
        try:
            for rid in paper['static_data']['summary']['names']['name']['data-item-ids']['data-item-id']:
                if rid['id-type'] == 'PreferredRID':
                    author_rids.add(rid['content'])
        except KeyError:
            pass  # No RID data in this author record
        except TypeError:
            # A rare case when the RID is linked to the author, but the record isn't claimed
            try:
                if paper['static_data']['contributors']['count'] == 1:
                    author_rids.add(paper['static_data']['contributors']['contributor']['name']['r_id'])
                else:
                    for contributor in paper['static_data']['contributors']['contributor']:
                        author_rids.add(contributor['name']['r_id'])
            except KeyError:
                pass # Okay, there's just no ResearcherID data in the paper
        try:
            author_orcids.add(paper['static_data']['summary']['names']['name']['orcid_id'])
        except KeyError:
            pass  # No ORCID data in this author record
    else:
        for person_name in paper['static_data']['summary']['names']['name']:
            try:
                author_names.add(person_name['wos_standard'])
            except KeyError:
                pass  # No author name data in this contributor record - i.e., it can be a group author
            try:
                author_dais.add(person_name['daisng_id'])
            except KeyError:
                pass  # No DAIS data in this author record
            try:
                for rid in person_name['data-item-ids']['data-item-id']:
                    if rid['id-type'] == 'PreferredRID':
                        author_rids.add(rid['content'])
            except KeyError:
                pass  # No RID data in this author record
            except TypeError:
                # A rare case when the RID is linked to the author, but the record isn't claimed
                try:
                    if paper['static_data']['contributors']['count'] == 1:
                        author_rids.add(paper['static_data']['contributors']['contributor']['name']['r_id'])
                    else:
                        for contributor in paper['static_data']['contributors']['contributor']:
                            author_rids.add(contributor['name']['r_id'])
                except KeyError:
                    pass  # Okay, there's just no ResearcherID data in the paper
            try:
                author_orcids.add(person_name['orcid_id'])
            except KeyError:
                pass  # No ORCID data in this author record
    return author_names, author_dais, author_rids, author_orcids


def get_org_list(paper):  # This function gets lists of affiliated organizations for every paper
    org_names = set()  # The set relies on Affiliation a.k.a. Organization-Enhanced field of every record
    try:
        if paper['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
            for org in paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']['organization']:
                if org['pref'] == 'Y':
                    org_names.add(org['content'])
        else:
            for affiliation in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
                for org in affiliation['address_spec']['organizations']['organization']:
                    if org['pref'] == 'Y':
                        org_names.add(org['content'])
    except KeyError:
        pass  # When there is no address data on the paper record at all
    return org_names


def get_country_list(paper):
    country_names = set()
    try:
        if paper['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
            country_names.add(paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['country'])
        else:
            for affiliation in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
                country_names.add(affiliation['address_spec']['country'])
    except KeyError:
        pass  # When there is no address data on the paper record at all
    return country_names


def get_source_name(paper):  # This function gets publication sources for every paper
    source_name = ""  # The string relies on Abbreviated Source Name field of every record
    for title in paper['static_data']['summary']['titles']['title']:
        if title['type'] == 'source_abbrev':
            source_name = title['content']
    return source_name


def get_times_cited(paper):  # This function gets the times cited count for every cited paper
    times_cited = paper['dynamic_data']['citation_related']['tc_list']['silo_tc']['local_count']
    return times_cited


# This is the function that performs the self-citation calculation for every cited reference. If the self-citation event
# has been identified by the above calculation() function, then the citing document is analyzed for the number of
# references to that particular cited document. This is required because the number of citations and the number of
# citing documents are not the same thing. One citing document can have multiple cited references leading to the cited
# one, so the total amount of citations to a paper can sometimes be significantly higher than the number of citing
# records.
def self_citation_crs_calc(cited_paper, citing_paper):
    citing_paper.self_citation_crs = 0  # The self-citation cited references count for every citing paper
    for checked_citing_paper in checked_citing_papers:  # Checking if the paper has already been extracted via API
        if checked_citing_paper[0] == citing_paper.ut:
            cr_data = checked_citing_paper[1]
    else:  # If it hasn't - the code will send a request to Web of Science API for cited references of that paper
        initial_response = requests.get(f'{baseurl}/references?databaseId=WOS&uniqueId={citing_paper.ut}&count=100&firstRecord=1', headers=headers)
        cr_data = initial_response.json()
        for i in range(((cr_data['QueryResult']['RecordsFound'] - 1) // 100)):
            subsequent_response = requests.get(
                f'{baseurl}/references?databaseId=WOS&uniqueId={citing_paper.ut}&count=100&firstRecord={(100 * (i + 1) + 1)}',
                headers=headers)
            addtl_cr_data = subsequent_response.json()
            for paper in range(len(addtl_cr_data['Data'])):
                cr_data['Data'].append(addtl_cr_data['Data'][paper])
        checked_citing_papers.append((citing_paper.ut, cr_data))  # Storing all the checked citing papers locally
    for cr in cr_data['Data']:  # Checking if the ID of a paper in cited reference matches the ID of a cited paper
        if cr['UID'] == cited_paper.ut:
            citing_paper.self_citation_crs += 1  # If it does, this citing paper self-citation count is increased by 1
    return citing_paper, checked_citing_papers


def self_citations(cited_papers_list):  # Self-citation calculations occur here
    total_citations = 0
    author_name_self_citation = 0
    author_dais_self_citation = 0
    author_rids_self_citation = 0
    author_orcids_self_citation = 0
    org_self_citation = 0
    country_self_citation = 0
    source_self_citation = 0
    for cited_paper in cited_papers_list:  # For every cited paper we run a check
        for citing_paper in cited_paper.citing_papers_list:  # Every paper that was citing it is checked for matches
            if len(cited_paper.author_names.intersection(citing_paper.author_names)) > 0:  # For (co)author names
                self_citation_crs_calc(cited_paper, citing_paper)  # If at least 1 match is found, a calculaton of references from citing to cited document is counted
                print(f'Oops, seems like a self-citation found: paper {cited_papers_list.index(cited_paper) + 1} of {len(cited_papers_list)}')
                author_name_self_citation += citing_paper.self_citation_crs
            if len(cited_paper.author_dais.intersection(citing_paper.author_dais)) > 0:  # For (co)author paper sets
                if citing_paper.self_citation_crs == 0:
                    self_citation_crs_calc(cited_paper, citing_paper)
                author_dais_self_citation += citing_paper.self_citation_crs
            if len(cited_paper.author_rids.intersection(citing_paper.author_rids)) > 0:  # For their ResearcherIDs
                if citing_paper.self_citation_crs == 0:
                    self_citation_crs_calc(cited_paper, citing_paper)
                author_rids_self_citation += citing_paper.self_citation_crs
            if len(cited_paper.author_orcids.intersection(citing_paper.author_orcids)) > 0:  # For their ORCIDs
                if citing_paper.self_citation_crs == 0:
                    self_citation_crs_calc(cited_paper, citing_paper)
                author_orcids_self_citation += citing_paper.self_citation_crs
            if len(cited_paper.org_names.intersection(citing_paper.org_names)) > 0:  # For their org affiliations
                if citing_paper.self_citation_crs == 0:
                    self_citation_crs_calc(cited_paper, citing_paper)
                org_self_citation += citing_paper.self_citation_crs
            if len(cited_paper.country_names.intersection(citing_paper.country_names)) > 0:  #For their country names
                if citing_paper.self_citation_crs == 0:
                    self_citation_crs_calc(cited_paper, citing_paper)
                country_self_citation += citing_paper.self_citation_crs
            if cited_paper.source_name == citing_paper.source_name:  # For the titles those papers were published in
                if citing_paper.self_citation_crs == 0:
                    self_citation_crs_calc(cited_paper, citing_paper)
                source_self_citation += citing_paper.self_citation_crs
        total_citations += cited_paper.times_cited  # The total citations is going to be the common denominator
    print(f'Coauthor self-citation:\n    Name-level: {(author_name_self_citation/total_citations * 100):.2f}% ({author_name_self_citation} self-citations, {total_citations - author_name_self_citation} external, {total_citations} total)')
    print(f'    DAIS-level: {(author_dais_self_citation/total_citations * 100):.2f}% ({author_dais_self_citation} self-citations, {total_citations - author_dais_self_citation} external, {total_citations} total)')
    print(f'    ResearcherID-level: {(author_rids_self_citation/total_citations * 100):.2f}% ({author_rids_self_citation} self-citations, {total_citations - author_rids_self_citation} external, {total_citations} total)')
    print(f'    ORCID-level: {(author_orcids_self_citation/total_citations * 100):.2f}% ({author_orcids_self_citation} self-citations, {total_citations - author_orcids_self_citation} external, {total_citations} total)')
    print(f'Organization-level self-citation: {(org_self_citation/total_citations * 100):.2f}% ({org_self_citation} self-citations, {total_citations - org_self_citation} external, {total_citations} total)')
    print(f'Country-level self-citation: {(country_self_citation/total_citations * 100):.2f}% ({country_self_citation} self-citations, {total_citations - country_self_citation} external, {total_citations} total)')
    print(f'Publication Source-level self-citation: {(source_self_citation/total_citations * 100):.2f}% ({source_self_citation} self-citations, {total_citations - source_self_citation} external, {total_citations} total)')


a = cited_papers()
b = citing_papers(a)
self_citations(a)
