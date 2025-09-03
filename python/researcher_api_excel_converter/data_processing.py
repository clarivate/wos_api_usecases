"""
Manage all the key functions after the 'Run' button is pressed,
mostly data processing.
"""

from datetime import date
import pandas as pd
from api_operations import (
    researcher_api_request,
    researcher_api_profile_request,
    researcher_api_doc_request,
    peer_review_api_request
)


def main(query: str, options: dict) -> str:
    """When the 'Run' button is pressed, manage all the API operations
    and data processing."""

    profiles = (
        retrieve_full_profiles_metadata(query)
        if options['full_profiles']
        else retrieve_profiles_metadata(query)
    )

    safe_search_query = (
        query.replace("*", "")
        .replace("?", "")
        .replace('"', '')
        .replace("/", '')
    )

    df2 = df3 = df4 = df5 = df6 = None

    if options['full_profiles']:
        df, df2, df3, df4 = manage_full_profiles(profiles)
    else:
        df = pd.DataFrame(profiles)

    if options['documents']:
        df5 = retrieve_documents_metadata(profiles)

    if options['peer_reviews']:
        df6 = retrieve_peer_reviews_metadata(profiles)

    safe_filename = f'{safe_search_query} - {date.today()}.xlsx'
    with pd.ExcelWriter(f'downloads/{safe_filename}') as writer:
        df.to_excel(writer, sheet_name='Researchers', index=False)
        if options['full_profiles']:
            df2.to_excel(writer, sheet_name='Publication Years', index=False)
            df3.to_excel(writer, sheet_name='Other Affiliations', index=False)
            df4.to_excel(writer, sheet_name='Awards', index=False)
        if options['documents']:
            df5.to_excel(writer, sheet_name='Documents', index=False)
        if options['peer_reviews']:
            df6.to_excel(writer, sheet_name='Peer Reviews', index=False)

    return safe_filename


def manage_full_profiles(profiles: list[dict]) -> tuple:
    """Manage all functions related to extracting the full profiles
    metadata."""

    df = pd.DataFrame(profiles)
    pub_years_df = pd.json_normalize(df['published_years'])
    pub_years_df = pub_years_df[sorted(pub_years_df.columns)]
    df2 = pd.concat([df[['primary_rid', 'fullname']], pub_years_df], axis=1)

    df_exploded = df.explode('other_affiliations').reset_index(drop=True)
    affiliations_df = pd.json_normalize(df_exploded['other_affiliations'])
    df3 = pd.concat([df_exploded[['primary_rid', 'fullname']], affiliations_df], axis=1)

    non_empty_awards_df = df[df['awards'].apply(
        lambda x: isinstance(x, dict) and bool(x)
    )].copy()

    awards_only_df = pd.json_normalize(non_empty_awards_df['awards'])

    awards_only_df = awards_only_df[sorted(awards_only_df.columns)]
    df4 = pd.concat([non_empty_awards_df[
                         ['primary_rid', 'fullname']
                     ].reset_index(drop=True),
                     awards_only_df.reset_index(drop=True)], axis=1)

    df = df.drop(['published_years', 'other_affiliations', 'awards'], axis=1)

    return df, df2, df3, df4


def retrieve_profiles_metadata(query: str) -> list[dict]:
    """Manage API calls and parsing Researcher Profiles metadata from a
    search query."""

    profiles = []
    initial_json = researcher_api_request(query)
    for profile in initial_json['hits']:
        profiles.append(fetch_researchers_data(profile))
    total_profiles = initial_json['metadata']['total']
    requests_required = (total_profiles - 1) // 50 + 1
    max_requests = min(requests_required, 1000)
    print(f'Researcher API search requests required: {requests_required}.')

    for i in range(1, max_requests):
        subsequent_json = researcher_api_request(query, i+1)
        for profile in subsequent_json['hits']:
            profiles.append(fetch_researchers_data(profile))
        print(f'Request {i + 1} of {max_requests} complete.')

    return profiles


def retrieve_full_profiles_metadata(query: str) -> list[dict]:
    """Manage API calls and parsing full Researcher Profiles
    metadata."""

    profiles = []
    rids = []

    # Getting the list of ResearcherIDs
    initial_rid_json = researcher_api_request(query)
    for profile in initial_rid_json['hits']:
        rids.append(profile['rid'][0])
    total_profiles = initial_rid_json['metadata']['total']
    requests_required = (total_profiles - 1) // 50 + 1
    max_requests = min(requests_required, 1000)
    print(f'Step 1. Retrieving Researcher IDs, requests required: '
          f'{requests_required}.')

    for i in range(1, max_requests):
        subsequent_rid_json = researcher_api_request(query, i+1)
        for profile in subsequent_rid_json['hits']:
            rids.append(profile['rid'][0])
        print(f'Request {i + 1} of {max_requests} complete.')

    # Getting their full profile metadata
    print(f'Step 2. Retrieving full profile metadata, requests required: '
          f'{len(rids)}.')
    for i, rid in enumerate(rids):
        full_profile_json = researcher_api_profile_request(rid)
        profiles.append(fetch_full_researchers_data(full_profile_json))

        print(f'Request {i + 1} of {len(rids)} complete.')

    return profiles


def retrieve_documents_metadata(profiles: list[dict]) -> pd.DataFrame:
    """Break down the list into individual researchers, and launch
    the function to get their individual documents lists."""

    documents = []

    for i, profile in enumerate(profiles):
        print(f'Retrieving documents metadata for researcher #{i+1} of '
              f'{len(profiles)}')
        documents.extend(get_individual_researchers_docs_list(profile))

    return pd.DataFrame(documents)


def get_individual_researchers_docs_list(profile: dict) -> list[dict]:
    """Manage API calls and parsing documents metadata."""

    docs = []

    initial_doc_json = researcher_api_doc_request(profile['primary_rid'])
    for doc in initial_doc_json['hits']:
        docs.append(fetch_documents_metadata(profile['primary_rid'], doc))
    total_docs = initial_doc_json['metadata']['total']
    requests_required = (total_docs - 1) // 50 + 1
    max_requests = min(requests_required, 1000)

    for i in range(1, max_requests):
        subsequent_doc_json = researcher_api_doc_request(
            profile['primary_rid'],
            i + 1
        )

        for doc in subsequent_doc_json['hits']:
            docs.append(fetch_documents_metadata(profile['primary_rid'], doc))

    return docs


def retrieve_peer_reviews_metadata(profiles: list[dict]) -> pd.DataFrame:
    """Break down the list into individual researchers, and launch
    the function to get their individual documents lists."""

    peer_reviews = []

    for i, profile in enumerate(profiles):
        print(f'Retrieving peer review metadata for researcher #{i + 1} of '
              f'{len(profiles)}')
        peer_reviews.extend(get_individual_peer_reviews_list(profile))

    return pd.DataFrame(peer_reviews)


def get_individual_peer_reviews_list(profile: dict) -> list[dict]:
    """Manage API calls and parsing peer reviews metadata."""

    peer_reviews = []
    initial_peer_review_json = peer_review_api_request(profile['primary_rid'])
    for peer_review in initial_peer_review_json['hits']:
        peer_reviews.append(
            fetch_peer_review_metadata(
                profile['primary_rid'],
                peer_review
            )
        )

    total_peer_reviews = initial_peer_review_json['metadata']['total']
    requests_required = (total_peer_reviews - 1) // 50 + 1
    max_requests = min(requests_required, 1000)

    for i in range(1, max_requests):
        subsequent_peer_review_json = peer_review_api_request(
            profile['primary_rid'],
            i + 1
        )
        for peer_review in subsequent_peer_review_json['hits']:
            peer_reviews.append(
                fetch_peer_review_metadata(
                    profile['primary_rid'],
                    peer_review
                )
            )

    return peer_reviews


def fetch_researchers_data(rec: dict) -> dict:
    """Fetch individual metadata fields from the basic researcher
    metadata."""

    if len(rec['rid']) > 1:
        other_rids = ", ".join(rec['rid'][1:])
    else:
        other_rids = ''

    return {
        'primary_rid': rec['rid'][0],
        'other_rids': other_rids,
        'orcid': ", ".join(rec['orcids']),
        'fullname': rec['fullName'],
        'primary_affiliation': ", ".join(rec['primaryAffiliation']),
        'link': rec['self'],
        'documents_count': rec['documentsCount']['count'],
        'times_cited': rec['totalTimesCited'],
        'h-index': rec['hIndex'],
        'documents_link': rec['documentsCount']['self'],
        }


def fetch_full_researchers_data(json: dict) -> dict:
    """Fetch all metadata fields from the full researcher profile
    metadata."""

    if len(json['ids']['rids']) > 1:
        other_rids = ", ".join(json['ids']['rids'][1:])
    else:
        other_rids = ''

    alt_names = '; '.join(
        alt['name'] for alt in json['name']['alternativeNames']
    )

    metrics = json['metricsAllTime']
    published_years = {
        year['year']: year['numberOfDocuments']
        for year in metrics['documents']['publishedYears']
    }

    primary_affiliations_section = json['organization']['primaryAffiliation']
    primary_affiliation = '; '.join(
        set(
            a['organizationEnhancedName']
            for a in primary_affiliations_section
        )
    )

    primary_aff_countries = '; '.join(
        set(
            a['country']
            for a
            in primary_affiliations_section
        )
    )

    departments = '; '.join(d for d in json['organization']['departments'])

    affiliations = [
        {
            'affiliation': a['organization'],
            'start_year': a['startYear'],
            'end_year': a['endYear'],
            'num_docs': a['numberOfDocuments']
    }
        for a in json['organization']['affiliations']
    ]

    pos = json['authorPosition']
    subject_categories = '; '.join(cat for cat in json['subjectCategories'])
    if json['awards']['highlyCitedResearcher']:
        awards = {
            award['year']: award['category']
            for award in json['awards']['highlyCitedResearcherYear']
    }
    else:
        awards = {}

    return {
        'primary_rid': json['ids']['rids'][0],
        'other_rids': other_rids,
        'orcid': ", ".join(json['ids']['orcids']),
        'claim_status': json['claimStatus'],
        'fullname': json['name']['fullName'],
        'first_name': json['name']['firstName'],
        'last_name': json['name']['lastName'],
        'alt_names': alt_names,
        'docs_count': metrics['documents']['count'],
        'times_cited': metrics['totalTimesCited'],
        'times_cited_excl_self': metrics['totalTimesCitedWithoutSelf'],
        'citing_publications': metrics['totalCitingPublications'],
        'citing_publications_excl_self': metrics['totalCitingWithoutSelf'],
        'h_index': metrics['hindex'],
        'published_years': published_years,
        'docs_self': metrics['documents']['self'],
        'primary_org_addresses': primary_affiliation,
        'primary_org_countries': primary_aff_countries,
        'departments': departments,
        'other_affiliations': affiliations,
        'author_position_first': pos['first']['numberOfDocuments'],
        'author_position_last': pos['last']['numberOfDocuments'],
        'author_position_corr': pos['corresponding']['numberOfDocuments'],
        'subject_categories': subject_categories,
        'awards': awards
    }


def fetch_documents_metadata(rid: str, doc: dict) -> dict:
    """Fetch individual metadata fields from the document metadata."""

    return {
        'rid': rid,
        'ut': doc['uid'],
        'document_title': doc['title'],
        'doc_type': '; '.join(doc['types']),
        'source_title': doc['source']['sourceTitle'],
        'publication_year': doc['source']['publishYear'],
        'publication_date': doc['source']['sortDate'],
        'volume': doc['source']['volume'] if 'volume' in doc['source'] else '',
        'issue': doc['source']['issue'] if 'issue' in doc['source'] else '',
        'times_cited': doc['citations'][0]['count'],
        'doi': doc['identifiers']['doi'] if 'doi' in doc['identifiers'] else ''
    }


def fetch_peer_review_metadata(rid: str, pr: dict) -> dict:
    """Fetch individual metadata fields from the peer reviews
    metadata."""

    return {
        'rid': rid,
        'journal': pr['journal'] if 'journal' in pr else '',
        'publisher': pr['publisher'] if 'publisher' in pr else '',
        'review_year': pr['dateOfReview'],
        'verified': pr['verified'],
    }
