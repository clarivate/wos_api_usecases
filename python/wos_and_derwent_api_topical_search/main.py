"""
This code uses Web of Science Lite API (you can also use Starter or Expanded API instead) to retrieve documents
from Web of Science Core Collection using a topical search request that can be specified by the user under the
TOPICAL_SEARCH constant. It then sends a similar topical search request to Derwent Innovation using Derwent API, and
breaks the results down by year. Finally, it uses Plotly to build an interactive trend graph to assess the increase or
decrease in the amount of scholarly documents or patent families related to this topic. It also saves the retrieved
time series into a .csv file for further analysis.
"""

import urllib.parse
import time
import threading
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import ttk, StringVar
from tkinter.filedialog import askopenfilename
from datetime import date
import plotly.express as px
import pandas as pd
import requests


DERWENT_HEADERS = {'Content-type': 'apiUI/json', 'Accept': 'text/plain'}
DERWENT_URL = 'https://services.derwentinnovation.com/ip-webservices/xrpc'


# A function for the WoS Lite API requests for retrieving the WoS document data
def lite_api_request(i, search_query, wos_data):
    request = requests.get(
        f'https://api.clarivate.com/api/woslite?databaseId=WOS&usrQuery=TS="{urllib.parse.quote(search_query)}"&'
        f'count=100&firstRecord={i}01', headers={'X-APIKey': app.apikey_window.get()})
    try:
        for wos_record in request.json()['Data']:
            wos_data.append(wos_record)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i+1}')
        time.sleep(100)
        lite_api_request(i, search_query, wos_data)


# A function for the Expanded API requests for retrieving the WoS document data
def expanded_api_request(i, search_query, wos_data):
    request = requests.get(
        f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery=TS="{urllib.parse.quote(search_query)}"&'
        f'count=100&firstRecord={i}01', headers={'X-APIKey': app.apikey_window.get()})
    try:
        for wos_record in request.json()['Data']['Records']['records']['REC']:
            wos_data.append(wos_record)
    except(requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i+1}')
        time.sleep(100)
        expanded_api_request(i, search_query, wos_data)


# A function for the Starter API requests for retrieving the WoS document data
def starter_api_request(i, search_query, wos_data):
    request = requests.get(
        f'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q=TS="{urllib.parse.quote(search_query)}"&'
        f'limit=50&page={i+1}', headers={'X-APIKey': app.apikey_window.get()})
    try:
        for wos_record in request.json()['hits']:
            wos_data.append(wos_record)
    except(requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i+1}')
        time.sleep(100)
        starter_api_request(i, search_query, wos_data)


# An initial Derwent API request to assess the total number of search results
def initial_derwent_request(search_query):
    initialsearch_by_query_json = [
        {
            "fn": "SessionManager.authenticateUser",
            "params": [{
                "username": app.username_window.get(),
                "password": app.password_window.get(),
            }]
        },
        {
            "fn": "Tsip.searchByQuery",
            "params": [{
                "query": f"ti=({search_query}) OR "
                         f"tid=({search_query}) OR "
                         f"tit=({search_query}) OR "
                         f"ab=({search_query}) OR "
                         f"abd=({search_query}) OR "
                         f"cl=({search_query}) OR "
                         f"dsc=({search_query})",
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

    api_response = requests.post(DERWENT_URL, json=initialsearch_by_query_json, headers=DERWENT_HEADERS)
    di_data = api_response.json()

    requests_required = (((int(di_data['responseHeader']['search-response']['size']) - 1) // 1000) + 1)
    return requests_required


# A function for Derwent API requests for retrieving the patent document data
def derwent_api_request(i, search_query, di_data):
    search_by_query_json = [
        {
            "fn": "SessionManager.authenticateUser",
            "params": [{
                "username": app.username_window.get(),
                "password": app.password_window.get(),
            }]
        },
        {
            "fn": "Tsip.searchByQuery",
            "params": [{
                "query": f"ti=({search_query}) OR "
                         f"tid=({search_query}) OR "
                         f"tit=({search_query}) OR "
                         f"ab=({search_query}) OR "
                         f"abd=({search_query}) OR "
                         f"cl=({search_query}) OR "
                         f"dsc=({search_query})",
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

    api_response = requests.post(DERWENT_URL, json=search_by_query_json, headers=DERWENT_HEADERS)

    try:
        di_response = api_response.json()
        for di_record in di_response['responseBody']['docs']:
            di_data.append(di_record)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending Derwent API request #{i+1}')
        time.sleep(100)
        derwent_api_request(i, search_query, di_data)


# Getting the necessary publication and priority years from data retrieved through the APIs
def process_data(wos_data, di_data, wos_api_type):
    # We are going to store the trend data as dictionaries in this list
    years = []

    # Extracting the publication years values from retrieved Web of Science data
    for paper in wos_data:
        if wos_api_type == 'lite':
            pub_year = int(paper['Source']['Published.BiblioYear'][0])
        elif wos_api_type == 'expanded':
            pub_year = int(paper['static_data']['summary']['pub_info']['pubyear'])
        else:
            pub_year = int(paper['source']['publishYear'])
        if len(years) == 0:
            years.append({
                'year': pub_year,
                'wos_documents': 1,
                'di_pry': 0,
                'di_py': 0
            })
        else:
            for year in years:
                if year['year'] == pub_year:
                    year['wos_documents'] += 1
                    break
            else:
                years.append({
                    'year': pub_year,
                    'wos_documents': 1,
                    'di_pry': 0,
                    'di_py': 0
                })

    # Extracting priority years and publication years values from Derwent data
    for di_document in di_data:
        # if the document's RefID exists, this means the record is a family member and thus skipped in the analysis
        try:
            if di_document[list(di_document)[0]]['RefId'] is True:
                continue
        except KeyError:
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
    return years


# Formatting the text lines for the function below
def format_line(text, line_start, symbol_limit, safe_text):
    if line_start + symbol_limit > len(text):
        safe_text += f'{text[line_start:len(text)]}\n'
        return safe_text, line_start
    for i in range(symbol_limit):
        if text[(line_start + symbol_limit) - i] == ' ':
            line_end = line_start + symbol_limit - i + 1
            safe_text += f'{text[line_start:line_end]}\n'
            return safe_text, line_end


# A function for word wrapping in longer messages
def format_label_text(text, symbol_limit):
    safe_text = ''
    line_start = 0
    if len(text) > symbol_limit:
        lines_amount = (len(text) // symbol_limit) + 1
        for line_number in range(lines_amount):
            safe_text, line_start = format_line(text, line_start, symbol_limit, safe_text)
        return safe_text
    return text


# A function for checking the validity of the Web of Science API key and which Web of Science API type to use
def validate_api_key():
    user_apikey = app.apikey_window.get()
    # Sending an Expanded test request to check if it passes authentication
    validation_request_expanded = requests.get(
        'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery=AU=Garfield&count=0&firstRecord=1',
        headers={'X-APIKey': user_apikey}
    )
    if validation_request_expanded.status_code == 200:
        # If the API call with this key is a success, we're also return the amount of records remaining
        docs_left = validation_request_expanded.headers['X-REC-AmtPerYear-Remaining']
        app.apikey_bottom_label['text'] = f"Expanded API authentication succeeded; Records left to retrieve: " \
                                          f"{docs_left}"
        return 'expanded'
    # If the Expanded API request status is anything but 200, sending a Lite API test request
    validation_request_free = requests.get(
        'https://api.clarivate.com/api/woslite?databaseId=WOS&usrQuery=AU=Garfield&count=0&firstRecord=1',
        headers={'X-APIKey': user_apikey}
    )
    if validation_request_free.status_code == 200:
        app.apikey_bottom_label['text'] = 'Lite API authentication succeeded'
        return 'lite'
    # If the Lite API request status is anything but 200, sending a Starter API test request
    validation_request_starter = requests.get(
        'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q=AU=Garfield&limit=1&page=1',
        headers={'X-APIKey': user_apikey}
    )
    if validation_request_starter.status_code == 200:
        requests_left_today = validation_request_starter.headers['X-RateLimit-Remaining-Day']
        if int(requests_left_today) < 100:
            app.apikey_bottom_label['text'] = f'API authentication succeeded; Requests left today:' \
                                              f' {requests_left_today}'
        else:
            app.apikey_bottom_label['text'] = 'Starter API authentication succeeded'
        return 'starter'
    app.apikey_bottom_label['text'] = 'Wrong API Key'
    return None


# A function for checking the validity of the Derwent API username and password
def validate_api_unp():
    username = app.username_window.get()
    password = app.password_window.get()
    validation_request_by_query_json = [
        {
            "fn": "SessionManager.authenticateUser",
            "params": [{
                "username": username,
                "password": password,
            }]
        },
        {
            "fn": "Tsip.searchByQuery",
            "params": [{
                "query": "IN=(garfield adj eugene)",
                "collections": "all",
                "offset": "0",
                "size": "0",
                "listref": "",
                "return-fields": "pn",
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

    api_response = requests.post(DERWENT_URL, json=validation_request_by_query_json, headers=DERWENT_HEADERS)
    if api_response.status_code == 200:
        app.password_bottom_label['text'] = 'Derwent API authentication succeeded'
        try:
            api_response.json()
            return True
        except requests.exceptions.JSONDecodeError:
            app.password_bottom_label['text'] = 'Wrong Derwent API credentials'
            return False
    else:
        return False


# Function to check how many results the search query returns from both databases
def validate_search():
    app.search_query_bottom_label['text'] = 'Validating...\n'
    wos_api_type = validate_api_key()
    if wos_api_type is None:
        app.apikey_bottom_label['text'] = "Wrong API Key"
        return False
    user_apikey = app.apikey_window.get()
    search_query = app.search_query_window.get()
    if wos_api_type == 'expanded':
        validation_request_expanded = requests.get(
            f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery=TS={search_query}&'
            f'count=0&firstRecord=1', headers={'X-APIKey': user_apikey}
        )
        validation_data = validation_request_expanded.json()
        wos_records_found = validation_data['QueryResult']['RecordsFound']
        wos_api_limit = 100000
    elif wos_api_type == 'lite':
        validation_request_lite = requests.get(
            f'https://api.clarivate.com/api/woslite?databaseId=WOS&usrQuery=TS={search_query}&'
            f'count=0&firstRecord=1', headers={'X-APIKey': user_apikey}
        )
        validation_data = validation_request_lite.json()
        wos_records_found = validation_data['QueryResult']['RecordsFound']
        wos_api_limit = 100000
    else:
        validation_request_starter = requests.get(
            f'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q=TS={search_query}&'
            f'limit=1&page=1', headers={'X-APIKey': user_apikey}
        )
        validation_data = validation_request_starter.json()
        wos_records_found = validation_data['metadata']['total']
        wos_api_limit = (int(validation_request_starter.headers['X-RateLimit-Remaining-Day']) - 1) * 50
    username = app.username_window.get()
    password = app.password_window.get()
    if ' ' in search_query:
        search_query = ' ADJ '.join(search_query.split(' '))

    validation_request_by_query_json = [
        {
            "fn": "SessionManager.authenticateUser",
            "params": [{
                "username": username,
                "password": password,
            }]
        },
        {
            "fn": "Tsip.searchByQuery",
            "params": [{
                "query": f"ti=({search_query}) OR "
                         f"tid=({search_query}) OR "
                         f"tit=({search_query}) OR "
                         f"ab=({search_query}) OR "
                         f"abd=({search_query}) OR "
                         f"cl=({search_query}) OR "
                         f"dsc=({search_query})",
                "collections": "all",
                "offset": "0",
                "size": "0",
                "listref": "",
                "return-fields": "pn",
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

    api_response = requests.post(DERWENT_URL, json=validation_request_by_query_json, headers=DERWENT_HEADERS)
    if api_response.status_code == 200:
        try:
            validation_data = api_response.json()
            derwent_records_found = int(validation_data['responseHeader']['search-response']['found'])
        except requests.exceptions.JSONDecodeError:
            try:
                bs_data = ET.fromstring(api_response.text)
                app.search_query_bottom_label['text'] = bs_data[0].text
                return False
            except ET.ParseError:
                derwent_records_found = 0
    else:
        return False
    app.search_query_bottom_label['text'] = f'Web of Science records found: {wos_records_found}\n' \
                                            f'Derwent records found: {derwent_records_found}'
    if wos_records_found == 0 and derwent_records_found == 0:
        return False
    if wos_records_found > wos_api_limit and derwent_records_found <= 1000000:
        text = (f'Web of Science records found: {wos_records_found}. You can export a maximum of {wos_api_limit}'
                f' records through {wos_api_type}. Derwent records found: {derwent_records_found}')
        app.search_query_bottom_label['text'] = format_label_text(text, 94)
        return True
    if wos_records_found <= wos_api_limit and derwent_records_found > 1000000:
        text = (f'Derwent records found: {derwent_records_found}. You can export a maximum of 1M records through '
                f'Derwent API')
        app.search_query_bottom_label['text'] = (f'Web of Science records found: {wos_records_found}\n'
                                                 f'{format_label_text(text, 94)}')
        return True
    if wos_records_found > wos_api_limit and derwent_records_found > 1000000:
        text_1 = (f'Web of Science records found: {wos_records_found}. You can export a maximum of {wos_api_limit} '
                  f'records through {wos_api_type}')
        text_2 = (f'Derwent records found: {derwent_records_found}. You can export a maximum of 1M records through '
                  f'Derwent API')
        app.search_query_bottom_label['text'] = f'{format_label_text(text_1, 94)}\n{format_label_text(text_2, 94)}'
        return True
    return True


# This function starts when the "Run" button is clicked and launches all the others
def main_function():
    app.search_button.config(state='disabled', text='Retrieving...')
    if app.progress_label['text'] != "":
        app.progress_label['text'] = ""
    wos_api_type = validate_api_key()
    if wos_api_type is None:
        app.apikey_bottom_label['text'] = "Wrong API Key"
        app.search_button.config(state='active', text='Run')
        return False
    if validate_search() is False:
        app.progress_label['text'] = 'Please check your search query'
        app.search_button.config(state='active', text='Run')
        return False
    if wos_api_type == 'lite':
        if app.progress_label['text'] == 'Please check your search query':
            app.progress_label['text'] = ''
        user_apikey = app.apikey_window.get()
        search_query = app.search_query_window.get()
        wos_data = []

        # Sending an initial WoS API request to assess the number of requests required
        initial_wos_response = requests.get(
            f'https://api.clarivate.com/api/woslite?databaseId=WOS&usrQuery=TS="{urllib.parse.quote(search_query)}"'
            f'&count=0&firstRecord=1', headers={'X-APIKey': user_apikey})
        data = initial_wos_response.json()
        wos_requests_required = (((data['QueryResult']['RecordsFound'] - 1) // 100) + 1)
        if ' ' in search_query:
            derwent_search_query = ' ADJ '.join(search_query.split(' '))
            derwent_requests_required = initial_derwent_request(derwent_search_query)
        else:
            derwent_requests_required = initial_derwent_request(search_query)
        # From the first response, extracting the total number of records found and calculating the number of requests
        # required. The program can take up to a few dozen minutes, depending on the number of records being analyzed
        for i in range(wos_requests_required):
            lite_api_request(i, search_query, wos_data)
            print(f"{(((i + 1) * 100) / wos_requests_required):.1f}% of WoS API requests complete")
            progress = ((i + 1) / (wos_requests_required + derwent_requests_required)) * 100
            app.progress_bar.config(value=progress)
            app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    elif wos_api_type == 'expanded':
        if app.progress_label['text'] == 'Please check your search query':
            app.progress_label['text'] = ''
        user_apikey = app.apikey_window.get()
        search_query = app.search_query_window.get()
        wos_data = []

        # Sending an initial WoS API request to assess the number of requests required
        initial_wos_response = requests.get(
            f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery=TS="{urllib.parse.quote(search_query)}"'
            f'&count=0&firstRecord=1', headers={'X-APIKey': user_apikey})
        data = initial_wos_response.json()
        wos_requests_required = (((data['QueryResult']['RecordsFound'] - 1) // 100) + 1)
        if ' ' in search_query:
            derwent_search_query = ' ADJ '.join(search_query.split(' '))
            derwent_requests_required = initial_derwent_request(derwent_search_query)
        else:
            derwent_requests_required = initial_derwent_request(search_query)
        # From the first response, extracting the total number of records found and calculating the number of requests
        # required. The program can take up to a few dozen minutes, depending on the number of records being analyzed
        for i in range(wos_requests_required):
            expanded_api_request(i, search_query, wos_data)
            print(f"{(((i + 1) * 100) / wos_requests_required):.1f}% of WoS API requests complete")
            progress = ((i + 1) / (wos_requests_required + derwent_requests_required)) * 100
            app.progress_bar.config(value=progress)
            app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')

    else:
        if app.progress_label['text'] == 'Please check your search query':
            app.progress_label['text'] = ''
        user_apikey = app.apikey_window.get()
        search_query = app.search_query_window.get()
        wos_data = []

        # Sending an initial WoS API request to assess the number of requests required
        initial_wos_response = requests.get(
            f'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q=TS="{urllib.parse.quote(search_query)}"'
            f'&limit=50&page=1', headers={'X-APIKey': user_apikey})
        data = initial_wos_response.json()
        wos_requests_required = (((data['metadata']['total'] - 1) // 50) + 1)
        if ' ' in search_query:
            derwent_search_query = ' ADJ '.join(search_query.split(' '))
            derwent_requests_required = initial_derwent_request(derwent_search_query)
        else:
            derwent_requests_required = initial_derwent_request(search_query)
        # From the first response, extracting the total number of records found and calculating the number of requests
        # required. The program can take up to a few dozen minutes, depending on the number of records being analyzed
        for i in range(wos_requests_required + 1):
            starter_api_request(i, search_query, wos_data)
            print(f"{(((i + 1) * 100) / wos_requests_required):.1f}% of WoS API requests complete")
            progress = ((i + 1) / (wos_requests_required + derwent_requests_required)) * 100
            app.progress_bar.config(value=progress)
            app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')

    if ' ' in search_query:
        derwent_search_query = ' ADJ '.join(search_query.split(' '))
    else:
        derwent_search_query = search_query

    di_data = []

    for i in range(derwent_requests_required):
        derwent_api_request(i, derwent_search_query, di_data)
        print(f"{(((i + 1) * 100) / derwent_requests_required):.1f}% of Derwent API requests complete")
        progress = ((wos_requests_required + i + 1) / (wos_requests_required + derwent_requests_required)) * 100
        app.progress_bar.config(value=progress)
        app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')

    years = process_data(wos_data, di_data, wos_api_type)
    output(search_query, years)

    app.search_button.config(state='active', text='Run')
    complete_message = f"Calculation complete. Please check the {search_query} - {date.today()}.xlsx file " \
                       f"for results"
    app.progress_label['text'] = format_label_text(complete_message, 94)


# Defining a class through threading so that the interface doesn't freeze when the data is being retrieved through API
class App(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.root = None
        self.style = None
        self.tabs = None
        self.tab1 = None
        self.tab2 = None
        self.api_frame = None
        self.apikey_top_label = None
        self.apikey_window = None
        self.unhide_image = None
        self.apikey_unhide_button = None
        self.apikey_validate_button = None
        self.apikey_bottom_label = None
        self.username_top_label = None
        self.username_window = None
        self.username_unhide_image = None
        self.username_unhide_button = None
        self.password_top_label = None
        self.password_window = None
        self.password_unhide_image = None
        self.password_unhide_button = None
        self.password_validate_button = None
        self.password_bottom_label = None
        self.search_query_label = None
        self.search_query_window = None
        self.search_validate_button = None
        self.search_query_bottom_label = None
        self.search_button = None
        self.progress_bar = None
        self.progress_label = None
        self.offline_frame = None
        self.offline_label = None
        self.filename_label = None
        self.file_name = None
        self.filename_entry = None
        self.browse_image = None
        self.open_file_button = None
        self.draw_graph_button = None
        self.start()

    def run(self):
        self.root = tk.Tk()
        self.root.iconbitmap('./assets/clarivate.ico')
        self.root.title("Research and Innovation trends comparison")
        self.root.geometry("540x470")
        self.root.resizable(False, False)
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        # Modifying certain style elements
        self.style.configure('TNotebook', background='#F0F0EB')
        self.style.configure('TNotebook.Tab', font=('Calibri bold', 12))
        self.style.map('TNotebook.Tab',
                       foreground=[('active', '#5E33BF'), ('!active', '#000000')],
                       background=[('selected', '#FFFFFF'), ('!selected', '#F0F0EB')],
                       focuscolor=[('selected', '#FFFFFF')])
        self.style.configure('Bold.TLabel', font=('Calibri bold', 12), borderwidth=0, bordercolor='#000000',
                             selectborderwidth=0)
        self.style.configure('White.TFrame', background='#FFFFFF')
        self.style.map('Bold.TLabel',
                       foreground=[('focus', '#000000'), ('!focus', '#000000')],
                       background=[('focus', '#FFFFFF'), ('!focus', '#FFFFFF')])
        self.style.configure('Regular.TLabel', font=('Calibri', 10), borderwidth=0, bordercolor='#000000',
                             selectborderwidth=0)
        self.style.map('Regular.TLabel',
                       foreground=[('focus', '#000000'), ('!focus', '#000000')],
                       background=[('focus', '#FFFFFF'), ('!focus', '#FFFFFF')])
        self.style.configure('TEntry', font=('Calibri bold', 12), borderwidth=0,
                             selectborderwidth=0, )
        self.style.map('TEntry',
                       bordercolor=[('focus', '#5E33BF'), ('!focus', '#000000')],
                       selectforeground=[('focus', '#FFFFFF'), ('!focus', '#FFFFFF')],
                       selectbackground=[('focus', '#5693F5'), ('!focus', '#5693F5')])
        self.style.configure('Small.TButton', font=('Calibri bold', 11), borderwidth=1,
                             padding=0, focuscolor='#F0F0EB')
        self.style.map('Small.TButton',
                       foreground=[('active', '#5E33BF'), ('!active', '#5E33BF')],
                       background=[('active', '#F0F0EB'), ('!active', '#FFFFFF')],
                       bordercolor=[('active', '#5E33BF'), ('!active', '#5E33BF')])
        self.style.configure('Large.TButton', font=('Calibri bold', 12), borderwidth=0)
        self.style.map('Large.TButton',
                       foreground=[('disabled', '#9D9D9C'), ('!disabled', '#FFFFFF')],
                       background=[('disabled', '#DADADA'), ('!disabled', '#5E33BF')],
                       focuscolor=[('disabled', '#DADADA'), ('!disabled', '#5E33BF')]
                       )
        # We had to borrow the horizontal progressbar from the Default scheme in order to remove one extra frame
        # around the progress bar
        self.style.element_create('color.pbar', 'from', 'default')
        self.style.layout(
            'Clarivate.Horizontal.TProgressbar',
            [
                (
                    'Horizontal.Progressbar.trough',
                    {
                        'sticky': 'nswe',
                        'children':
                            [
                                (
                                    'Horizontal.Progressbar.color.pbar',
                                    {
                                        'side': 'left',
                                        'sticky': 'ns'
                                    }
                                )
                            ],
                    }
                ),
                (
                    'Horizontal.Progressbar.label', {'sticky': 'nswe'}
                )
            ]
        )
        self.style.configure('Clarivate.Horizontal.TProgressbar', font=('Calibri bold', 12), borderwidth=0,
                             troughcolor='#F0F0EB', background='#16AB03', foreground='#000000', text='',
                             anchor='center')

        self.tabs = ttk.Notebook(self.root)
        self.tab1 = ttk.Frame(self.tabs, style='White.TFrame')
        self.tab2 = ttk.Frame(self.tabs, style='White.TFrame')

        self.api_frame = ttk.Frame(self.tab1, style='White.TFrame')
        apikey = StringVar()
        username = StringVar()
        password = StringVar()
        self.apikey_top_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                          text="Web of Science API Key:")
        self.apikey_window = ttk.Entry(self.api_frame, font=('Calibri', 11), show="*", textvariable=apikey,
                                       validate="focusout")
        self.unhide_image = tk.PhotoImage(file='./assets/XC_icon_eye_01.png')
        self.apikey_unhide_button = ttk.Button(self.api_frame,
                                               text="Show symbols",
                                               style='Small.TButton',
                                               image=self.unhide_image,
                                               command=self.unhide_symbols_apikey)
        self.apikey_validate_button = ttk.Button(self.api_frame, text="Validate", style='Small.TButton',
                                                 command=self.check_api_key)
        self.apikey_bottom_label = ttk.Label(self.api_frame, text="", style='Regular.TLabel')
        self.username_top_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                            text="Derwent API Username:")
        self.username_window = ttk.Entry(self.api_frame, font=('Calibri', 11), show="*", textvariable=username,
                                         validate="focusout")
        self.username_unhide_image = tk.PhotoImage(file='./assets/XC_icon_eye_01.png')
        self.username_unhide_button = ttk.Button(self.api_frame,
                                                 text="Show symbols",
                                                 style='Small.TButton',
                                                 image=self.unhide_image,
                                                 command=self.unhide_symbols_username)
        self.password_top_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                            text="Derwent API Password:")
        self.password_window = ttk.Entry(self.api_frame, font=('Calibri', 11), show="*", textvariable=password,
                                         validate="focusout")
        self.password_unhide_image = tk.PhotoImage(file='./assets/XC_icon_eye_01.png')
        self.password_unhide_button = ttk.Button(self.api_frame,
                                                 text="Show symbols",
                                                 style='Small.TButton',
                                                 image=self.unhide_image,
                                                 command=self.unhide_symbols_password)
        self.password_validate_button = ttk.Button(self.api_frame, text="Validate", style='Small.TButton',
                                                   command=self.check_api_unp)
        self.password_bottom_label = ttk.Label(self.api_frame, text="", style='Regular.TLabel')
        self.search_query_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                            text="Topical Search:")
        self.search_query_window = ttk.Entry(self.api_frame, font=('Calibri', 11))
        self.search_query_window.insert(0, 'microplastic*')
        self.search_validate_button = ttk.Button(self.api_frame, text="Validate", style='Small.TButton',
                                                 command=self.check_search_query)
        self.search_query_bottom_label = ttk.Label(self.api_frame, text='', style='Regular.TLabel')
        self.search_button = ttk.Button(self.api_frame,
                                        text='Run',
                                        style='Large.TButton',
                                        command=self.run_button)
        self.progress_bar = ttk.Progressbar(self.api_frame, style='Clarivate.Horizontal.TProgressbar',
                                            mode="determinate")
        self.progress_label = ttk.Label(self.api_frame, style='Regular.TLabel')
        self.offline_frame = ttk.Frame(self.tab2, style='White.TFrame')
        self.offline_label = ttk.Label(self.offline_frame,
                                       style='Regular.TLabel',
                                       text='Here you can simply load a previously saved Excel file and draw a trend '
                                            'graph from it.\n')
        self.filename_label = ttk.Label(self.offline_frame, style='Bold.TLabel', text='Select file:')
        self.file_name = StringVar()
        self.filename_entry = ttk.Entry(self.offline_frame, textvariable=self.file_name)
        self.browse_image = tk.PhotoImage(file='./assets/XC_icon_folder_05.png')
        self.open_file_button = ttk.Button(self.offline_frame,
                                           text='Open File',
                                           style='Small.TButton',
                                           image=self.browse_image,
                                           command=self.file_menu,
                                           default='normal')
        self.draw_graph_button = ttk.Button(self.offline_frame,
                                            text='Draw Graph',
                                            style='Large.TButton',
                                            command=self.draw_graph)

        self.tabs.place(x=0, y=0, width=540, height=470)
        self.tab1.place(x=0, y=0, width=0, height=0)
        self.tab2.place(x=0, y=0, width=0, height=0)
        self.tabs.add(self.tab1, text='            RETRIEVE THROUGH APIS             ')
        self.tabs.add(self.tab2, text='               LOAD EXCEL FILE                ')
        self.api_frame.place(x=0, y=0, width=540, height=480)
        self.apikey_top_label.place(x=5, y=5, width=535, height=24)
        self.apikey_window.place(x=5, y=29, width=400, height=30)
        self.apikey_unhide_button.place(x=406, y=29, width=30, height=30)
        self.apikey_validate_button.place(x=440, y=29, width=90, height=30)
        self.apikey_bottom_label.place(x=5, y=59, width=500, height=24)
        self.username_top_label.place(x=5, y=83, width=535, height=24)
        self.username_window.place(x=5, y=107, width=400, height=30)
        self.username_unhide_button.place(x=406, y=107, width=30, height=30)
        self.password_top_label.place(x=5, y=142, width=535, height=24)
        self.password_window.place(x=5, y=166, width=400, height=30)
        self.password_unhide_button.place(x=406, y=166, width=30, height=30)
        self.password_validate_button.place(x=440, y=166, width=90, height=30)
        self.password_bottom_label.place(x=5, y=196, width=400, height=24)
        self.search_query_label.place(x=5, y=220, width=400, height=24)
        self.search_query_window.place(x=5, y=244, width=400, height=30)
        self.search_validate_button.place(x=410, y=244, width=120, height=30)
        self.search_query_bottom_label.place(x=5, y=274, width=500, height=40)
        self.search_button.place(x=220, y=320, width=100, height=35)
        self.progress_bar.place(x=5, y=370, width=525, height=30)
        self.progress_label.place(x=5, y=400, width=525, height=40)
        self.offline_frame.place(x=0, y=0, width=540, height=430)
        self.offline_label.place(x=5, y=0, width=535, height=50)
        self.filename_label.place(x=5, y=65, width=535, height=24)
        self.filename_entry.place(x=5, y=89, width=495, height=30)
        self.open_file_button.place(x=502, y=89, width=30, height=30)
        self.draw_graph_button.place(x=220, y=150, width=100, height=35)

        self.root.mainloop()

    def unhide_symbols_apikey(self):
        if self.apikey_window['show'] == "*":
            self.apikey_window['show'] = ""
        else:
            self.apikey_window['show'] = "*"

    def unhide_symbols_username(self):
        if self.username_window['show'] == "*":
            self.username_window['show'] = ""
        else:
            self.username_window['show'] = "*"

    def unhide_symbols_password(self):
        if self.password_window['show'] == "*":
            self.password_window['show'] = ""
        else:
            self.password_window['show'] = "*"

    def check_api_key(self):
        threading.Thread(target=validate_api_key).start()

    def check_api_unp(self):
        threading.Thread(target=validate_api_unp).start()

    def check_search_query(self):
        threading.Thread(target=validate_search).start()

    def run_button(self):
        threading.Thread(target=main_function).start()

    def file_menu(self):
        self.file_name.set(askopenfilename(initialdir='./', filetypes=[("Excel files", "*.xlsx")]))

    def draw_graph(self):
        threading.Thread(target=offline_plotting).start()


app = App()


def output(search_query, years):
    # Sorting the values by year, largest to smallest, to save them into a .csv file
    years.sort(reverse=True, key=lambda years: years['year'])

    # Converting our list of dictionaries into a dataframe
    df = pd.DataFrame(data=years)
    column_names = {'year': 'Year',
                    'wos_documents': 'Web of Science Documents',
                    'di_pry': 'Derwent Innovation - Patent Families (Earliest Priority Year)',
                    'di_py': 'Derwent Innovation - Patent Families (Publication Year)'}
    df.rename(columns=column_names, inplace=True)
    search_parameters = pd.DataFrame(data={'Search Query': [search_query],
                                           'Search Date': [date.today()]})
    # The results are saved to an Excel file
    safe_search_query = search_query.replace('?', '').replace('*', '')
    filename = f'trends - {safe_search_query} - by families - {date.today()}'
    if len(filename) > 218:
        safe_filename = filename[:218]
    else:
        safe_filename = filename
    with pd.ExcelWriter(f'{safe_filename}.xlsx') as writer:
        df.to_excel(writer, sheet_name='Annual Dynamics', index=False)
        search_parameters.to_excel(writer, sheet_name='Search Parameters', index=False)

    # Setting up the plot
    fig = px.bar(data_frame=df,
                 x='Year',
                 y=['Web of Science Documents',
                    'Derwent Innovation - Patent Families (Earliest Priority Year)',
                    'Derwent Innovation - Patent Families (Publication Year)'],
                 barmode='group',
                 color_discrete_sequence=['#5E33BF', '#16AB03', '#000000'],
                 title=f'Topical Search: {search_query}')

    # Making cosmetic edits to the plot
    fig.update_layout({'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
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


def offline_plotting():
    # Loading the excel file into a dataframe
    df = pd.read_excel(app.filename_entry.get(), sheet_name='Annual Dynamics')
    search_parameters = pd.read_excel(app.filename_entry.get(), sheet_name='Search Parameters')

    # Setting up the plot
    fig = px.bar(data_frame=df,
                 x='Year',
                 y=['Web of Science Documents',
                    'Derwent Innovation - Patent Families (Earliest Priority Year)',
                    'Derwent Innovation - Patent Families (Publication Year)'],
                 barmode='group',
                 color_discrete_sequence=['#5E33BF', '#16AB03', '#000000'],
                 title=f'Topical Search: {search_parameters["Search Query"][0]}')

    # Making cosmetic edits to the plot
    fig.update_layout({'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
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
