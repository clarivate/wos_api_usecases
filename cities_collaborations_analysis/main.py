"""
This code can analyze cities involvement in certain research, i.e., analyzing which cities are the
centers of scientific research on a given topics, which cities does a specific organization
collaborate with, or which cities does a specific organization concentrate its research at.
Just modify in the search_query and - optionally - our_org variables, and run the code.
"""
import threading
import urllib.parse
import time
import tkinter as tk
from tkinter import ttk, StringVar, IntVar
from tkinter.filedialog import askopenfilename
from datetime import date
import requests
import pandas as pd
import plotly.express as px


# The cities are to be stored in a list. If there is an existing organizational profile mentioned in the "our_org"
# field, the program will store the list of cities associated with this org to keep them separate from the
# collaborating cities list
def our_org_city_check(wos_city, wos_state, wos_country, our_org_cities):
    if len(our_org_cities) >= 1:
        for our_org_city in our_org_cities:
            if our_org_city['name'] == wos_city and \
                    our_org_city['state'] == wos_state and \
                    our_org_city['country'] == wos_country:
                our_org_city['occurrences'] += 1
                break
        else:
            our_org_cities.append({'name': wos_city, 'state': wos_state, 'country': wos_country, "occurrences": 1})
    else:
        our_org_cities.append({'name': wos_city, 'state': wos_state, 'country': wos_country, "occurrences": 1})


def city_check(wos_city, wos_state, wos_country, cities):
    if len(cities) > 1:
        for city in cities:
            if city['name'] == wos_city and city['state'] == wos_state and city['country'] == wos_country:
                city['occurrences'] += 1
                break
        else:
            cities.append({'name': wos_city, 'state': wos_state, 'country': wos_country, "occurrences": 1})
    else:
        cities.append({'name': wos_city, 'state': wos_state, 'country': wos_country, "occurrences": 1})


# This function gets the cities values from the Web of Science records which we received through the API
def analyze_cities(records, our_org, cities, our_org_cities):
    country_glossary = [['Peoples R China', 'China'],
                        ['Czech Republic', 'Czechia'],
                        ['U Arab Emirates', 'United Arab Emirates'],
                        ['England', 'United Kingdom'],
                        ['Scotland', 'United Kingdom'],
                        ['Wales', 'United Kingdom'],
                        ['North Ireland', 'United Kingdom'],
                        ['Usa', 'United States']]

    for paper in records:  # This is how we iterate over individual WoS records
        if paper['static_data']['fullrecord_metadata']['addresses']['count'] == 1:  # if there's only 1 address
            for org in (
                    paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']
                    ['organizations']['organization']
            ):
                # Iterating over individual organizations in the address field. First, storing the city belonging
                # to our organization
                if org['pref'] == 'Y' and org['content'] == our_org:
                    wos_city = paper['static_data']['fullrecord_metadata']['addresses']['address_name'] \
                        ['address_spec']['city'].title()
                    wos_country = paper['static_data']['fullrecord_metadata']['addresses']['address_name'] \
                        ['address_spec']['country'].title()
                    if wos_country == 'Usa':
                        wos_state = paper['static_data']['fullrecord_metadata']['addresses']['address_name'] \
                            ['address_spec']['state']
                    else:
                        wos_state = ''
                    for country in country_glossary:
                        if wos_country == country[0]:
                            wos_country = country[1]
                    our_org_city_check(wos_city, wos_state, wos_country, our_org_cities)
                    break
            # Storing the cities belonging to every other org.
            else:
                wos_city = paper['static_data']['fullrecord_metadata']['addresses']['address_name'] \
                    ['address_spec']['city'].title()
                wos_country = paper['static_data']['fullrecord_metadata']['addresses']['address_name'] \
                    ['address_spec']['country'].title()
                if wos_country == 'Usa':
                    wos_state = paper['static_data']['fullrecord_metadata']['addresses']['address_name'] \
                        ['address_spec']['state']
                else:
                    wos_state = ''
                for country in country_glossary:
                    if wos_country == country[0]:
                        wos_country = country[1]
                city_check(wos_city, wos_state, wos_country, cities)
        # Standard case - when there are multiple addresses in the document record
        else:
            # These 2 variables allow us to make multiple addresses with the same city count only once for each paper.
            cities_cache = []
            our_cities_cache = []
            try:
                # Iterating over individual addresses in the Web of Science record
                for address in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
                    try:
                        wos_city = address['address_spec']['city'].title()
                        wos_country = address['address_spec']['country'].title()
                        if wos_country == 'Usa':
                            wos_state = address['address_spec']['state']
                        else:
                            wos_state = ''
                        for country in country_glossary:
                            if wos_country == country[0]:
                                wos_country = country[1]
                        # Iterating over individual organizations in the address field
                        for org in address['address_spec']['organizations']['organization']:
                            if org['pref'] == 'Y' and org['content'] == our_org:
                                # storing the city belonging to organization being analyzed
                                if [wos_city, wos_state, wos_country] not in our_cities_cache:
                                    our_cities_cache.append([wos_city, wos_state, wos_country])
                                    our_org_city_check(wos_city, wos_state, wos_country, our_org_cities)
                                    break
                        else:
                            if [wos_city, wos_state, wos_country] not in cities_cache:
                                cities_cache.append([wos_city, wos_state, wos_country])
                                # storing the cities belonging to every other org. Each of them stored as a list item
                                city_check(wos_city, wos_state, wos_country, cities)
                    except KeyError:  # When there's no org data in the address (i.e., only street address)
                        pass
            except KeyError:  # when there's no address field in the record
                pass


# This function sends the main API requests to retrieve the data
def wos_api_request(i, search_query, records, requests_required):
    subsequent_response = requests.get(
        f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&'
        f'count=10&firstRecord={i}1', headers={'X-APIKey': app.apikey_window.get()}
    )
    data = subsequent_response.json()
    try:
        for wos_record in data['Data']['Records']['records']['REC']:
            records.append(wos_record)
    # This is to prevent certain occasional connection problems
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i + 1}')
        time.sleep(1)
        wos_api_request(i, search_query, records, requests_required)
    print(f"{((i + 1) * 100) / requests_required:.1f}% complete")
    progress = ((i + 1) / requests_required) * 100
    app.progress_bar.config(value=progress)
    app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    app.root.update_idletasks()


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
    validation_request = requests.get(
        'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery=AU=Garfield&count=0&firstRecord=1',
        headers={'X-APIKey': user_apikey}
    )
    if validation_request.status_code == 200:
        # If the API call with this key is a success, we're also return the amount of records remaining
        docs_left = validation_request.headers['X-REC-AmtPerYear-Remaining']
        app.apikey_bottom_label['text'] = f"API Authentication succeeded; Records left to retrieve: {docs_left}"
        return True
    app.apikey_bottom_label['text'] = "Wrong API Key"
    return False


# Function to check how many results the search query returns
def validate_search():
    if validate_api_key():
        user_apikey = app.apikey_window.get()
        search_query = app.search_query_window.get("1.0", "end-1c")
        validation_request = requests.get(
            f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&'
            f'count=0&firstRecord=1', headers={'X-APIKey': user_apikey})
        if validation_request.status_code == 200:
            validation_data = validation_request.json()
            records_amount = validation_data['QueryResult']['RecordsFound']
            app.search_query_bottom_label['text'] = f'Records found: {records_amount} \n '
            if records_amount == 0:
                return False
            if records_amount > 100000:
                app.search_query_bottom_label['text'] = (f'Records found: {records_amount}. You can export '
                                                         f'a maximum of 100k records through Expanded API\n')
                return True
            return True
        validation_data = validation_request.json()
        error_message_text = validation_data['message'][validation_data['message'].find(": ") + 2:]
        app.search_query_bottom_label['text'] = (f'Request failed with status code '
                                                 f'{validation_request.status_code}\n'
                                                 f'{format_label_text(error_message_text, 94)}')
        return False
    return False


# A function to make sure the affiliation name provided bythe user is a valid one
def validate_affiliation():
    if validate_api_key():
        user_apikey = app.apikey_window.get()
        search_query = f'OG={app.our_org_window.get()}'
        validation_request = requests.get(f'https://api.clarivate.com/api/wos?databaseId=WOS&'
                                          f'usrQuery={urllib.parse.quote(search_query)}&count=0&firstRecord=1',
                                          headers={'X-APIKey': user_apikey})
        if validation_request.status_code == 200:
            validation_data = validation_request.json()
            records_amount = validation_data['QueryResult']['RecordsFound']
            if records_amount > 0:
                return True
            app.our_org_bottom_label['text'] = 'Please check your Affiliation name'
            return False
        app.our_org_bottom_label['text'] = 'Please check your Affiliation name'
        return False
    print('Wrong API Key')
    return False


# This function starts when the "Run" button is clicked and launches all the others
def main_function():
    app.search_button.config(state='disabled', text='Retrieving...')
    app.progress_label['text'] = ''
    if validate_api_key() is False:
        app.apikey_bottom_label['text'] = "Wrong API Key"
        app.search_button.config(state='active', text='Run')
        return False
    if validate_search() is False:
        app.progress_label['text'] = 'Please check your search query'
        app.search_button.config(state='active', text='Run')
        return False
    if app.exclude_collaborations.get() > 1 and validate_affiliation() is False:
        app.search_button.config(state='active', text='Run')
        return False
    our_org = app.our_org_window.get()
    if ('Please check your search query' or 'Calculation complete') in app.progress_label['text']:
        app.progress_label['text'] = ''
    if app.our_org_bottom_label['text'] == 'Please check your Affiliation name':
        app.our_org_bottom_label['text'] = ''
    search_query = app.search_query_window.get("1.0", "end-1c")

    cities = []
    our_org_cities = []

    # This is the initial API request
    initial_request = requests.get(
        f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&count=0&'
        f'firstRecord=1', headers={'X-APIKey': app.apikey_window.get()}
    )
    data = initial_request.json()
    requests_required = ((data['QueryResult']['RecordsFound'] - 1) // 10) + 1
    records = []

    # From the first response, extracting the total number of records found and calculating the number of requests
    # required. The program can take up to a few dozen minutes, depending on the number of records being analyzed
    for i in range(requests_required):
        wos_api_request(i, search_query, records, requests_required)
    analyze_cities(records, our_org, cities, our_org_cities)
    output(our_org, search_query, app.exclude_collaborations.get(), cities, our_org_cities)
    app.search_button.config(state='active', text='Run')
    complete_message = f"Calculation complete. Please check the cities - {search_query} - {date.today()}.xlsx " \
                       f"file for results"
    app.progress_label['text'] = format_label_text(complete_message, 94)


# Defining a class through threading so that the interface doesn't freeze when the data is being retrieved through API
class App(threading.Thread):

    def __init__(self, ):
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
        self.apikey_button = None
        self.apikey_bottom_label = None
        self.search_query_label = None
        self.search_query_window = None
        self.search_validate_button = None
        self.search_query_bottom_label = None
        self.maximize_image = None
        self.minimize_image = None
        self.our_org_framebutton = None
        self.our_org_label = None
        self.our_org_window = None
        self.our_org_bottom_label = None
        self.exclude_collaborations = None
        self.exclude_collaborations_radio = None
        self.keep_collaborations_radio = None
        self.no_breakdown_radio = None
        self.search_button = None
        self.progress_bar = None
        self.progress_label = None
        self.offline_frame = None
        self.offline_label = None
        self.filename_label = None
        self.filename_entry = None
        self.browse_image = None
        self.open_file_button = None
        self.file_name = None
        self.filename_bottom_label = None
        self.exclude_collaborations_offline = None
        self.exclude_collaborations_offline_radio = None
        self.keep_collaborations_offline_radio = None
        self.draw_graph_button = None
        self.start()

    def run(self):
        self.root = tk.Tk()
        self.root.iconbitmap('./assets/clarivate.ico')
        self.root.title("City Data Visualizations")
        self.root.geometry("540x620")
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
        self.style.configure('Framed.TFrame', background='#FFFFFF', bordercolor='#DADADA',
                             borderwidth=1, relief='solid')
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
                       bordercolor=[('focus', '#5E33BF'), ('disabled', '#DADADA'), ('!focus', '#000000')],
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
        self.style.layout(
            'Frame.TButton', [
                ('Button.button', None),
                ('Button.border', {'children': [
                    ('Button.focus', {'children': [
                        ('Button.padding', {'children': [
                            ('Button.label', {'side': 'top'}
                             )]}
                         )]}
                     )]}
                 )]
        )
        self.style.configure('Frame.TButton', justify='left', font=('Calibri bold', 12), borderwidth=1,
                             padding=(10, 5, 5, 5))
        self.style.map('Frame.TButton',
                       foreground=[('active', '#000000'), ('!active', '#000000')],
                       background=[('active', '#F0F0EB'), ('!active', '#FFFFFF')],
                       bordercolor=[('active', '#5E33BF'), ('!active', '#FFFFFF')],
                       focuscolor=[('disabled', '#F0F0EB'), ('!disabled', '#FFFFFF')])
        self.style.configure('TRadiobutton', font=('Calibri', 11), indicatorsize=16)
        self.style.map('TRadiobutton',
                       foreground=[('disabled', '#000000'), ('!disabled', '#000000')],
                       background=[('disabled', '#FFFFFF'), ('!disabled', '#FFFFFF')],
                       focuscolor=[('disabled', '#FFFFFF'), ('!disabled', '#FFFFFF')],
                       indicatorforeground=[('selected', '#5E33BF'), ('!selected', '#FFFFFF')],
                       indicatorbackground=[('selected', '#FFFFFF'), ('active', '#F0F0EB'), ('!selected', '#FFFFFF')],
                       upperbordercolor=[('selected', '#5E33BF'), ('!selected', '#646363')],
                       lowerbordercolor=[('selected', '#5E33BF'), ('!selected', '#646363')])
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
        self.apikey_top_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                          text="Web of Science Expanded API Key:")
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
        self.search_query_window.insert('1.0', 'OG=Clarivate and PY=2018-2022')
        self.search_validate_button = ttk.Button(self.api_frame, text="Validate", style='Small.TButton',
                                                 command=self.check_search_query)
        self.search_query_bottom_label = ttk.Label(self.api_frame, text='', style='Regular.TLabel')
        self.maximize_image = tk.PhotoImage(file='./assets/XC_icon_arrow_down.png')
        self.minimize_image = tk.PhotoImage(file='./assets/XC_icon_arrow_up.png')
        self.our_org_framebutton = ttk.Button(self.api_frame, style='Frame.TButton', command=self.maximize,
                                              text='Own / Collaborating Cities Breakdown                              '
                                                   '                         ',
                                              image=self.maximize_image, compound='right')
        self.our_org_label = ttk.Label(self.our_org_framebutton, style='Bold.TLabel',
                                       text="Affiliation name:")
        self.our_org_window = ttk.Entry(self.our_org_framebutton, font=('Calibri', 11))
        self.our_org_bottom_label = ttk.Label(self.our_org_framebutton,
                                              text='This is the name of the organization that you\'d like to '
                                                   'analyze for its cities',
                                              style='Regular.TLabel')
        self.exclude_collaborations = IntVar(value=0)
        self.exclude_collaborations_radio = ttk.Radiobutton(self.our_org_framebutton,
                                                            text='Exclude Collaborating Cities',
                                                            value=2,
                                                            variable=self.exclude_collaborations,
                                                            command=self.enable_affiliation)
        self.keep_collaborations_radio = ttk.Radiobutton(self.our_org_framebutton,
                                                         text='Keep Only Collaborating Cities',
                                                         value=3,
                                                         variable=self.exclude_collaborations,
                                                         command=self.enable_affiliation)
        self.no_breakdown_radio = ttk.Radiobutton(self.our_org_framebutton,
                                                  text='No Own/Collaborating Breakdown',
                                                  value=1,
                                                  variable=self.exclude_collaborations,
                                                  command=self.disable_affiliation)
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
                                       text='Here you can simply load a previously saved Excel file and vizualize '
                                            'the cities locations from it.\n')
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
        self.filename_bottom_label = ttk.Label(self.offline_frame, style='Regular.TLabel', text='')
        self.exclude_collaborations_offline = IntVar(value=0)
        self.exclude_collaborations_offline_radio = ttk.Radiobutton(self.offline_frame,
                                                                    text='Exclude Collaborating Cities',
                                                                    value=1,
                                                                    variable=self.exclude_collaborations_offline)
        self.keep_collaborations_offline_radio = ttk.Radiobutton(self.offline_frame,
                                                                 text='Keep Only Collaborating Cities',
                                                                 value=2,
                                                                 variable=self.exclude_collaborations_offline)
        self.draw_graph_button = ttk.Button(self.offline_frame,
                                            text='Visualize',
                                            style='Large.TButton',
                                            command=self.draw_graph)

        self.tabs.place(x=0, y=0, width=540, height=620)
        self.tab1.place(x=0, y=0, width=0, height=0)
        self.tab2.place(x=0, y=0, width=0, height=0)
        self.tabs.add(self.tab1, text='             RETRIEVE THROUGH API             ')
        self.tabs.add(self.tab2, text='               LOAD EXCEL FILE                 ')
        self.api_frame.place(x=0, y=0, width=540, height=600)
        self.apikey_top_label.place(x=5, y=5, width=535, height=24)
        self.apikey_window.place(x=5, y=29, width=400, height=30)
        self.apikey_unhide_button.place(x=406, y=29, width=30, height=30)
        self.apikey_button.place(x=440, y=29, width=90, height=30)
        self.apikey_bottom_label.place(x=5, y=59, width=400, height=24)
        self.search_query_label.place(x=5, y=89, width=400, height=24)
        self.search_query_window.place(x=5, y=113, width=400, height=90)
        self.search_validate_button.place(x=410, y=113, width=120, height=30)
        self.search_query_bottom_label.place(x=5, y=203, width=500, height=40)
        self.our_org_framebutton.place(x=5, y=250, width=525, height=34)
        self.exclude_collaborations_radio.place(x=5, y=35, width=250, height=25)
        self.keep_collaborations_radio.place(x=5, y=60, width=250, height=25)
        self.no_breakdown_radio.place(x=5, y=85, width=250, height=25)
        self.our_org_label.place(x=5, y=110, width=400, height=30)
        self.our_org_window.place(x=5, y=140, width=400, height=30)
        self.our_org_bottom_label.place(x=5, y=170, width=500, height=24)
        self.search_button.place(x=220, y=300, width=100, height=35)
        self.progress_bar.place(x=5, y=350, width=525, height=30)
        self.progress_label.place(x=5, y=380, width=525, height=40)
        self.offline_frame.place(x=0, y=0, width=540, height=600)
        self.offline_label.place(x=5, y=0, width=535, height=50)
        self.filename_label.place(x=5, y=65, width=535, height=24)
        self.filename_entry.place(x=5, y=89, width=495, height=30)
        self.open_file_button.place(x=502, y=89, width=30, height=30)
        self.filename_bottom_label.place(x=5, y=119, width=495, height=24)
        self.draw_graph_button.place(x=220, y=150, width=100, height=35)

        self.root.mainloop()

    def maximize(self):
        self.our_org_framebutton.place(x=5, y=250, width=525, height=200)
        self.style.map('Frame.TButton',
                       background=[('active', '#FFFFFF'), ('!active', '#FFFFFF')],
                       focuscolor=[('disabled', '#FFFFFF'), ('!disabled', '#FFFFFF')])
        self.our_org_framebutton['image'] = self.minimize_image
        self.our_org_framebutton['command'] = self.minimize
        self.search_button.place(x=220, y=470, width=100, height=35)
        self.progress_bar.place(x=5, y=520, width=525, height=30)
        self.progress_label.place(x=5, y=550, width=525, height=40)

    def minimize(self):
        self.exclude_collaborations.set(0)
        self.our_org_framebutton.place(x=5, y=250, width=525, height=34)
        self.style.map('Frame.TButton',
                       background=[('active', '#F0F0EB'), ('!active', '#FFFFFF')],
                       focuscolor=[('disabled', '#F0F0EB'), ('!disabled', '#FFFFFF')])
        self.our_org_framebutton['image'] = self.maximize_image
        self.our_org_framebutton['command'] = self.maximize
        self.search_button.place(x=220, y=300, width=100, height=35)
        self.progress_bar.place(x=5, y=350, width=525, height=30)
        self.progress_label.place(x=5, y=380, width=525, height=40)

    def disable_affiliation(self):
        self.our_org_window.state(['disabled'])

    def enable_affiliation(self):
        self.our_org_window.state(['!disabled'])

    def check_api_key(self):
        threading.Thread(target=validate_api_key).start()

    def check_search_query(self):
        threading.Thread(target=validate_search).start()

    def run_button(self):
        threading.Thread(target=main_function).start()

    def file_menu(self):
        self.file_name.set(askopenfilename(initialdir='./', filetypes=[("Excel files", "*.xlsx")]))
        try:
            pd.read_excel(self.filename_entry.get(), sheet_name='Collaborating Cities')
            pd.read_excel(self.filename_entry.get(), sheet_name='Our Org Cities')
            self.exclude_collaborations_offline_radio.place(x=5, y=130, width=250, height=25)
            self.keep_collaborations_offline_radio.place(x=255, y=130, width=250, height=25)
            self.filename_bottom_label.place(x=5, y=160, width=495, height=24)
            self.draw_graph_button.place(x=220, y=210, width=100, height=35)
            self.filename_bottom_label['text'] = ''
        except ValueError:
            try:
                pd.read_excel(self.filename_entry.get(), sheet_name='Cities')
                self.exclude_collaborations_offline.set(0)
                self.exclude_collaborations_offline_radio.place_forget()
                self.keep_collaborations_offline_radio.place_forget()
                self.filename_bottom_label.place(x=5, y=119, width=495, height=24)
                self.draw_graph_button.place(x=220, y=150, width=100, height=35)
                self.filename_bottom_label['text'] = ''
            except ValueError:
                self.filename_bottom_label['text'] = 'Oops! Seems like a wrong Excel file'

    def draw_graph(self):
        threading.Thread(target=offline_plotting).start()


app = App()


# Getting the cities geographic coordinates to be able to plot them on the map
def worldcities():
    # Loading a file with cities of the world and their latitude and longitude data - obtained from SimpleMaps World
    # Cities Database (http://simplemaps.com/data/world-cities) under CC-BY 4.0
    df2 = pd.read_csv('worldcities.csv')

    # That file provides full name for the US states, while our file from Web of Science contains abbreviations.
    states_dict = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
                   'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC',
                   'Florida': 'FL',
                   'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN',
                   'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME',
                   'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
                   'Mississippi': 'MS',
                   'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH',
                   'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
                   'North Dakota': 'ND',
                   'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI',
                   'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
                   'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI',
                   'Wyoming': 'WY'}

    # Preparing the dataframe for plotting
    df2['state'] = df2[df2['country'] == 'United States']['admin_name'].map(states_dict)
    df2_us = pd.DataFrame()
    df2_us['name'] = df2[df2['country'] == 'United States']['city_ascii'] + ', ' + \
        df2[df2['country'] == 'United States']['state'] + ', ' + \
        df2[df2['country'] == 'United States']['country']
    df2_us['lat'] = df2[df2['country'] == 'United States']['lat']
    df2_us['lng'] = df2[df2['country'] == 'United States']['lng']
    df2_non_us = pd.DataFrame()
    df2_non_us['name'] = df2[df2['country'] != 'United States']['city_ascii'] + ', ' + \
        df2[df2['country'] != 'United States']['country']
    df2_non_us['lat'] = df2[df2['country'] != 'United States']['lat']
    df2_non_us['lng'] = df2[df2['country'] != 'United States']['lng']
    return df2_us, df2_non_us


subtitle = f'© Clarivate {date.today().year}. Generated with Data from SimpleMaps World Cities Database ' \
           f'(https://simplemaps.com/data/world-cities) under CC-BY 4.0 and Web of Science from Clarivate'


# Saving the data into an excel file and visualizing the data
def output(our_org, search_query, exclude_collaborations, cities, our_org_cities):
    # All the cities data gets exported in an Excel file.
    df = pd.DataFrame(cities)
    df_our = pd.DataFrame(our_org_cities)
    search_parameters = pd.DataFrame(data={'Search Query': [search_query],
                                           'Our Organization': [our_org],
                                           'Search Date': [date.today()]})
    safe_search_query = search_query.replace('\"', '').replace('*', '')
    if exclude_collaborations == 0:
        with pd.ExcelWriter(f'cities - {safe_search_query} - {date.today()}.xlsx') as writer:
            df.to_excel(writer, sheet_name='Cities', index=False)
            search_parameters.to_excel(writer, sheet_name='Search Parameters', index=False)
    else:
        with pd.ExcelWriter(f'cities - {safe_search_query} - {date.today()}.xlsx') as writer:
            df.to_excel(writer, sheet_name='Collaborating Cities', index=False)
            df_our.to_excel(writer, sheet_name='Our Org Cities', index=False)
            search_parameters.to_excel(writer, sheet_name='Search Parameters', index=False)

    # Breaking the cities by US/non-US for higher plotting precision
    df_us = pd.DataFrame()
    if exclude_collaborations == 2:
        df_us['name'] = df_our[df_our['country'] == 'United States']['name'] + ', ' + \
                        df_our[df_our['country'] == 'United States']['state'] + ', ' + \
                        df_our[df_our['country'] == 'United States']['country']
        df_us['occurrences'] = df_our[df_our['country'] == 'United States']['occurrences']
        df_non_us = pd.DataFrame()
        df_non_us['name'] = df_our[df_our['country'] != 'United States']['name'] + ', ' + \
            df_our[df_our['country'] != 'United States']['country']
        df_non_us['occurrences'] = df_our[df_our['country'] != 'United States']['occurrences']
    elif exclude_collaborations == 3:
        df_us['name'] = df[df['country'] == 'United States']['name'] + ', ' + \
                        df[df['country'] == 'United States']['state'] + ', ' + \
                        df[df['country'] == 'United States']['country']
        df_us['occurrences'] = df[df['country'] == 'United States']['occurrences']
        df_non_us = pd.DataFrame()
        df_non_us['name'] = df[df['country'] != 'United States']['name'] + ', ' + \
            df[df['country'] != 'United States']['country']
        df_non_us['occurrences'] = df[df['country'] != 'United States']['occurrences']
    else:
        df_us['name'] = df[df['country'] == 'United States']['name'] + ', ' + \
                        df[df['country'] == 'United States']['state'] + ', ' + \
                        df[df['country'] == 'United States']['country']
        df_us['occurrences'] = df[df['country'] == 'United States']['occurrences']
        df_non_us = pd.DataFrame()
        df_non_us['name'] = df[df['country'] != 'United States']['name'] + ', ' + \
            df[df['country'] != 'United States']['country']
        df_non_us['occurrences'] = df[df['country'] != 'United States']['occurrences']

    df2_us, df2_non_us = worldcities()

    df3 = pd.merge(df_non_us, df2_non_us, on='name', how='left')
    df3_us = pd.merge(df_us, df2_us, on='name', how='left')

    df4 = pd.concat([df3, df3_us], ignore_index=True)

    # Setting up the plot figure
    fig = px.scatter_geo(df4,
                         lat='lat',
                         lon='lng',
                         size='occurrences',
                         hover_name='name',
                         size_max=50,
                         hover_data={'occurrences': True, 'lat': False, 'lng': False},
                         projection='natural earth',
                         title=(f'Cities where "{search_query}" research is concentrated<br><sup>{subtitle}</sup>'
                                if exclude_collaborations < 2
                                else
                                (
                                    f'Cities where {our_org} concentrates its research: '
                                    f'{search_query}<br><sup>{subtitle}</sup>' if exclude_collaborations == 2 else
                                    f'Cities collaborating with {our_org} on: {search_query}<br><sup>{subtitle}</sup>'))
                         )

    fig.update_traces(marker=dict(color='#5E33BF'))

    fig.update_geos(landcolor='#F0F0EB', showcoastlines=False, showcountries=True, countrycolor='#FFFFFF',
                    countrywidth=1)
    fig.show()


# Visualizing the data based on the previously created Excel file
def offline_plotting():
    # Loading the excel file into a dataframe
    search_parameters = pd.read_excel(app.filename_entry.get(), sheet_name='Search Parameters')
    if app.exclude_collaborations_offline.get() == 0:
        try:
            df = pd.read_excel(app.filename_entry.get(), sheet_name='Cities')

            df_us = pd.DataFrame()
            df_us['name'] = df[df['country'] == 'United States']['name'] + ', ' + \
                df[df['country'] == 'United States']['state'] + ', ' + \
                df[df['country'] == 'United States']['country']
            df_us['occurrences'] = df[df['country'] == 'United States']['occurrences']
            df_non_us = pd.DataFrame()
            df_non_us['name'] = df[df['country'] != 'United States']['name'] + ', ' + \
                df[df['country'] != 'United States']['country']
            df_non_us['occurrences'] = df[df['country'] != 'United States']['occurrences']

            df2_us, df2_non_us = worldcities()

            df3 = pd.merge(df_non_us, df2_non_us, on='name', how='left')
            df3_us = pd.merge(df_us, df2_us, on='name', how='left')

            df4 = pd.concat([df3, df3_us], ignore_index=True)

            fig = px.scatter_geo(df4,
                                 lat='lat',
                                 lon='lng',
                                 size='occurrences',
                                 hover_name='name',
                                 size_max=50,
                                 hover_data={'occurrences': True, 'lat': False, 'lng': False},
                                 projection='natural earth',
                                 title=f'Cities where "{search_parameters["Search Query"][0]}" research is concentrated<br>'
                                       f'<sup>{subtitle}</sup>')

            fig.update_traces(marker=dict(color='#5E33BF'))
            fig.update_geos(landcolor='#F0F0EB', showcoastlines=False, showcountries=True, countrycolor='#FFFFFF',
                            countrywidth=1)
            fig.show()
        except ValueError:
            app.filename_bottom_label['text'] = 'Choose whether you need the collaborating cities excluded'

    elif app.exclude_collaborations_offline.get() == 1:
        df_our = pd.read_excel(app.filename_entry.get(), sheet_name='Our Org Cities')

        df_us_our = pd.DataFrame()
        df_us_our['name'] = df_our[df_our['country'] == 'United States']['name'] + ', ' + \
            df_our[df_our['country'] == 'United States']['state'] + ', ' + \
            df_our[df_our['country'] == 'United States']['country']
        df_us_our['occurrences'] = df_our[df_our['country'] == 'United States']['occurrences']
        df_non_us_our = pd.DataFrame()
        df_non_us_our['name'] = df_our[df_our['country'] != 'United States']['name'] + ', ' + \
            df_our[df_our['country'] != 'United States']['country']
        df_non_us_our['occurrences'] = df_our[df_our['country'] != 'United States']['occurrences']

        df2_us, df2_non_us = worldcities()

        df3_our = pd.merge(df_non_us_our, df2_non_us, on='name', how='left')
        df3_us_our = pd.merge(df_us_our, df2_us, on='name', how='left')
        df4_our = pd.concat([df3_our, df3_us_our], ignore_index=True)

        # Setting up the plot figure
        fig = px.scatter_geo(df4_our,
                             lat='lat',
                             lon='lng',
                             size='occurrences',
                             hover_name='name',
                             size_max=50,
                             hover_data={'occurrences': True, 'lat': False, 'lng': False},
                             projection='natural earth',
                             title=(f"Cities where {search_parameters['Our Organization'][0]} concentrates its "
                                    f"research: {search_parameters['Search Query'][0]}<br><sup>{subtitle}</sup>"))

        fig.update_traces(marker=dict(color='#5E33BF'))
        fig.update_geos(landcolor='#F0F0EB', showcoastlines=False, showcountries=True, countrycolor='#FFFFFF',
                        countrywidth=1)
        fig.show()

    elif app.exclude_collaborations_offline.get() == 2:
        df_collab = pd.read_excel(app.filename_entry.get(), sheet_name='Collaborating Cities')

        df_us_collab = pd.DataFrame()
        df_us_collab['name'] = df_collab[df_collab['country'] == 'United States']['name'] + ', ' + \
            df_collab[df_collab['country'] == 'United States']['state'] + ', ' + \
            df_collab[df_collab['country'] == 'United States']['country']
        df_us_collab['occurrences'] = df_collab[df_collab['country'] == 'United States']['occurrences']
        df_non_us_collab = pd.DataFrame()
        df_non_us_collab['name'] = df_collab[df_collab['country'] != 'United States']['name'] + ', ' + \
            df_collab[df_collab['country'] != 'United States']['country']
        df_non_us_collab['occurrences'] = df_collab[df_collab['country'] != 'United States']['occurrences']

        df2_us, df2_non_us = worldcities()

        df3_collab = pd.merge(df_non_us_collab, df2_non_us, on='name', how='left')
        df3_us_collab = pd.merge(df_us_collab, df2_us, on='name', how='left')
        df4_collab = pd.concat([df3_collab, df3_us_collab], ignore_index=True)

        # Setting up the plot figure
        fig = px.scatter_geo(df4_collab,
                             lat='lat',
                             lon='lng',
                             size='occurrences',
                             hover_name='name',
                             size_max=50,
                             hover_data={'occurrences': True, 'lat': False, 'lng': False},
                             projection='natural earth',
                             title=(f"Cities collaborating with {search_parameters['Our Organization'][0]} on: "
                                    f"{search_parameters['Search Query'][0]}<br><sup>{subtitle}</sup>"))

        fig.update_traces(marker=dict(color='#5E33BF'))
        fig.update_geos(landcolor='#F0F0EB', showcoastlines=False, showcountries=True, countrycolor='#FFFFFF',
                        countrywidth=1)
        fig.show()
