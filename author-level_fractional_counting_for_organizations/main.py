"""
This program is designed to demonstrate the capabilities of the Web of Science Expanded API for
fractional counting analysis. It offers simple graphical user interface. On the RETRIEVE THROUGH
API tab, enter your Web of Science Expanded API key. Then, enter your search query using Web of
Science Advanced Search syntax. Finally, specify which specific affiliation you want the program
to calculate the fractional output for. The program will query retrieve the documents according
to the search query you provided, perform the affiliation-level fractional counting output
calculation, visualize the annual dynamics for both Whole/Full and Fractional counting output
using Plotly package, and save the document-level fractional counting statistics into an Excel
file. You can then reuse the already saved Excel files using the LOAD EXCEL FILE tab.
"""
import urllib.parse
import threading
import time
import tkinter as tk
from tkinter import ttk, StringVar
from tkinter.filedialog import askopenfilename
from datetime import date
import plotly.graph_objects as go
from pandas import DataFrame, ExcelWriter, read_excel
from plotly.subplots import make_subplots
import requests


def fracount(records, our_org, frac_counts):
    """Extract the publication year from the document, check if there is one or multiple
    affiliations in it, and launch one of two address analysis functions based on that,
    then append the results to the frac_count list.

    :param records: list from API JSON.
    :param our_org: str.
    :param frac_counts: list.
    """
    for record in records:
        total_au_input = 0  # Total input of the authors from your org into this paper
        authors = 0  # Total number of authors in the paper
        our_authors = 0  # The number of authors from your org
        try:
            pub_year = record['static_data']['summary']['pub_info']['early_access_year']
        except KeyError:
            pub_year = record['static_data']['summary']['pub_info']['pubyear']
        if record['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
            fractional_counting_paper, our_authors = \
                singe_address_record_check(record, authors, our_authors, our_org)
        else:
            fractional_counting_paper, our_authors = \
                standard_case_paper_check(record, authors, total_au_input, our_org)
        frac_counts.append({'UT': record['UID'],
                            'Publication_year': pub_year,
                            'Our_authors': our_authors,
                            'Fractional_value': fractional_counting_paper})


def singe_address_record_check(paper, authors, our_authors, our_org):
    """When there is only one affiliation in the paper. Just to launch the functions for
    calculating the author numbers and our organization's fractional output for a given
    document.

    :param paper: dict from API JSON.
    :param authors: int representing number of authors in the paper.
    :param our_authors: int representing number of our org's authors in the paper.
    :param our_org: str.
    :return fractional_counting_paper: float.
    :return our_authors: list.
    """
    authors = authors_check(paper, authors)
    fractional_counting_paper, our_authors = \
        single_address_org_check(paper, authors, our_authors, our_org)
    return fractional_counting_paper, our_authors


def authors_check(paper, authors):
    """Calculate the value of the authors in the document

    :param paper: dict.
    :param authors: int.
    :return: int, updated.
    """
    if paper['static_data']['summary']['names']['count'] == 1:
        if paper['static_data']['summary']['names']['name']['role'] == "author":
            authors = 1
    else:
        for person in paper['static_data']['summary']['names']['name']:
            if person['role'] == "author":
                authors += 1
    return authors


def single_address_org_check(paper, authors, our_authors, our_org):
    """Calculate the number of our organization's authors as well as our organization's fractional
     output for this particular document

    :param paper: dict from API JSON.
    :param authors: int representing number of authors in the paper.
    :param our_authors: int representing number of our org's authors in the paper.
    :param our_org: str.
    :return fractional_counting_paper: float.
    :return our_authors: list.
    """
    fractional_counting_paper = 0
    try:
        for org in (
                paper['static_data']['fullrecord_metadata']['addresses']['address_name']
                ['address_spec']['organizations']['organization']
        ):
            if org['content'].lower() == our_org.lower():
                fractional_counting_paper = 1
                our_authors = authors
            else:
                pass
    except (IndexError, KeyError):
        pass
    return fractional_counting_paper, our_authors


def standard_case_paper_check(paper, authors, total_au_input, our_org):
    """Check for a rare case when the number of authors in the document is 0, launch the
    standard_case_address_check function, calculate the fractional counting value for the document
    from the total_au_input and authors values returned by that function.

    :param paper: dict from API JSON.
    :param authors: int representing number of authors in the paper.
    :param total_au_input: float representing total authors' input into this research.
    :param our_org: str.
    :return fractional_counting_paper: float.
    :return our_authors: list.
    """
    authors = authors_check(paper, authors)
    # A very rare case when there are no authors in the paper (i.e., only the "group author")
    if authors == 0:
        fractional_counting_paper = 0
        our_authors = 0
    else:
        total_au_input, authors, our_authors = \
            standard_case_address_check(paper, authors, total_au_input, our_org)
        fractional_counting_paper = total_au_input / authors
    return fractional_counting_paper, our_authors


def standard_case_address_check(paper, authors, total_au_input, our_org):
    """Figure out who of the authors are affiliated with our organization, launch the
    standard_case_affiliation_check function, calculate the total author input value from
    individual author input values returned by it.

    :param paper: dict from API JSON.
    :param authors: int representing number of authors in the paper.
    :param total_au_input: float representing total authors' input into this research.
    :param our_org: str.
    :return total_au_input: float.
    :return authors: int.
    :return our_authors: list.
    """
    our_authors_seq_numbers = set()
    try:
        for affiliation in paper['static_data']['fullrecord_metadata']['addresses']\
                ['address_name']:
            for org in affiliation['address_spec']['organizations']['organization']:
                if org['pref'] == 'Y' and org['content'].lower() == our_org.lower() and \
                        affiliation['names']['count'] == 1 and \
                        affiliation['names']['name']['role'] == 'author':
                    # Filling in the set with our authors' sequence numbers
                    our_authors_seq_numbers.add(affiliation['names']['name']['seq_no'])
                elif org['pref'] == 'Y' and org['content'].lower() == our_org.lower() and \
                                    affiliation['names']['count'] > 1:
                    for our_author in affiliation['names']['name']:
                        if our_author['role'] == 'author':
                            our_authors_seq_numbers.add(our_author['seq_no'])
    except (IndexError, KeyError, TypeError):
        # When the address doesn't contain organization component at all, i.e. street address only
        pass
    our_authors = len(our_authors_seq_numbers)
    if paper['static_data']['summary']['names']['count'] == 1:
        au_input = 0
        try:
            au_affils = str(paper['static_data']['summary']['names']['name']['addr_no']).split(' ')
            authors = 1
            au_input = standard_case_affiliation_check(paper, au_affils, au_input, our_org)
            total_au_input = au_input
        except KeyError:
            # Very rare cases when there is no link between author and affiliation record
            pass
    else:
        for author in our_authors_seq_numbers:
            au_input = 0
            au_affils = str(paper['static_data']['summary']['names']['name'][int(author) - 1]
                            ['addr_no']).split(' ')
            au_input = standard_case_affiliation_check(paper, au_affils, au_input, our_org)
            total_au_input += au_input
    return total_au_input, authors, our_authors


def standard_case_affiliation_check(paper, au_affils, au_input, our_org):
    """For every affiliation, check if it's our organization's affiliation, and calculate the
    individual author's inputs (or, in other words, their fractional values of the document).

    :param paper: dict from API JSON.
    :param au_affils: list of strs representing authors' affiliations.
    :param au_input: float representing individual authors' input into this research.
    :param our_org: str.
    :return au_input: float, updated.
    """

    for c_1 in au_affils:
        try:
            affiliation = (paper['static_data']['fullrecord_metadata']['addresses']
                           ['address_name'][int(c_1) - 1])
            for org in affiliation['address_spec']['organizations']['organization']:
                if org['pref'] == 'Y' and org['content'].lower() == our_org.lower():
                    au_input += 1 / len(au_affils)
        except (KeyError, IndexError, TypeError):
            # When the address is not linked to an org profile
            pass
    return au_input


def format_line(text, line_start, symbol_limit, safe_text):
    """Format the text lines for the function below.

    :param text: str to format.
    :param line_start: int, the index of the character that starts the line.
    :param symbol_limit: int, the maximum number of characters per line.
    :param safe_text: str prepared for the output.

    :return safe_text: str, updated.
    :return line_end: int, the index of the character that ends the line.
    """
    if line_start + symbol_limit > len(text):
        safe_text += f'{text[line_start:len(text)]}\n'
        return safe_text, line_start
    for i in range(symbol_limit):
        if text[(line_start + symbol_limit) - i] == ' ':
            line_end = line_start + symbol_limit - i + 1
            safe_text += f'{text[line_start:line_end]}\n'
            return safe_text, line_end


def format_label_text(text, symbol_limit):
    """Wrap words in longer messages.

    :param text: str to format.
    :param symbol_limit: int, the maximum number of characters per line.
    :return: str.
    """
    safe_text = ''
    line_start = 0
    if len(text) > symbol_limit:
        lines_amount = (len(text) // symbol_limit) + 1
        for i in range(lines_amount):
            safe_text, line_start = format_line(text, line_start, symbol_limit, safe_text)
        return safe_text
    return text


def unhide_symbols():
    """Hide/unhide symbols in the API Key field.

    """
    if app.apikey_window['show'] == "*":
        app.apikey_window['show'] = ""
    else:
        app.apikey_window['show'] = "*"


def validate_api_key():
    """Check the validity of the API key

    """
    user_apikey = app.apikey_window.get()
    validation_request = requests.get(
        'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery=AU=Garfield&count=0&'
        'firstRecord=1', headers={'X-APIKey': user_apikey}
    )
    if validation_request.status_code == 200:
        # If the API call is a success, we'll also return the amount of records remaining
        docs_left = validation_request.headers['X-REC-AmtPerYear-Remaining']
        app.apikey_bottom_label['text'] = f"API Authentication succeeded; Records left to " \
                                          f"retrieve: {docs_left}"
        return True
    app.apikey_bottom_label['text'] = "Wrong API Key"
    return False


def validate_search():
    """Check how many results the search query returns

    """
    if validate_api_key():
        user_apikey = app.apikey_window.get()
        search_query = app.search_query_window.get("1.0", "end-1c")
        validation_request = requests.get(
            f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery='
            f'{urllib.parse.quote(search_query)}&'
            f'count=0&firstRecord=1', headers={'X-APIKey': user_apikey})
        validation_data = validation_request.json()
        if validation_request.status_code == 200:
            docs_left = validation_request.headers['X-REC-AmtPerYear-Remaining']
            app.apikey_bottom_label['text'] = f"API Authentication succeeded; Records left to " \
                                              f"retrieve: {docs_left}"
            records_amount = validation_data['QueryResult']['RecordsFound']
            app.search_query_bottom_label['text'] = f'Records found: {records_amount} \n '
            if records_amount == 0:
                return False
            if records_amount > 100000:
                app.search_query_bottom_label['text'] = (f'Records found: {records_amount}. You '
                                                         f'can export a maximum of 100k records '
                                                         f'through Expanded API\n')
                return True
            return True
        error_message = validation_data['message']
        if error_message == 'Invalid authentication credentials':
            app.apikey_bottom_label['text'] = "Wrong API Key"
        else:
            error_message_text = validation_data['message'][validation_data['message'].find(": ")
                                                            + 2:]
            app.search_query_bottom_label['text'] = (f'Request failed with status code '
                                                     f'{validation_request.status_code}\n'
                                                     f'{format_label_text(error_message_text, 94)}')
        return False
    return False


def validate_affiliation():
    """Make sure the affiliation name provided by the user is a valid one.

    """
    if validate_api_key():
        user_apikey = app.apikey_window.get()
        search_query = f'OG={app.our_org_window.get()}'
        validation_request = requests.get(f'https://api.clarivate.com/api/wos?databaseId=WOS&'
                                          f'usrQuery={urllib.parse.quote(search_query)}&count=0&'
                                          f'firstRecord=1', headers={'X-APIKey': user_apikey})
        if validation_request.status_code == 200:
            validation_data = validation_request.json()
            records_amount = validation_data['QueryResult']['RecordsFound']
            if records_amount > 0:
                return True
            app.our_org_bottom_label['text'] = 'Please check your Affiliation name'
            return False
        app.our_org_bottom_label['text'] = 'Please check your Affiliation name'
        return False
    return False


def wos_api_request(i, search_query, records, requests_required):
    """Send the API requests to retrieve the data.

    :param i: int, number of current request .
    :param search_query: str.
    :param records: list
    :param requests_required: int over which i is iterated.
    """
    subsequent_response = requests.get(
        f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery='
        f'{urllib.parse.quote(search_query)}&count=10&firstRecord={i}1',
        headers={'X-APIKey': app.apikey_window.get()}
    )
    data = subsequent_response.json()
    try:
        for wos_record in data['Data']['Records']['records']['REC']:
            records.append(wos_record)
    # This is to prevent certain occasional connection problems
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending WoS API request #{i + 1}')
        time.sleep(100)
        wos_api_request(i, search_query, records, requests_required)
    print(f"{((i + 1) * 100) / requests_required:.1f}% complete")
    progress = ((i + 1) / requests_required) * 100
    app.progress_bar.config(value=progress)
    app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
    app.root.update_idletasks()


def main_function():
    """Launch all the other functions after "Run" button is pressed.

    """
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
    if validate_affiliation() is False:
        app.search_button.config(state='active', text='Run')
        return False
    frac_counts = []
    our_org = app.our_org_window.get()
    if app.progress_label['text'] == 'Please check your search query':
        app.progress_label['text'] = ''
    search_query = app.search_query_window.get("1.0", "end-1c")

    # This is the initial API request
    initial_request = requests.get(
        f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery='
        f'{urllib.parse.quote(search_query)}&count=0&firstRecord=1',
        headers={'X-APIKey': app.apikey_window.get()}
    )
    data = initial_request.json()
    requests_required = ((data['QueryResult']['RecordsFound'] - 1) // 10) + 1
    records = []

    # From the first response, extracting the total number of records found and calculating the
    # number of requests required. The program can take up to a few dozen minutes, depending on
    # the number of records being analyzed
    for i in range(requests_required):
        wos_api_request(i, search_query, records, requests_required)
    fracount(records, our_org, frac_counts)
    output(our_org, search_query, frac_counts)
    app.search_button.config(state='active', text='Run')
    complete_message = f"Calculation complete. Please check the {our_org} - {date.today()}.xlsx " \
                       f"file for results"
    app.progress_label['text'] = format_label_text(complete_message, 94)


class App(threading.Thread):
    """Represents an app interface. Required as a separate class so that the interface doesn't
    freeze when the data is being retrieved through API.

    """

    def __init__(self,):
        threading.Thread.__init__(self)
        self.root = None
        self.style = None
        self.tabs = None
        self.tab1 = None
        self.tab2 = None
        self.api_frame = None
        self.apikey_top_label = None
        self.apikey_window = None
        self.apikey_button = None
        self.unhide_image = None
        self.apikey_unhide_button = None
        self.apikey_validate_button = None
        self.apikey_bottom_label = None
        self.search_query_label = None
        self.search_query_window = None
        self.search_validate_button = None
        self.search_query_bottom_label = None
        self.search_button = None
        self.our_org_label = None
        self.our_org_window = None
        self.our_org_bottom_label = None
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

        # Setting up style and geometry
        self.root.iconbitmap('./assets/clarivate.ico')
        self.root.title("Fractional Counting Calculator")
        self.root.geometry("540x500")
        self.root.resizable(False, False)
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.style.configure('TNotebook', background='#F0F0EB')
        self.style.configure('TNotebook.Tab', font=('Calibri bold', 12))
        self.style.map('TNotebook.Tab',
                       foreground=[('active', '#5E33BF'), ('!active', '#000000')],
                       background=[('selected', '#FFFFFF'), ('!selected', '#F0F0EB')],
                       focuscolor=[('selected', '#FFFFFF')])
        self.style.configure('Bold.TLabel', font=('Calibri bold', 12), borderwidth=0,
                             bordercolor='#000000', selectborderwidth=0)
        self.style.configure('White.TFrame', background='#FFFFFF')
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
        # We had to borrow the horizontal progressbar from the Default scheme in order to remove
        # one extra frame around the progress bar
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
        self.style.configure('Clarivate.Horizontal.TProgressbar', font=('Calibri bold', 12),
                             borderwidth=0, troughcolor='#F0F0EB', background='#16AB03',
                             foreground='#000000', text='', anchor='center')

        # Setting up widgets
        self.tabs = ttk.Notebook(self.root)
        self.tab1 = ttk.Frame(self.tabs, style='White.TFrame')
        self.tab2 = ttk.Frame(self.tabs, style='White.TFrame')

        self.api_frame = ttk.Frame(self.tab1, style='White.TFrame')
        apikey = StringVar()
        self.apikey_top_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                          text="Web of Science Expanded API Key:")
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
        self.search_query_bottom_label = ttk.Label(self.api_frame, text='', style='Regular.TLabel')
        self.our_org_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                       text="Affiliation name:")
        self.our_org_window = ttk.Entry(self.api_frame, font=('Calibri', 11))
        self.our_org_window.insert(0, 'Clarivate')
        self.our_org_bottom_label = ttk.Label(self.api_frame,
                                              text='This is the name of the organization that '
                                                   'you\'d like to analyze for its fractional '
                                                   'output',
                                              style='Regular.TLabel')
        self.search_button = ttk.Button(self.api_frame,
                                        text='Run',
                                        style='Large.TButton',
                                        command=self.run_button)
        self.progress_bar = ttk.Progressbar(self.api_frame,
                                            style='Clarivate.Horizontal.TProgressbar',
                                            mode="determinate")
        self.progress_label = ttk.Label(self.api_frame, style='Regular.TLabel')
        self.offline_frame = ttk.Frame(self.tab2, style='White.TFrame')
        self.offline_label = ttk.Label(self.offline_frame,
                                       style='Regular.TLabel',
                                       text='Here you can simply load a previously saved Excel '
                                            'file and draw a trend graph from it.\n')
        self.filename_label = ttk.Label(self.offline_frame, style='Bold.TLabel',
                                        text='Select file:')
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
        # Placing widgets
        self.tabs.place(x=0, y=0, width=540, height=500)
        self.tab1.place(x=0, y=0, width=0, height=0)
        self.tab2.place(x=0, y=0, width=0, height=0)
        self.tabs.add(self.tab1, text='             RETRIEVE THROUGH API             ')
        self.tabs.add(self.tab2, text='               LOAD EXCEL FILE                 ')
        self.api_frame.place(x=0, y=0, width=540, height=480)
        self.apikey_top_label.place(x=5, y=5, width=535, height=24)
        self.apikey_window.place(x=5, y=29, width=400, height=30)
        self.apikey_unhide_button.place(x=406, y=29, width=30, height=30)
        self.apikey_button.place(x=440, y=29, width=90, height=30)
        self.apikey_bottom_label.place(x=5, y=59, width=400, height=24)
        self.search_query_label.place(x=5, y=89, width=400, height=24)
        self.search_query_window.place(x=5, y=113, width=400, height=90)
        self.search_validate_button.place(x=410, y=113, width=120, height=30)
        self.search_query_bottom_label.place(x=5, y=203, width=500, height=40)
        self.our_org_label.place(x=5, y=251, width=400, height=30)
        self.our_org_window.place(x=5, y=281, width=400, height=30)
        self.our_org_bottom_label.place(x=5, y=311, width=500, height=24)
        self.search_button.place(x=220, y=350, width=100, height=35)
        self.progress_bar.place(x=5, y=400, width=525, height=30)
        self.progress_label.place(x=5, y=430, width=525, height=40)
        self.offline_frame.place(x=0, y=0, width=540, height=430)
        self.offline_label.place(x=5, y=0, width=535, height=50)
        self.filename_label.place(x=5, y=65, width=535, height=24)
        self.filename_entry.place(x=5, y=89, width=495, height=30)
        self.open_file_button.place(x=502, y=89, width=30, height=30)
        self.draw_graph_button.place(x=220, y=150, width=100, height=35)

        self.root.mainloop()

    def check_api_key(self):
        threading.Thread(target=validate_api_key).start()

    def check_search_query(self):
        threading.Thread(target=validate_search).start()

    def run_button(self):
        threading.Thread(target=main_function).start()

    def file_menu(self):
        self.file_name.set(askopenfilename(initialdir='./', filetypes=[("Excel files", "*.xlsx")]))

    def draw_graph(self):
        threading.Thread(target=offline_plotting).start()


app = App()


def build_graph(dataframe):
    """Prepare subplots, fill them with bars and a line

    :param dataframe: pandas DataFrame object.
    :return fig: plotly Figure object.
    """
    # Plotting the data on a bar plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=dataframe['Publication_year'],
                         y=dataframe['Whole Counting'],
                         offset=0.0005,
                         name='Whole Counting',
                         marker=dict(color='#5E33BF')),
                  secondary_y=False)
    fig.add_trace(go.Bar(x=dataframe['Publication_year'],
                         y=dataframe['Fractional Counting'],
                         name='Fractional Counting',
                         marker=dict(color='#16AB03')),
                  secondary_y=False)

    fig.update_traces(marker=dict(line=dict(width=3, color='white')))

    # Adding the fractional/whole ratio as a line above the bar plot
    fig.add_trace(go.Scatter(x=dataframe['Publication_year'],
                             y=(dataframe['Fractional Counting'] / dataframe['Whole Counting']),
                             line=dict(color="black", width=5),
                             name='Average Fractional Value (Research Involvement)'),
                  secondary_y=True)
    return fig


def beautify_graph(fig, title):
    """Add Clarivate colors to the graph, update layout with the title.

    :param fig: plotly Figure object.
    :param title: str.
    """
    fig.update_layout({'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
                      barmode='group',
                      bargroupgap=.5,
                      font_family='Calibri',
                      font_color='#646363',
                      font_size=18,
                      title_font_family='Calibri',
                      title_font_color='#646363',
                      title=title,
                      legend_title_text=None,
                      legend=dict(
                          yanchor="bottom",
                          y=-0.4,
                          xanchor="center",
                          x=0.5
                      ))
    fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C', secondary_y=False)
    fig.update_yaxes(range=[0, 1], showgrid=False, tickformat=',.0%', secondary_y=True)
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

    fig.show()


def output(our_org, search_query, frac_counts):
    """Save the retrieved data in an Excel file and visualize it with Plotly.

    :param our_org: str.
    :param search_query: str.
    :param frac_counts: list.
    """
    # Saving the collected data to a dataframe
    df = DataFrame(frac_counts)

    # Gathering document counts by years
    df2 = (df[['UT', 'Publication_year']].groupby('Publication_year').count())
    df2.rename(columns={'UT': 'Whole Counting'}, inplace=True)
    df2['Fractional Counting'] = (df[['Fractional_value', 'Publication_year']].
                                  groupby('Publication_year').sum())
    df2.reset_index(inplace=True)

    # The results are saved to an Excel file
    safe_our_org = our_org.replace('\"', '').replace('*', '')
    filename = f'fractional counting - {safe_our_org} - {date.today()}'
    if len(filename) > 218:
        safe_filename = filename[:218]
    else:
        safe_filename = filename
    # Safe saving - as openpyxl module won't allow to open the file if it's already open
    try:
        with ExcelWriter(f'{safe_filename}.xlsx') as writer:
            df2.to_excel(writer, sheet_name='Annual Dynamics', index=False)
            df.to_excel(writer, sheet_name='Document-level Data', index=False)
    except PermissionError:
        i = 2
        while i < 10:
            try:
                with ExcelWriter(f'{safe_filename} ({i}).xlsx') as writer:
                    df2.to_excel(writer, sheet_name='Annual Dynamics', index=False)
                    df.to_excel(writer, sheet_name='Document-level Data', index=False)
                    break
            except PermissionError:
                i += 1

    graph = build_graph(df2)

    # Making cosmetic edits to the plot
    plot_title = f'Whole and Fractional Research Output Comparison for {our_org}'
    plot_subtitle = f'<br><sup>Search query: {search_query}</sup>'
    if len(plot_title) > 100:
        safe_plot_title = f'{plot_title[:100]}...'
    else:
        safe_plot_title = plot_title
    if len(plot_subtitle) > 200:
        safe_plot_subtitle = f'{plot_subtitle[:200]}...'
    else:
        safe_plot_subtitle = plot_subtitle
    joined_titles = f'{safe_plot_title}<br><sup>{safe_plot_subtitle}</sup>'
    beautify_graph(graph, joined_titles)


def offline_plotting():
    """Plot the graphs from the files stored locally without the API retrieval.

    """
    # Loading the excel file into a dataframe
    df = read_excel(app.filename_entry.get(), sheet_name='Annual Dynamics')

    graph = build_graph(df)

    # Making cosmetic edits to the plot
    plot_title = (str(app.filename_entry.get()).split('/')[-1].split(' - ')[1])
    if len(plot_title) > 100:
        safe_plot_title = f'Whole and Fractional Research Output Comparison for ' \
                          f'{plot_title[:99]}<br>{plot_title[100:]}'
    else:
        safe_plot_title = f'Whole and Fractional Research Output Comparison for {plot_title}'
    beautify_graph(graph, safe_plot_title)
