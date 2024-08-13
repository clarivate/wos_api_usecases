"""
This code is created to simplify the data export from Web of Science and to prepare the files
acceptable by VOSviewer. All you need to do is enter your Web of Science API key (Expanded is
better, but Starter would also work), enter the Web of Science Advanced Search query, and click
"Run". You can also choose to retrieve the cited references data, but it currently takes much
longer through the API.
"""

import urllib.parse
import textwrap
import time
import threading
import tkinter as tk
from tkinter import ttk, BooleanVar
from datetime import date
import pandas as pd
import requests


def fetch_author_names(names_json):
    """Retrieve the names of the authors.

    :param names_json: dict.
    :return: str.
    """
    if isinstance(names_json['name'], dict):
        if names_json['name']['role'] == 'author':
            return names_json['name']['full_name']
        return ''
    return ', '.join([n['full_name'] for n in names_json['name'] if n['role'] == 'author'])


def fetch_author_affiliation_links(address_json):
    """Retrieve the author names, but for the 'C1' field that stores them in
    relation to specific affiliations.

    :param address_json: dict.
    :return: str.
    """
    address = address_json['address_spec']['full_address']
    if 'names' not in address_json.keys():
        return f'[] {address}'
    if isinstance(address_json['names']['name'], list):
        names_list = []
        for name in address_json['names']['name']:
            try:
                names_list.append(name['full_name'])
            except KeyError:
                # Uncomment the following string for debugging:if
                # print('Missing Author Full name in the record: {address_json}')
                pass
        return f"[{'; '.join(names_list)}] {address}"
    name = address_json['names']['name']['full_name']
    return f"[{name}] {address}"


def fetch_affiliations(address_json):
    """Retrieve the names of the authors-affiliations links.

    :param address_json: dict.
    :return: str.
    """

    # When there are no address fields on the record
    if address_json['count'] == 0:
        return ''

    # When there are multiple address fields on the record
    if isinstance(address_json['address_name'], list):
        au_affil_list = []
        for address_subfield in address_json['address_name']:
            au_affil_list.append(fetch_author_affiliation_links(address_subfield))
        return '; '.join(au_affil_list)

    # When there is only one address field on the record
    return fetch_author_affiliation_links(address_json['address_name'])


def fetch_titles(titles_json):
    """Retrieve the source title and document title.

    :param titles_json: dict.
    :return: str, str.
    """
    return ([t['content'] for t in titles_json if t['type'] == 'source'][0],
            [t['content'] for t in titles_json if t['type'] == 'item'][0])


def fetch_keywords(keywords_json):
    """Retrieve the author keywords and keywords plus

    :param keywords_json: dict.
    :return: str.
    """
    if isinstance(keywords_json['keyword'], str):
        return keywords_json['keyword']
    return '; '.join(str(e) for e in keywords_json['keyword'])


def fetch_abstract(fullrecord_metadata):
    """Retrieve the abstract of the document.

    :param fullrecord_metadata: dict.
    :return: str.
    """
    if 'abstracts' in fullrecord_metadata.keys():
        if 'p' in fullrecord_metadata['abstracts']['abstract']['abstract_text'].keys():
            return fullrecord_metadata['abstracts']['abstract']['abstract_text']['p']
        return ''
    return ''


def fetch_times_cited(tc_json):
    """Retrieve the times cited counts.

    :param tc_json: dict
    :return: str or int.
    """
    for database in tc_json:
        if database['coll_id'] == 'WOS':
            return database['local_count']
    return ''


def fetch_expanded_metadata(record):
    """Parse the metadata fields required for VOSviewer that are available via
    Web of Science Expanded API

    :param record: dict.
    :return: dict.
    """
    ut = record['UID']
    py = record['static_data']['summary']['pub_info']['pubyear']
    authors = fetch_author_names(record['static_data']['summary']['names'])
    c1 = fetch_affiliations(record['static_data']['fullrecord_metadata']['addresses'])
    source_title, doc_title = fetch_titles(record['static_data']['summary']['titles']['title'])
    if 'keywords' in record['static_data']['fullrecord_metadata'].keys():
        keywords = fetch_keywords(record['static_data']['fullrecord_metadata']['keywords'])
    else:
        keywords = ''
    if 'keywords_plus' in record['static_data']['item'].keys():
        keywords_plus = fetch_keywords(record['static_data']['item']['keywords_plus'])
    else:
        keywords_plus = ''
    abstract = fetch_abstract(record['static_data']['fullrecord_metadata'])
    tc = fetch_times_cited(record['dynamic_data']['citation_related']['tc_list']['silo_tc'])
    return {'UT': ut, 'PY': py, 'AU': authors, 'SO': source_title, 'C1': c1,
            'TI': doc_title, 'DE': keywords, 'ID': keywords_plus, 'AB': abstract, 'TC': tc}


# If the user provided the Expanded API key, this is the way to retrieve the data
def expanded_api_request(i, search_query, requests_required, records):
    """Send Web of Science Expanded API request to get records metadata.

    :param i: int.
    :param search_query: str.
    :param requests_required: int.
    :param records: list.
    :return: None.
    """
    user_apikey = app.apikey_window.get()
    request_json = {"databaseId": "WOS",
                    "usrQuery": f"{search_query}",
                    "count": 100,
                    "firstRecord": int(f'{i}01')}
    request = requests.post('https://wos-api.clarivate.com/api/wos',
                            json=request_json,
                            headers={'X-APIKey': user_apikey},
                            timeout=16)
    data = request.json()
    try:
        for wos_record in data['Data']['Records']['records']['REC']:
            records.append(fetch_expanded_metadata(wos_record))
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
        print(f'Resending WoS API request #{i + 1}')
        time.sleep(1)
        expanded_api_request(i, search_query, requests_required, records)
    print(f"{((i + 1) * 100) / requests_required:.1f}% documents retrieved")
    if app.retrieve_cited_refs.get():
        progress = ((i + 1) / requests_required)
    else:
        progress = ((i + 1) / requests_required) * 100
    app.progress_bar.config(value=progress)
    app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    app.root.update_idletasks()


def fetch_starter_metadata(record):
    """Parse the metadata fields required for VOSviewer that are available via
    Web of Science Starter API

    :param record: dict.
    :return: dict.
    """
    ut = record['uid']
    py = record['source']['publishYear']
    try:
        names = []
        for name in record['names']['authors']:
            names.append(name['wosStandard'])
        authors = '; '.join(names)
    except TypeError:
        authors = ''
        # Uncomment the following line for debugging:
        print(f'Something weird with the author names in record: {ut}')
    source_title = record['source']['sourceTitle']
    doc_title = record['title']
    try:
        keywords = '; '.join(record['keywords']['authorKeywords'])
    except KeyError:
        keywords = ''
        # Uncomment the following lines for debugging:
        # print(f'No keywords for record {ut}')
        # print(record['static_data']['fullrecord_metadata'])
    except TypeError:
        keywords = ['']
        # Uncomment the following lines for debugging:
        # print(f"Something weird in record {ut}:
        # {record['static_data']['fullrecord_metadata']['keywords']}")
    try:
        for db in record['citations']:
            if db['db'] == 'wos':
                tc = db['count']
                break
        else:
            tc = 0
    except KeyError:
        tc = 0
    return {'UT': ut, 'PY': py, 'AU': authors, 'SO': source_title, 'TI': doc_title,
            'DE': keywords, 'TC': tc}


def starter_api_request(i, search_query, requests_required, records):
    """Send Web of Science Starter API request to get records metadata.

    :param i: int.
    :param search_query: str.
    :param requests_required: int.
    :param records: list.
    :return: None.
    """
    user_apikey = app.apikey_window.get()
    request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents?db=WOS&q='
                           f'{urllib.parse.quote(search_query)}&limit=50&page={i + 1}',
                           headers={'X-APIKey': user_apikey},
                           timeout=16)
    data = request.json()
    try:
        for wos_record in data['hits']:
            records.append(fetch_starter_metadata(wos_record))
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
        print(f'Resending WoS API request #{i + 1}')
        time.sleep(1)
        starter_api_request(i, search_query, requests_required, records)
    print(f"{((i + 1) * 100) / requests_required:.1f}% complete")
    if app.retrieve_cited_refs.get():
        progress = ((i + 1) / requests_required)
    else:
        progress = ((i + 1) / requests_required) * 100
    app.progress_bar.config(value=progress)
    app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    app.root.update_idletasks()


def fetch_cited_metadata(cited_record):
    """Parse the cited reference record for individual metadata fields.

    :param cited_record: dict.
    :return: str.
    """
    cited_ref_string = ''
    fields = ('CitedAuthor', 'Year', 'CitedWork', 'Volume', 'Page', 'DOI')
    for field in fields:
        if field in cited_record.keys():
            cited_ref_string += f"{cited_record[field]}, "
    return cited_ref_string[:-2]


def cited_endpoint_request(record, records, i, user_apikey):
    """Query the cited endpoint if the "Also retrieve Cited References" checkbox is ticked.

    :param record: dict.
    :param records: list.
    :param i: int.
    :param user_apikey: str.
    :return: None
    """
    crs = []
    initial_cited_request = requests.get(f'https://api.clarivate.com/api/wos/references?'
                                         f'databaseId=WOS&uniqueId={record["UT"]}'
                                         f'&count=100&firstRecord=1',
                                         headers={'X-APIKey': user_apikey},
                                         timeout=16)
    try:
        cited_json = initial_cited_request.json()
        for cited_record in cited_json['Data']:
            crs.append(fetch_cited_metadata(cited_record))
        if cited_json['QueryResult']['RecordsFound'] > 100:
            cited_requests_required = ((cited_json['QueryResult']['RecordsFound'] - 1) // 100) + 1
            for j in range(1, cited_requests_required):
                cited_request = requests.get(f'https://api.clarivate.com/api/wos/references?'
                                             f'databaseId=WOS&uniqueId={record["UT"]}'
                                             f'&count=100&firstRecord={j}01',
                                             headers={'X-APIKey': user_apikey},
                                             timeout=16)
                cited_json = cited_request.json()
                for cited_record in cited_json['Data']:
                    crs.append(fetch_cited_metadata(cited_record))
        record['CR'] = '; '.join(crs)
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
        print(f'Resending WoS API request #{i + 1}')
        time.sleep(1)
        cited_endpoint_request(record, records, i, user_apikey)
    progress = ((len(records) / 100 + i + 1) / (len(records) * 1.01)) * 100
    app.progress_bar.config(value=progress)
    app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    app.root.update_idletasks()


def output(search_query, records):
    """Save data into a .txt tab-felimited file.

    :param search_query: str.
    :param records: list.
    :return: str.
    """
    df = pd.DataFrame(records)
    if len(search_query) > 100 and app.retrieve_cited_refs.get():
        safe_search_query = search_query[:100]
        filename = f'{safe_search_query}... - {date.today()} - with cited references.txt'
    elif len(search_query) <= 100 and app.retrieve_cited_refs.get():
        filename = f'{search_query} - {date.today()} - with cited references.txt'
    elif len(search_query) > 100 and app.retrieve_cited_refs.get() is False:
        safe_search_query = search_query[:100]
        filename = f'{safe_search_query} - {date.today()}.txt'
    else:
        filename = f'{search_query} - {date.today()}.txt'
    safe_filename = (filename.replace('?', '').replace('*', '').replace('"', ''))
    df.to_csv(f'{safe_filename}', index=False, sep='\t')
    return safe_filename


def format_label_text(text, symbol_limit):
    """Wraps words for longer messages.

    :param text: str.
    :param symbol_limit: int.
    :return: str.
    """
    return '\n'.join(textwrap.wrap(text, symbol_limit))


def unhide_symbols():
    """Hide/unhide symbols in the API key field.

    :return: None.
    """
    if app.apikey_window['show'] == "*":
        app.apikey_window['show'] = ""
    else:
        app.apikey_window['show'] = "*"


# A function for checking the validity of the API key
def validate_api_key():
    """Validate the API key, check how many records are left for Expanded API.

    :return: str or None.
    """
    user_apikey = app.apikey_window.get()
    # Sending an Expanded test request to check if it passes authentication
    validation_request = requests.get('https://api.clarivate.com/api/wos?databaseId=WOS&'
                                      'usrQuery=AU=Garfield&count=0&firstRecord=1',
                                      headers={'X-APIKey': user_apikey},
                                      timeout=16)
    if validation_request.status_code == 200:
        # If the API call with this key is a success,also return the amount of records remaining
        docs_left = validation_request.headers['X-REC-AmtPerYear-Remaining']
        app.apikey_bottom_label['text'] = (f"Expanded API Authentication succeeded; "
                                           f"Records left to retrieve: {docs_left}")
        app.cited_references_checkbutton.config(state='active')
        return 'expanded'
    # If the Expanded API request status is anything but 200, send a Starter API test request
    validation_request_starter = requests.get('https://api.clarivate.com/apis/wos-starter/v1/'
                                              'documents?db=WOS&q=AU=Garfield&limit=1&page=1',
                                              headers={'X-APIKey': user_apikey},
                                              timeout=16)
    if validation_request_starter.status_code == 200:
        try:
            requests_left_today = validation_request_starter.headers['X-RateLimit-Remaining-Day']
        except KeyError:
            requests_left_today = 99999999
        if int(requests_left_today) < 100:
            label_text = (f'Starter API authentication succeeded; Requests left today: '
                          f'{requests_left_today}')

        else:
            label_text = ('Starter API authentication succeeded. Address, Abstract, Keywords Plus,'
                          ' and Cited references metadata is only available with Expanded API')
        app.apikey_bottom_label['text'] = format_label_text(label_text, 94)
        if app.retrieve_cited_refs.get():
            app.cited_references_checkbutton.invoke()
        app.cited_references_checkbutton.config(state='disabled')
        return 'starter'
    app.apikey_bottom_label['text'] = "Wrong API Key"
    return None


def validate_search_query():
    """Make sure the search query provided by the user is a valid one.

    :return: bool.
    """
    app.search_query_bottom_label['text'] = 'Validating...\n\n'
    wos_api_type = validate_api_key()
    if wos_api_type is None:
        app.apikey_bottom_label['text'] = "Wrong API Key"
        return False
    user_apikey = app.apikey_window.get()
    search_query = app.search_query_window.get("1.0", "end-1c")
    if wos_api_type == 'expanded':
        validation_request_json = {"databaseId": "WOS",
                                   "usrQuery": f"{search_query}",
                                   "count": 0,
                                   "firstRecord": 1
                                   }
        validation_request = requests.post('https://wos-api.clarivate.com/api/wos',
                                           json=validation_request_json,
                                           headers={'X-APIKey': user_apikey},
                                           timeout=16)
        validation_data = validation_request.json()
        if validation_request.status_code == 200:
            records_amount = validation_data['QueryResult']['RecordsFound']
            app.search_query_bottom_label['text'] = f'Records found: {records_amount} \n\n'
            if records_amount == 0:
                return False
            if records_amount > 100000:
                text = (f'Records found: {records_amount}. You can export a maximum of 100k '
                        f'records through Expanded API\n')
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
    if wos_api_type == 'starter':
        validation_request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents'
                                          f'?db=WOS&q={urllib.parse.quote(search_query)}&'
                                          f'limit=1&page=1', headers={'X-APIKey': user_apikey},
                                          timeout=16)
        validation_data = validation_request.json()
        if validation_request.status_code == 200:
            records_amount = validation_data['metadata']['total']
            try:
                wos_api_limit = (int(validation_request.headers['X-RateLimit-Remaining-Day']) - 1) * 50
            except KeyError:
                wos_api_limit = 99999999
            if records_amount == 0:
                return False
            if records_amount > wos_api_limit:
                label_text = (f'Web of Science records found: {records_amount}. You have '
                              f'a maximum of {wos_api_limit} records remaining to export '
                              f'today using {wos_api_type}')
                app.search_query_bottom_label['text'] = format_label_text(label_text, 94)
                return True
            app.search_query_bottom_label['text'] = (f'Web of Science records found: '
                                                     f'{records_amount}\n\n')
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


def main_function():
    """When the 'Run' button is clicked, manage all the other functions.

    :return: None.
    """
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
        initial_request_json = {"databaseId": "WOS",
                                "usrQuery": f"{search_query}",
                                "count": 0,
                                "firstRecord": 1}
        initial_request = requests.post('https://wos-api.clarivate.com/api/wos',
                                        json=initial_request_json,
                                        headers={'X-APIKey': app.apikey_window.get()},
                                        timeout=16)
        data = initial_request.json()
        requests_required = ((data['QueryResult']['RecordsFound'] - 1) // 100) + 1
        for i in range(requests_required):
            expanded_api_request(i, search_query, requests_required, records)
        if app.retrieve_cited_refs.get():
            for record in records:
                user_apikey = app.apikey_window.get()
                cited_endpoint_request(record, records, records.index(record), user_apikey)
                print(f"{((records.index(record) + 1) * 100) / len(records):.1f}% cited "
                      f"references requests complete")
    elif wos_api_type == 'starter':
        # This is the initial Starter API request
        initial_request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents?'
                                       f'db=WOS&q={urllib.parse.quote(search_query)}&'
                                       f'limit=1&page=1',
                                       headers={'X-APIKey': app.apikey_window.get()},
                                       timeout=16)
        data = initial_request.json()
        requests_required = ((data['metadata']['total'] - 1) // 100) + 1
        for i in range(requests_required):
            starter_api_request(i, search_query, requests_required, records)
    safe_filename = output(search_query, records)
    app.search_button.config(state='active', text='Run')
    message = f"Retrieval complete. Please check the {safe_filename} file for results"
    app.progress_label['text'] = format_label_text(message, 94)


class App(threading.Thread):
    """Application class through threading so that the interface doesn't
    freeze when the data is being retrieved through API.

    """

    def __init__(self, ):
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
        self.retrieve_cited_refs = None
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
        self.root.geometry("535x440")
        self.root.resizable(False, False)
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.style.configure('White.TFrame', background='#FFFFFF')
        self.style.configure('Bold.TLabel', font=('Calibri bold', 12), borderwidth=0,
                             bordercolor='#000000', selectborderwidth=0)
        self.style.map('Bold.TLabel',
                       foreground=[('focus', '#000000'), ('!focus', '#000000')],
                       background=[('focus', '#FFFFFF'), ('!focus', '#FFFFFF')])
        self.style.configure('Regular.TLabel', font=('Calibri', 10), borderwidth=0,
                             bordercolor='#000000', selectborderwidth=0)
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
                       indicatorbackground=[('selected', '#FFFFFF'),
                                            ('active', '#F0F0EB'),
                                            ('!selected', '#FFFFFF')],
                       upperbordercolor=[('selected', '#5E33BF'),
                                         ('!selected', '#646363'),
                                         ('disabled', '#DADADA')],
                       lowerbordercolor=[('selected', '#5E33BF'),
                                         ('!selected', '#646363'),
                                         ('disabled', '#DADADA')])
        # Borrowed the horizontal progressbar from the Default scheme in order to remove one extra
        # frame around the progress bar
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
        self.style.configure('Clarivate.Horizontal.TProgressbar', font=('Calibri bold', 12),
                             borderwidth=0, troughcolor='#F0F0EB', background='#16AB03',
                             foreground='#000000', text='', anchor='center')

        # Setting up widgets
        self.api_frame = ttk.Frame(self.root, style='White.TFrame')
        self.apikey_top_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                          text="Web of Science API Key:")
        apikey = tk.StringVar()
        self.apikey_window = ttk.Entry(self.api_frame, font=('Calibri', 11), show="*",
                                       textvariable=apikey, validate="focusout")
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
                                            text="Web of Science Core Collection Advanced Search "
                                                 "query:")
        self.search_query_window = tk.Text(self.api_frame, font=("Calibri", 12),
                                           borderwidth=1, relief='solid', wrap='word')
        self.search_query_window.insert('1.0', 'OG=Clarivate and PY=2008-2022')
        self.search_validate_button = ttk.Button(self.api_frame, text="Validate",
                                                 style='Small.TButton',
                                                 command=self.check_search_query)
        self.retrieve_cited_refs = BooleanVar()
        self.cited_references_checkbutton = ttk.Checkbutton(self.api_frame,
                                                            text='  Also retrieve Cited References'
                                                                 ' (takes significantly '
                                                                 'more time)',
                                                            variable=self.retrieve_cited_refs,
                                                            onvalue=True,
                                                            offvalue=False,
                                                            style='Clarivate.TCheckbutton')
        self.search_query_bottom_label = ttk.Label(self.api_frame, text='', style='Regular.TLabel')
        self.search_button = ttk.Button(self.api_frame,
                                        text='Run',
                                        style='Large.TButton',
                                        command=self.run_button)
        self.progress_bar = ttk.Progressbar(self.api_frame,
                                            style='Clarivate.Horizontal.TProgressbar',
                                            mode="determinate")
        self.progress_label = ttk.Label(self.api_frame, style='Regular.TLabel')

        # Placing widgets
        self.api_frame.place(x=0, y=0, width=535, height=440)
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
