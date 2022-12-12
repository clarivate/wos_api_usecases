"""
This code uses Web of Science Lite API (you can also use Starter or Expanded API instead) to retrieve documents
from Web of Science Core Collectrion using a topical search request that can be specified by the user under the
TOPICAL_SEARCH constant. It then sends a similar topical search request to Derwent Innovation using Derwent API, and
breaks the results down by year. Finally, it uses Plotly to build an interactive trend graph to assess the increase or
decrease in the amount of scholarly documents or patent families related to this topic. It also saves the retrieved
time series into a .csv file for further analysis.
"""

import urllib.parse
import requests
import time
import pandas as pd
import plotly.express as px
from datetime import date
from dash import Dash
from apikeys import LITE_KEY, USERNAME, PASSWORD  # Create a separate apikey.py file in the project folder

TOPICAL_SEARCH = 'metasurface*'  # Enter the search query here

LITE_HEADERS = {'X-APIKey': LITE_KEY}
LITE_BASEURL = "https://api.clarivate.com/api/woslite"
DERWENT_HEADERS = {'Content-type': 'apiUI/json', 'Accept': 'text/plain'}
DERWENT_URL = 'https://services.derwentinnovation.com/ip-webservices/xrpc'

# Sending an initial WoS API request to assess the number of requests required
initial_wos_response = requests.get(f'{LITE_BASEURL}?databaseId=WOS&usrQuery=TS="{urllib.parse.quote(TOPICAL_SEARCH)}"'
                                f'&count=0&firstRecord=1', headers=LITE_HEADERS)
data = initial_wos_response.json()
requests_required = (((data['QueryResult']['RecordsFound'] - 1) // 100) + 1)
wos_data = []


# A function for the WoS API requests for retrieving all the WoS document data
def wos_api_request(i):
    request = requests.get(
        f'{LITE_BASEURL}?databaseId=WOS&usrQuery=TS="{urllib.parse.quote(TOPICAL_SEARCH)}"&count=100&'
        f'firstRecord={i}01', headers=LITE_HEADERS)
    try:
        for wos_record in request.json()['Data']:
            wos_data.append(wos_record)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i+1}')
        time.sleep(100)
        wos_api_request(i)


# A function for the Derwent API single-word requests for retrieving all the patent data
def derwent_api_request_single_term(i):
    searchByQuery_JSON = [
        {
            "fn": "SessionManager.authenticateUser",
            "params": [{
                "username": USERNAME,
                "password": PASSWORD,
            }]
        },
        {
            "fn": "Tsip.searchByQuery",
            "params": [{
                "query": f"ti=('{(TOPICAL_SEARCH)}') OR "
                         f"tid=('{(TOPICAL_SEARCH)}') OR "
                         f"tit=('{(TOPICAL_SEARCH)}') OR "
                         f"ab=('{(TOPICAL_SEARCH)}') OR "
                         f"abd=('{(TOPICAL_SEARCH)}') OR "
                         f"cl=('{(TOPICAL_SEARCH)}') OR "
                         f"dsc=('{(TOPICAL_SEARCH)}')",
                "collections": "all",
                "offset": f'{i}000',
                "size": "1000",
                "listref": "",
                "return-fields": "pn,prye,prd,pd",
                "search-on-datatype": "fld_dwpi",
                "return-listref": "true",
                "return-request": "true",
                "return-body": "true",
                "return-documents": "",
                "dwpi-basic": "true",
                "return-metainfo": "true",
                "display-limit": "1000000",
                "search-limit": "1000000",
                "filter": "collapse:derwent-family",
                "list-format": ""
            }]
        }
    ]

    APIResponse = requests.post(DERWENT_URL, json=searchByQuery_JSON, headers=DERWENT_HEADERS)

    try:
        di_data = APIResponse.json()
        for di_record in di_data['responseBody']['docs']:
            di_records.append(di_record)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending Derwent API request #{i+1}')
        time.sleep(100)
        derwent_api_request_single_term(i)


# A similar function for multi-word topical requests for Derwent
def derwent_api_request_multiple_terms(i):
    searchByQuery_JSON = [
        {
            "fn": "SessionManager.authenticateUser",
            "params": [{
                "username": USERNAME,
                "password": PASSWORD,
            }]
        },
        {
            "fn": "Tsip.searchByQuery",
            "params": [{
                "query": f"ti=({(topical_search_adj)}) OR "
                         f"tid=({(topical_search_adj)}) OR "
                         f"tit=({(topical_search_adj)}) OR "
                         f"ab=({(topical_search_adj)}) OR "
                         f"abd=({(topical_search_adj)}) OR "
                         f"cl=({(topical_search_adj)}) OR "
                         f"dsc=({(topical_search_adj)})",
                "collections": "all",
                "offset": f'{i}000',
                "size": "1000",
                "listref": "",
                "return-fields": "pn,prye,prd,pd",
                "search-on-datatype": "fld_dwpi",
                "return-listref": "true",
                "return-request": "true",
                "return-body": "true",
                "return-documents": "",
                "dwpi-basic": "true",
                "return-metainfo": "true",
                "display-limit": "1000000",
                "search-limit": "1000000",
                "filter": "collapse:derwent-family",
                "list-format": ""
            }]
        }
    ]

    APIResponse = requests.post(DERWENT_URL, json=searchByQuery_JSON, headers=DERWENT_HEADERS)

    try:
        di_data = APIResponse.json()
        for di_record in di_data['responseBody']['docs']:
            di_records.append(di_record)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending Derwent API request #{i+1}')
        time.sleep(100)
        derwent_api_request_multiple_terms(i)


# This cycle launches the necessary number of WoS API requests
for i in range(requests_required):
    wos_api_request(i)
    print(f"{(((i + 1) * 100) / requests_required):.1f}% of WoS API requests complete")

# We are going to store the trend data as dictionaries in this list
years = []

# Extracting the publication years values from retrieved Web of Science data
for paper in wos_data:
    if len(years) == 0:
        years.append({
            'year': int(paper['Source']['Published.BiblioYear'][0]),
            'wos_documents': 1,
            'di_pry': 0,
            'di_py': 0
        })
    else:
        for year in years:
            if year['year'] == int(paper['Source']['Published.BiblioYear'][0]):
                year['wos_documents'] += 1
                break
        else:
            years.append({
            'year': int(paper['Source']['Published.BiblioYear'][0]),
            'wos_documents': 1,
            'di_pry': 0,
            'di_py': 0
        })

# An initial Derwent API request to assess the total number of search results
if ' ' in TOPICAL_SEARCH: # if there are spaces in the search query, the request contains multiple terms
    topical_search_adj = TOPICAL_SEARCH.replace(' ', ' ADJ ')
    initialsearchByQuery_JSON = [
        {
            "fn": "SessionManager.authenticateUser",
            "params": [{
                "username": USERNAME,
                "password": PASSWORD,
            }]
        },
        {
            "fn": "Tsip.searchByQuery",
            "params": [{
                "query": f"ti=({(topical_search_adj)}) OR "
                         f"tid=({(topical_search_adj)}) OR "
                         f"tit=({(topical_search_adj)}) OR "
                         f"ab=({(topical_search_adj)}) OR "
                         f"abd=({(topical_search_adj)}) OR "
                         f"cl=({(topical_search_adj)}) OR "
                         f"dsc=({(topical_search_adj)})",
                "collections": "all",
                "offset": "0",
                "size": "0",
                "listref": "",
                "return-fields": "pn,prye,prd,pd",
                "search-on-datatype": "fld_dwpi",
                "return-listref": "true",
                "return-request": "true",
                "return-body": "true",
                "return-documents": "false",
                "dwpi-basic": "true",
                "return-metainfo": "true",
                "display-limit": "1000000",
                "search-limit": "1000000",
                "filter": "collapse:derwent-family",
                "list-format": ""
            }]
        }
    ]

    APIResponse = requests.post(DERWENT_URL, json=initialsearchByQuery_JSON, headers=DERWENT_HEADERS)
    di_data = APIResponse.json()

    requests_required = (((int(di_data['responseHeader']['search-response']['size']) - 1) // 1000) + 1)
    di_records = []

    # Getting all the necessary patent records via Derwent API.
    for i in range(requests_required):
        derwent_api_request_multiple_terms(i)
        print(f"{(((i + 1) * 100) / requests_required):.1f}% of Derwent API requests complete")
else: # if there are no spaces in the search query, the request contains only one term
    initialsearchByQuery_JSON = [
        {
            "fn":"SessionManager.authenticateUser",
            "params":[{
               "username": USERNAME,
               "password": PASSWORD,
            }]
        },
        {
            "fn":"Tsip.searchByQuery",
            "params":[{
                "query": f"ti=('{(TOPICAL_SEARCH)}') OR "
                         f"tid=('{(TOPICAL_SEARCH)}') OR "
                         f"tit=('{(TOPICAL_SEARCH)}') OR "
                         f"ab=('{(TOPICAL_SEARCH)}') OR "
                         f"abd=('{(TOPICAL_SEARCH)}') OR "
                         f"cl=('{(TOPICAL_SEARCH)}') OR "
                         f"dsc=('{(TOPICAL_SEARCH)}')",
                "collections":"all",
                "offset":"0",
                "size":"0",
                "listref":"",
                "return-fields":"pn,prye,prd,pd",
                "search-on-datatype":"fld_dwpi",
                "return-listref":"true",
                "return-request":"true",
                "return-body":"true",
                "return-documents":"false",
                "dwpi-basic":"true",
                "return-metainfo":"true",
                "display-limit": "1000000",
                "search-limit":"1000000",
                "filter":"collapse:derwent-family",
                "list-format":""
            }]
        }
    ]

    APIResponse = requests.post(DERWENT_URL, json=initialsearchByQuery_JSON, headers=DERWENT_HEADERS)
    di_data = APIResponse.json()

    requests_required = (((int(di_data['responseHeader']['search-response']['size']) - 1) // 1000) + 1)
    di_records = []

    # Getting all the necessary patent records via Derwent API.
    for i in range(requests_required):
        derwent_api_request_single_term(i)
        print(f"{(((i + 1) * 100) / requests_required):.1f}% of Derwent API requests complete")

# Extracting priority years and publication years values from Derwent data
for di_document in di_records:
    # if the document's RefID exists, this means the record is a family member and thus skipped in the analysis
    try:
        if di_document[list(di_document)[0]]['RefId'] is True:
            continue
    except KeyError:
        key = str(di_document.keys())
        key = key[12:-3]
        for field in di_document[list(di_document)[0]]['fields']:
            if list(field)[0] == 'prd':
                priority_date = field[list(field)[0]]['value']
                priority_year = int(priority_date[:4])
                if len(years) == 0:
                    years.append({'year': priority_year, 'wos_documents': 0, 'di_pry': 1, 'di_py': 0})
                else:
                    for year in years:
                        if year['year'] == priority_year:
                            year['di_pry'] += 1
                            break
                    else:
                        years.append({'year': priority_year, 'wos_documents': 0, 'di_pry': 1, 'di_py': 0})
                break
        else:
            print(f'No Priority Year data: {di_document}')
        for field in di_document[list(di_document)[0]]['fields']:
            if list(field)[0] == 'pd':
                pub_date = field[list(field)[0]]['value']
                pub_year = int(pub_date[:4])
                if len(years) == 0:
                    years.append({'year': pub_year, 'wos_documents': 0, 'di_pry': 0, 'di_py': 1})
                else:
                    for year in years:
                        if year['year'] == pub_year:
                            year['di_py'] += 1
                            break
                    else:
                        years.append({'year': pub_year, 'wos_documents': 0, 'di_pry': 0, 'di_py': 1})
                break
        else:
            print(f'No Publication Year data: {di_document}')

# Sorting the values by year, largest to smallest, to save them into a .csv file
years.sort(reverse=True, key=lambda years: years['year'])

# Saving the created list to a .csv file
with open(f"trends - {TOPICAL_SEARCH.replace('?','').replace('$','').replace('&','').replace('*','')} - by families - "
          f"{date.today()}.csv", 'w') as writing:
    writing.write(f'Topical Search:,{TOPICAL_SEARCH}\n'
                  f'\nYear,Web of Science Documents,Derwent Innovation - Patent Families (Earliest Priority Year),'
                  f'Derwent Innovation - Patent Families (Publication Year)\n')
    for year in years:
        writing.writelines(
        f'{year["year"]},{year["wos_documents"]},{year["di_pry"]},{year["di_py"]}\n'
        )


# Converting our list of dictionaries into a dataframe
df = pd.DataFrame(data=years[:-1])

app = Dash(__name__)

# Setting up the plot
fig = px.bar(data_frame=df,
             x='year',
             y=['wos_documents',
                'di_pry',
                'di_py'],
             barmode='group',
             color_discrete_sequence=['#5E33BF', '#16AB03', '#000000'],
             title=f'Topical Search: {TOPICAL_SEARCH}')

# Changing the legend label names
newnames = {'wos_documents': 'Web of Science Documents',
            'di_pry': 'Derwent Innovation - Patent Families (Earliest Priority Year)',
            'di_py': 'Derwent Innovation - Patent Families (Publication Year)'}
fig.for_each_trace(lambda t: t.update(name = newnames[t.name]))

# Making cosmetic edits to the plot
fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)', 'paper_bgcolor': 'rgba(0, 0, 0, 0)'},
                  font_family='Calibri',
                  font_color='#646363',
                  font_size=18,
                  title_font_family='Calibri',
                  title_font_color='#646363',
                  legend_title_text=None,
                  legend=dict(
                      yanchor="bottom",
                      y=-0.4,
                      xanchor="center",
                      x=0.5
                  ))
fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C')
fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

fig.show()
