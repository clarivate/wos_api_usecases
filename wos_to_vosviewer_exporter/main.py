"""
This code is created to simplify the data export from Web of Science and to prepare the files acceptable by VOSviewer.
All you need to do is enter your Web of Science API key (Expanded is better, but Starter would also work), enter the
Web of Science Advanced Search query, and click "Run". You can also choose to retrieve the cited references data, but
it currently takes much longer through the API.
"""

import urllib.parse
import time
import threading
import tkinter as tk
from tkinter import ttk, BooleanVar
from datetime import date
import pandas as pd
import requests


# If the user provided the Starter API key, this is the way to fetch the necessary metadata from the records
def fetch_expanded_metadata(record, records):
    ut = record['UID']
    py = record['static_data']['summary']['pub_info']['pubyear']
    try:
        names = []
        for name in record['static_data']['summary']['names']['name']:
            names.append(name['full_name'])
        authors = '; '.join(names)
    except TypeError:
        authors = record['static_data']['summary']['names']['name']['full_name']
    c1 = ''
    # When there are multiple address fields on the record
    if record['static_data']['fullrecord_metadata']['addresses']['count'] > 1:
        c1_1 = []
        for address_subfield in record['static_data']['fullrecord_metadata']['addresses']['address_name']:
            names_c1 = []
            address = address_subfield['address_spec']['full_address']
            try:
                if address_subfield['names']['count'] > 1:
                    for name in address_subfield['names']['name']:
                        try:
                            names_c1.append(name['full_name'])
                        except KeyError:
                            pass
                    c1_1.append(f"[{'; '.join(names_c1)}] {address}")
                else:
                    names_c1 = address_subfield['names']['name']['full_name']
                    c1_1.append(f"[{names_c1}] {address}")
            except KeyError:
                address = address_subfield['address_spec']['full_address']
                c1_1.append(address)
        c1 = '; '.join(c1_1)
    # When there are no address fields on the record
    elif record['static_data']['fullrecord_metadata']['addresses']['count'] == 0:
        pass
    # When there is only one address field on the record
    else:

        names_c1 = []
        address = record['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec'][
            'full_address']
        try:
            if record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']['count'] > 1:
                for name in record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']['name']:
                    names_c1.append(name['full_name'])
                c1 = f"[{'; '.join(names_c1)}] {address}"
            else:
                name_c1 = record['static_data']['fullrecord_metadata']['addresses']['address_name']['names']['name'][
                    'full_name']
                c1 += f"[{name_c1}] {address}"
        except KeyError:
            pass
    for title in record['static_data']['summary']['titles']['title']:
        if title['type'] == 'source':
            source_title = title['content']
            break
    else:
        source_title = ''
    for title in record['static_data']['summary']['titles']['title']:
        if title['type'] == 'item':
            doc_title = title['content']
            break
    else:
        doc_title = ''
    try:
        keywords = '; '.join(record['static_data']['fullrecord_metadata']['keywords']['keyword'])
    except KeyError:
        keywords = ''
        """You can add the following lines for debugging:
        print(f'no keywords for record {ut}')
        print(record['static_data']['fullrecord_metadata'])"""
    except TypeError:
        keywords = ['']
        """You can add the following lines for debugging:
        print(f"something weird in record {ut}: {record['static_data']['fullrecord_metadata']['keywords']}")"""
    try:
        if record['static_data']['item']['keywords_plus']['count'] == 1:
            keywords_plus = record['static_data']['item']['keywords_plus']['keyword']
        else:
            keywords_plus = '; '.join(record['static_data']['item']['keywords_plus']['keyword'])
    except KeyError:
        keywords_plus = ''
        """You can add the following lines for debugging:
        print(f'no keywords plus for record {ut}')
        print(record['static_data']['item'])"""
    try:
        abstract = record['static_data']['fullrecord_metadata']['abstracts']['abstract']['abstract_text']['p']
    except KeyError:
        abstract = ''
        """You can add the following lines for debugging:
        print(f'no abstract metadata found for record {ut}')"""
    tc = record['dynamic_data']['citation_related']['tc_list']['silo_tc']['local_count']
    records.append({
        'UT': ut,
        'PY': py,
        'AU': authors,
        'SO': source_title,
        'C1': c1,
        'TI': doc_title,
        'DE': keywords,
        'ID': keywords_plus,
        'AB': abstract,
        'TC': tc
    })


# If the user provided the Expanded API key, this is the way to retrieve the data
def expanded_api_request(i, search_query, requests_required, records):
    user_apikey = app.apikey_window.get()
    request = requests.get(f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery='
                           f'{urllib.parse.quote(search_query)}&count=100&firstRecord={i}01',
                           headers={'X-APIKey': user_apikey})
    data = request.json()
    try:
        for wos_record in data['Data']['Records']['records']['REC']:
            fetch_expanded_metadata(wos_record, records)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i + 1}')
        time.sleep(1)
        expanded_api_request(i, search_query, requests_required, records)
    print(f"{((i + 1) * 100) / requests_required:.1f}% documents retrieved")
    if app.retrieve_cited_references.get():
        progress = ((i + 1) / requests_required)
    else:
        progress = ((i + 1) / requests_required) * 100
    app.progress_bar.config(value=progress)
    app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    app.root.update_idletasks()


# If the user provided the Starter API key, this is the way to fetch the necessary metadata from the records
def fetch_starter_metadata(record, records):
    ut = record['uid']
    py = record['source']['publishYear']
    try:
        names = []
        for name in record['names']['authors']:
            names.append(name['wosStandard'])
        authors = '; '.join(names)
    except TypeError:
        authors = ''
        """You can add the following lines for debugging:
        print(f'something weird with the author names in record: {ut}')"""
    source_title = record['source']['sourceTitle']
    doc_title = record['title']
    try:
        keywords = '; '.join(record['keywords']['authorKeywords'])
    except KeyError:
        keywords = ''
        """You can add the following lines for debugging:
        print(f'no keywords for record {ut}')
        print(record['static_data']['fullrecord_metadata'])"""
    except TypeError:
        keywords = ['']
        """You can add the following lines for debugging:
        print(f"something weird in record {ut}: {record['static_data']['fullrecord_metadata']['keywords']}")"""
    try:
        for db in record['citations']:
            if db['db'] == 'wos':
                tc = db['count']
                break
        else:
            tc = 0
    except KeyError:
        tc = 0
    records.append({
        'UT': ut,
        'PY': py,
        'AU': authors,
        'SO': source_title,
        'TI': doc_title,
        'DE': keywords,
        'TC': tc
    })


# If the user provided the Starter API key, this is the way to retrieve the data
def starter_api_request(i, search_query, requests_required, records):
    user_apikey = app.apikey_window.get()
    request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q='
                           f'{urllib.parse.quote(search_query)}&limit=50&page={i+1}', headers={'X-APIKey': user_apikey})
    data = request.json()
    try:
        for wos_record in data['hits']:
            fetch_starter_metadata(wos_record, records)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i + 1}')
        time.sleep(1)
        expanded_api_request(i, search_query, requests_required, records)
    print(f"{((i + 1) * 100) / requests_required:.1f}% complete")
    if app.retrieve_cited_references.get():
        progress = ((i + 1) / requests_required)
    else:
        progress = ((i + 1) / requests_required) * 100
    app.progress_bar.config(value=progress)
    app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    app.root.update_idletasks()


def fetch_cited_metadata(crs, cited_data):
    for cited_record in cited_data['Data']:
        cr = ''
        try:
            cr += f"{cited_record['CitedAuthor']}"
        except KeyError:
            pass
        try:
            cr += f", {cited_record['Year']}"
        except KeyError:
            pass
        try:
            cr += f", {cited_record['CitedWork']}"
        except KeyError:
            pass
        try:
            cr += f", V{cited_record['Volume']}"
        except KeyError:
            pass
        try:
            cr += f", P{cited_record['Page']}"
        except KeyError:
            pass
        try:
            cr += f", DOI {cited_record['DOI']}"
        except KeyError:
            pass
        crs.append(cr)


# Querying the cited endpoint if the "Also retrieve Cited References" checkbox is ticked
def cited_endpoint_request(record, records, i, user_apikey):
    crs = []
    initial_cited_request = requests.get(f'https://api.clarivate.com/api/wos/references?databaseId=WOS&uniqueId='
                                         f'{record["UT"]}&count=100&firstRecord=1',
                                         headers={'X-APIKey': user_apikey})
    try:
        cited_data = initial_cited_request.json()
        fetch_cited_metadata(crs, cited_data)
        if cited_data['QueryResult']['RecordsFound'] > 100:
            cited_requests_required = ((cited_data['QueryResult']['RecordsFound'] - 1) // 100) + 1
            for j in range(1, cited_requests_required):
                cited_request = requests.get(f'https://api.clarivate.com/api/wos/references?databaseId=WOS&'
                                             f'uniqueId={record["UT"]}&count=100&firstRecord={j}01',
                                             headers={'X-APIKey': user_apikey})
                cited_data = cited_request.json()
                fetch_cited_metadata(crs, cited_data)
        record['CR'] = '; '.join(crs)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i + 1}')
        time.sleep(1)
        cited_endpoint_request(record, records, i, user_apikey)
    progress = ((len(records)/100 + i + 1) / (len(records) * 1.01)) * 100
    app.progress_bar.config(value=progress)
    app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    app.root.update_idletasks()


# Saving the data into a .csv file
def output(search_query, records):
    df = pd.DataFrame(records)
    filename = f'{search_query} - {date.today()}'
    safe_filename = filename.replace('?', '').replace('*', '').replace('"', '')
    if app.retrieve_cited_references.get():
        df.to_csv(f'{safe_filename} - with cited references.txt', index=False, sep='\t')
    else:
        df.to_csv(f'{safe_filename}.txt', index=False, sep='\t')


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


# A function for hiding/unhiding symbols in the API Key field
def unhide_symbols():
    if app.apikey_window['show'] == "*":
        app.apikey_window['show'] = ""
    else:
        app.apikey_window['show'] = "*"


# A function for checking the validity of the API key
def validate_api_key():
    user_apikey = app.apikey_window.get()
    # Sending an Expanded test request to check if it passes authentication
    validation_request = requests.get(
        'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery=AU=Garfield&count=0&firstRecord=1',
        headers={'X-APIKey': user_apikey}
    )
    if validation_request.status_code == 200:
        # If the API call with this key is a success, we're also return the amount of records remaining
        docs_left = validation_request.headers['X-REC-AmtPerYear-Remaining']
        app.apikey_bottom_label['text'] = f"Expanded API Authentication succeeded; Records left to retrieve: " \
                                          f"{docs_left}"
        app.cited_references_checkbutton.config(state='active')
        return 'expanded'
    # If the Expanded API request status is anything but 200, sending a Starter API test request
    validation_request_starter = requests.get(
        'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q=AU=Garfield&limit=1&page=1',
        headers={'X-APIKey': user_apikey}
    )
    if validation_request_starter.status_code == 200:
        requests_left_today = validation_request_starter.headers['X-RateLimit-Remaining-Day']
        if int(requests_left_today) < 100:
            label_text = f'Starter API authentication succeeded; Requests left today: {requests_left_today}'

        else:
            label_text = 'Starter API authentication succeeded. Address, Abstract, Keywords Plus, and Cited ' \
                         'references metadata is only available with Expanded API'
        app.apikey_bottom_label['text'] = format_label_text(label_text, 94)
        if app.retrieve_cited_references.get():
            app.cited_references_checkbutton.invoke()
        app.cited_references_checkbutton.config(state='disabled')
        return 'starter'
    app.apikey_bottom_label['text'] = "Wrong API Key"
    return None


# A function to make sure the affiliation name provided by the user is a valid one
def validate_search_query():
    app.search_query_bottom_label['text'] = 'Validating...\n\n'
    wos_api_type = validate_api_key()
    if wos_api_type is None:
        app.apikey_bottom_label['text'] = "Wrong API Key"
        return False
    user_apikey = app.apikey_window.get()
    search_query = app.search_query_window.get("1.0", "end-1c")
    if wos_api_type == 'expanded':
        validation_request = requests.get(
            f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&'
            f'count=0&firstRecord=1', headers={'X-APIKey': user_apikey})
        validation_data = validation_request.json()
        if validation_request.status_code == 200:
            records_amount = validation_data['QueryResult']['RecordsFound']
            app.search_query_bottom_label['text'] = f'Records found: {records_amount} \n\n'
            if records_amount == 0:
                return False
            if records_amount > 100000:
                text = f'Records found: {records_amount}. You can export a maximum of 100k records through Expanded ' \
                       f'API\n'
                app.search_query_bottom_label['text'] = format_label_text(text, 94)
                return True
            return True
        error_message = validation_data['message']
        if error_message == 'Invalid authentication credentials':
            app.apikey_bottom_label['text'] = "Wrong API Key"
        else:
            error_message_text = error_message[error_message.find(": ") + 2:]
            app.search_query_bottom_label['text'] = (f'Request failed with status code '
                                                     f'{validation_request.status_code}\n'
                                                     f'{format_label_text(error_message_text, 94)}')
        return False
    if wos_api_type == 'starter':
        validation_request = requests.get(
            f'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q={urllib.parse.quote(search_query)}&'
            f'limit=1&page=1', headers={'X-APIKey': user_apikey})
        validation_data = validation_request.json()
        if validation_request.status_code == 200:
            records_amount = validation_data['metadata']['total']
            wos_api_limit = (int(validation_request.headers['X-RateLimit-Remaining-Day']) - 1) * 50
            if records_amount == 0:
                return False
            if records_amount > wos_api_limit:
                label_text = f'Web of Science records found: {records_amount}. You have a maximum of {wos_api_limit} ' \
                             f'records remaining to export today using {wos_api_type}'
                app.search_query_bottom_label['text'] = format_label_text(label_text, 94)
                return True
            app.search_query_bottom_label['text'] = f'Web of Science records found: {records_amount}\n\n'
            return True
        try:
            error_message_text = validation_data["error"]["details"]
            app.search_query_bottom_label['text'] = (f'Request failed with status code '
                                                     f'{validation_request.status_code}: '
                                                     f'{validation_data["error"]["title"]}. \n'
                                                     f'{format_label_text(error_message_text, 94)}')
        except KeyError:
            try:
                if validation_data['message'] == 'Invalid authentication credentials':
                    app.apikey_bottom_label['text'] = "Wrong API Key"
            except KeyError:
                return False
        return False
    return False


# This function is launched when the "Run" button is clicked
def main_function():
    app.search_button.config(state='disabled', text='Retrieving...')
    app.progress_label['text'] = ''
    wos_api_type = validate_api_key()
    search_query = app.search_query_window.get("1.0", "end-1c")
    records = []
    if validate_search_query() is False:
        app.progress_label['text'] = 'Please check your search query'
        app.search_button.config(state='active', text='Run')
        return False
    if app.progress_label['text'] == 'Please check your search query':
        app.progress_label['text'] = ''
    if wos_api_type == 'expanded':
        # This is the initial Expanded API request
        initial_request = requests.get(
            f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&count=0&'
            f'firstRecord=1', headers={'X-APIKey': app.apikey_window.get()}
        )
        data = initial_request.json()
        requests_required = ((data['QueryResult']['RecordsFound'] - 1) // 100) + 1
        for i in range(requests_required):
            expanded_api_request(i, search_query, requests_required, records)
        if app.retrieve_cited_references.get():
            for record in records:
                user_apikey = app.apikey_window.get()
                cited_endpoint_request(record, records, records.index(record), user_apikey)
                print(f"{((records.index(record) + 1) * 100) / len(records):.1f}% cited references requests complete")
    elif wos_api_type == 'starter':
        # This is the initial Starter API request
        initial_request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q='
                                       f'{urllib.parse.quote(search_query)}&limit=1&page=1',
                                       headers={'X-APIKey': app.apikey_window.get()})
        data = initial_request.json()
        requests_required = ((data['metadata']['total'] - 1) // 100) + 1
        for i in range(requests_required):
            starter_api_request(i, search_query, requests_required, records)
    output(search_query, records)
    app.search_button.config(state='active', text='Run')
    if app.retrieve_cited_references.get():
        complete_message = f"Retrieval complete. Please check the {search_query} - {date.today()} - with cited " \
                           f"references.txt file for results"
    else:
        complete_message = f"Retrieval complete. Please check the {search_query} - {date.today()}.txt file for" \
                           f" results"
    app.progress_label['text'] = format_label_text(complete_message, 94)


# Defining a class through threading so that the interface doesn't freeze when the data is being retrieved through API
class App(threading.Thread):

    def __init__(self,):
        threading.Thread.__init__(self)
        self.root = None
        self.style = None
        self.api_frame = None
        self.apikey_top_label = None
        self.apikey_window = None
        self.unhide_image = None
        self.apikey_unhide_button = None
        self.apikey_button = None
        self.apikey_bottom_label = None
        self.search_query_label = None
        self.search_query_window = None
        self.search_validate_button = None
        self.retrieve_cited_references = None
        self.cited_references_checkbutton = None
        self.search_query_bottom_label = None
        self.search_button = None
        self.progress_bar = None
        self.progress_label = None
        self.start()

    def run(self):
        self.root = tk.Tk()

        # Setting up style and geometry
        self.root.iconbitmap('./assets/clarivate.ico')
        self.root.title("Web of Science API to VOSviewer extractor")
        self.root.geometry("540x440")
        self.root.resizable(False, False)
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.style.configure('White.TFrame', background='#FFFFFF')
        self.style.configure('Bold.TLabel', font=('Calibri bold', 12), borderwidth=0, bordercolor='#000000',
                             selectborderwidth=0)
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
        # Setting up a Checkbutton to look 
        img_unselected = tk.PhotoImage(file='./assets/XC_icon_box_01.png')
        img_selected = tk.PhotoImage(file='./assets/XC_icon_tick_04.png')
        self.style.element_create('custom.indicator', 'image', img_unselected,
                             ('selected', '!disabled', img_selected))
        self.style.layout(
            'Clarivate.TCheckbutton',
            [('Checkbutton.padding',
              {'sticky': 'nswe',
               'children': [('custom.indicator', {'side': 'left', 'sticky': ''}),
                            ('Checkbutton.focus',
                             {'side': 'left',
                              'sticky': '',
                              'children': [('Checkbutton.label', {'sticky': 'nswe'})]})]})])

        self.style.configure('Clarivate.TCheckbutton', font=('Calibri', 11), indicatorsize=16)
        self.style.map('Clarivate.TCheckbutton',
                       foreground=[('disabled', '#DADADA'), ('!disabled', '#000000')],
                       background=[('disabled', '#FFFFFF'), ('!disabled', '#FFFFFF')],
                       focuscolor=[('disabled', '#FFFFFF'), ('!disabled', '#FFFFFF')],
                       indicatorforeground=[('selected', '#5E33BF'), ('!selected', '#FFFFFF')],
                       indicatorbackground=[('selected', '#FFFFFF'), ('active', '#F0F0EB'), ('!selected', '#FFFFFF')],
                       upperbordercolor=[('selected', '#5E33BF'), ('!selected', '#646363'), ('disabled', '#DADADA')],
                       lowerbordercolor=[('selected', '#5E33BF'), ('!selected', '#646363'), ('disabled', '#DADADA')])
        # We had to borrow the horizontal progressbar from the Default scheme in order to remove one extra frame
        # around the progress bar
        self.style.element_create('color.pbar', 'from', 'default')
        self.style.layout(
            'Clarivate.Horizontal.TProgressbar',
            [('Horizontal.Progressbar.trough',
                    {'sticky': 'nswe',
                        'children':
                            [('Horizontal.Progressbar.color.pbar', {'side': 'left', 'sticky': 'ns'})]}
                ),
                ('Horizontal.Progressbar.label', {'sticky': 'nswe'})
            ]
        )
        self.style.configure('Clarivate.Horizontal.TProgressbar', font=('Calibri bold', 12), borderwidth=0,
                             troughcolor='#F0F0EB', background='#16AB03', foreground='#000000', text='',
                             anchor='center')

        # Setting up widgets
        self.api_frame = ttk.Frame(self.root, style='White.TFrame')
        self.apikey_top_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                          text="Web of Science API Key:")
        apikey = tk.StringVar()
        self.apikey_window = ttk.Entry(self.api_frame, font=('Calibri', 11), show="*", textvariable=apikey,
                                       validate="focusout")
        self.unhide_image = tk.PhotoImage(file='./assets/XC_icon_eye_01.png')
        self.apikey_unhide_button = ttk.Button(self.api_frame,
                                               text="Show symbols",
                                               style='Small.TButton',
                                               image=self.unhide_image,
                                               command=unhide_symbols)
        self.apikey_button = ttk.Button(self.api_frame, text="Validate", style='Small.TButton',
                                        command=self.check_api_key)
        self.apikey_bottom_label = ttk.Label(self.api_frame, text="", style='Regular.TLabel')
        self.search_query_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                            text="Web of Science Core Collection Advanced Search query:")
        self.search_query_window = tk.Text(self.api_frame, font=("Calibri", 12),
                                           borderwidth=1, relief='solid', wrap='word')
        self.search_query_window.insert('1.0', 'OG=Clarivate and PY=2008-2022')
        self.search_validate_button = ttk.Button(self.api_frame, text="Validate", style='Small.TButton',
                                                 command=self.check_search_query)
        self.retrieve_cited_references = BooleanVar()
        self.cited_references_checkbutton = ttk.Checkbutton(self.api_frame,
                                                            text='  Also retrieve Cited References (takes significantly'
                                                                 ' more time)',
                                                            variable=self.retrieve_cited_references,
                                                            onvalue=True,
                                                            offvalue=False,
                                                            style='Clarivate.TCheckbutton')
        self.search_query_bottom_label = ttk.Label(self.api_frame, text='', style='Regular.TLabel')
        self.search_button = ttk.Button(self.api_frame,
                                        text='Run',
                                        style='Large.TButton',
                                        command=self.run_button)
        self.progress_bar = ttk.Progressbar(self.api_frame, style='Clarivate.Horizontal.TProgressbar',
                                            mode="determinate")
        self.progress_label = ttk.Label(self.api_frame, style='Regular.TLabel')

        # Placing widgets
        self.api_frame.place(x=0, y=0, width=540, height=440)
        self.apikey_top_label.place(x=5, y=5, width=535, height=24)
        self.apikey_window.place(x=5, y=29, width=400, height=30)
        self.apikey_unhide_button.place(x=406, y=29, width=30, height=30)
        self.apikey_button.place(x=440, y=29, width=90, height=30)
        self.apikey_bottom_label.place(x=5, y=59, width=525, height=40)
        self.search_query_label.place(x=5, y=99, width=400, height=30)
        self.search_query_window.place(x=5, y=129, width=400, height=90)
        self.search_validate_button.place(x=410, y=129, width=120, height=30)
        self.cited_references_checkbutton.place(x=5, y=219, width=500, height=30)
        self.search_query_bottom_label.place(x=5, y=249, width=525, height=60)
        self.search_button.place(x=220, y=320, width=100, height=35)
        self.progress_bar.place(x=5, y=370, width=525, height=30)
        self.progress_label.place(x=5, y=400, width=525, height=40)

        self.root.mainloop()

    def check_api_key(self):
        threading.Thread(target=validate_api_key).start()

    def check_search_query(self):
        threading.Thread(target=validate_search_query).start()

    def run_button(self):
        threading.Thread(target=main_function).start()


app = App()
