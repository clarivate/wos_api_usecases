"""
Manage all the key functions after the 'Run' button is pressed,
mostly data processing.
"""

from datetime import date
import pandas as pd
from api_operations import (
    researcher_api_request,
    researcher_api_profile_request
)


def run_button(apikey: str, query: str, full_profiles: bool) -> str:
    """When the 'Run' button is pressed, manage all the API operations
    and data processing."""

    if full_profiles:
        profiles = retrieve_full_profiles_metadata(apikey, query)
    else:
        profiles = retrieve_profiles_metadata(apikey, query)

    df = pd.DataFrame(profiles)

    safe_search_query = (query.replace("*", "").replace("?", "")
                         .replace('"', '').replace("/", ''))
    if full_profiles:
        safe_filename = f'{safe_search_query} - full profiles - {date.today()}.xlsx'

        pub_years_df = pd.json_normalize(df['published_years'])
        pub_years_df = pub_years_df[sorted(pub_years_df.columns)]
        df2 = pd.concat([df[['primary_rid', 'fullname']], pub_years_df], axis=1)

        df_exploded = df.explode('other_affiliations').reset_index(drop=True)
        affiliations_df = pd.json_normalize(df_exploded['other_affiliations'])
        df3 = pd.concat([df_exploded[['primary_rid', 'fullname']], affiliations_df], axis=1)

        awards_df = pd.json_normalize(df['awards'])
        awards_df = awards_df[sorted(awards_df.columns)]
        df4 = pd.concat([df[['primary_rid', 'fullname']], awards_df], axis=1)

        df = df.drop(['published_years', 'other_affiliations', 'awards'], axis=1)

        with pd.ExcelWriter(f'downloads/{safe_filename}') as writer:
            df.to_excel(writer, sheet_name='Researchers', index=False)
            df2.to_excel(writer, sheet_name='Publication Years', index=False)
            df3.to_excel(writer, sheet_name='Other Affiliations', index=False)
            df4.to_excel(writer, sheet_name='Awards', index=False)

    else:
        safe_filename = f'{safe_search_query} - {date.today()}.xlsx'
        with pd.ExcelWriter(f'downloads/{safe_filename}') as writer:
            df.to_excel(writer, sheet_name='Researchers', index=False)

    return safe_filename


def retrieve_profiles_metadata(apikey: str, query: str) -> list[dict]:
    """Manage API calls and parsing Researcher Profiles metadata from a
    search query."""

    profiles = []
    initial_json = researcher_api_request(apikey, query)
    for profile in initial_json['hits']:
        profiles.append(fetch_researchers_data(profile))
    total_profiles = initial_json['metadata']['total']
    requests_required = (total_profiles - 1) // 50 + 1
    max_requests = min(requests_required, 1000)
    print(f'Researcher API requests required: {requests_required}.')

    for i in range(1, max_requests):
        subsequent_json = researcher_api_request(apikey, query, i+1)
        for profile in subsequent_json['hits']:
            profiles.append(fetch_researchers_data(profile))
        print(f'Request {i + 1} of {max_requests} complete.')

    return profiles


def retrieve_full_profiles_metadata(apikey: str, query: str) -> list[dict]:
    """Manage API calls and parsing full Researcher Profiles metadata."""

    profiles = []
    rids = []

    # Getting the list of ResearcherIDs
    initial_rid_json = researcher_api_request(apikey, query)
    for profile in initial_rid_json['hits']:
        rids.append(profile['rid'][0])
    total_profiles = initial_rid_json['metadata']['total']
    requests_required = (total_profiles - 1) // 50 + 1
    max_requests = min(requests_required, 1000)
    print(f'Step 1. Retrieving Researcher IDs, requests required: '
          f'{requests_required}.')

    for i in range(1, max_requests):
        subsequent_rid_json = researcher_api_request(apikey, query, i+1)
        for profile in subsequent_rid_json['hits']:
            rids.append(profile['rid'][0])
        print(f'Request {i + 1} of {max_requests} complete.')

    # Getting their full profile metadata
    print(f'Step 2. Retrieving full profile metadata, requests required: '
          f'{len(rids)}.')
    for i, rid in enumerate(rids):
        full_profile_json = researcher_api_profile_request(apikey, rid)
        profiles.append(fetch_full_researchers_data(full_profile_json))

        print(f'Request {i + 1} of {len(rids)} complete.')

    return profiles


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

    prim_affil = json['organization']['primaryAffiliation']
    primary_affiliation = '; '.join(set(a['organizationEnhancedName'] for a in prim_affil))
    primary_aff_countries = '; '.join(set(a['country'] for a in prim_affil))
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
