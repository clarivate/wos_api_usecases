"""
This code is accepting the Affiliation name and publication years and returns a table of the Web of Science Core
Collection documents affiliated with this organization for the specified period counted both using Whole Counting and
Fractional Counting approach. This data, along with a number of organization's authors per each document is saved
into an Excel table, and the comparison of the organization's output by years using Whole and Fractional counting
methods is also visualized using Plotly.
"""
import requests
import urllib.parse
import threading
import time
import pandas as pd
import plotly.graph_objects as go
import tkinter as tk
from plotly.subplots import make_subplots
from tkinter import ttk, StringVar
from tkinter.filedialog import askopenfilename
from datetime import date


# This function  aggregates the document-level values
def fracount(records, our_org):
    for record in records:
        total_au_input = 0  # Total input of the authors from your org into this paper, it's going to be the numerator
        authors = 0  # Total number of authors in the paper, it's going to be the denominator
        our_authors = 0  # The number of authors from your org, it will be saved into the .csv file for every record
        try:
            pub_year = record['static_data']['summary']['pub_info']['early_access_year']
        except KeyError:
            pub_year = record['static_data']['summary']['pub_info']['pubyear']
        if record['static_data']['fullrecord_metadata']['addresses']['count'] == 1:
            fractional_counting_paper, our_authors = singe_address_record_check(record, authors, our_authors, our_org)
        else:  # Standard case
            fractional_counting_paper, our_authors = standard_case_paper_check(record, authors, total_au_input, our_org)
        frac_counts.append({'UT': record['UID'], 'Publication_year': pub_year,
                            'Our_authors': our_authors, 'Fractional_value': fractional_counting_paper})


# When there is only one affiliation in the paper
def singe_address_record_check(paper, authors, our_authors, our_org):
    authors = single_address_person_check(paper, authors)
    fractional_counting_paper, our_authors = single_address_org_check(paper, authors, our_authors, our_org)
    return fractional_counting_paper, our_authors


# A person may have a status different from an "author", i.e.: "editor". For the purpose of this code,
# we are only using the "author" type
def single_address_person_check(paper, authors):
    if paper['static_data']['summary']['names']['count'] == 1:  # A case when there's only one name on the paper
        if paper['static_data']['summary']['names']['name']['role'] == "author":
            authors = 1
    else:
        for person in paper['static_data']['summary']['names']['name']:
            if person['role'] == "author":
                authors += 1
    return authors


# Checking if the organization profile in the paper belongs to our organization
def single_address_org_check(paper, authors, our_authors, our_org):
    fractional_counting_paper = 0
    try:
        for org in (
                paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec'][
                    'organizations']['organization']
        ):
            if org['content'] == our_org:
                fractional_counting_paper = 1  # If it is - doesn't matter how many authors, the whole paper is counted
                our_authors = authors  # Just for reference, we'll store the number of authors from our org in the csv
            else:
                pass
    except (IndexError, KeyError):  # The chances that this paper won't be linked to your org-enhanced profile are tiny
        pass
        """ You can add the following code instead of "pass" for checking:
        print(f"Record {paper['UID']}: address not linked to an Affiliation:
        {affiliation['address_spec']['organizations']['organization'][0]['content']}")"""
    return fractional_counting_paper, our_authors


# When there are multiple affiliations in the paper (that's where we really need this whole algorithm)
def standard_case_paper_check(paper, authors, total_au_input, our_org):
    if paper['static_data']['summary']['names']['count'] == 1:  # Again, checking if the person is actually an author
        if paper['static_data']['summary']['names']['name']['role'] == "author":
            authors = 1
    else:
        for person in paper['static_data']['summary']['names']['name']:
            if person['role'] == "author":
                authors += 1
    if authors == 0:  # A very rare case when there are no authors in the paper (i.e., only the "group author")
        fractional_counting_paper = 0
        our_authors = 0
    else:
        total_au_input, authors, our_authors = standard_case_address_check(paper, authors, total_au_input, our_org)
        fractional_counting_paper = total_au_input / authors  # Calculating fractional counting for every paper
    return fractional_counting_paper, our_authors


#  Identifying which authors in the paper are affiliated with our organization
def standard_case_address_check(paper, authors, total_au_input, our_org):
    our_authors_seq_numbers = set()  # Building a set of sequence numbers of authors from our org
    try:  # Checking every address in the paper
        for affiliation in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
            for org in affiliation['address_spec']['organizations']['organization']:
                if org['pref'] == 'Y' and org['content'] == our_org:  # Checking every org the address is linked to
                    if affiliation['names']['count'] == 1:  # Filling in the set with our authors' sequence numbers
                        if affiliation['names']['name']['role'] == 'author':
                            our_authors_seq_numbers.add(affiliation['names']['name']['seq_no'])
                    else:
                        for our_author in affiliation['names']['name']:
                            if our_author['role'] == 'author':
                                our_authors_seq_numbers.add(our_author['seq_no'])
    except (IndexError, KeyError,
            TypeError):  # In case the address doesn't contain organization component at all, i.e. street address only
        pass
        """ You can add the following code instead of "pass" for checking:
        print(f"Record {paper['UID']}:
        organization field {affiliation['address_spec']['organizations']['organization'][1]['content']}
        is not linked to any author fields")"""
    our_authors = len(our_authors_seq_numbers)  # The number of our authors in the paper is the length of our set
    if paper['static_data']['summary']['names']['count'] == 1:  # The case when the total number of authors is one
        au_input = 0
        try:
            au_affils = str(paper['static_data']['summary']['names']['name']['addr_no']).split(' ')
            authors = 1
            au_input = standard_case_affiliation_check(paper, au_affils, au_input, our_org)
            total_au_input = au_input
        except KeyError:
            pass  # Very rare cases when there is no link between author and affiliation record
    else:  # The case when the total number of authors is more than one - just calling their affiliations differently
        for author in our_authors_seq_numbers:
            au_input = 0
            au_affils = str(paper['static_data']['summary']['names']['name'][int(author) - 1]['addr_no']).split(' ')
            au_input = standard_case_affiliation_check(paper, au_affils, au_input, our_org)
            total_au_input += au_input  # The total input of our authors is the sum of individual author inputs
    return total_au_input, authors, our_authors


# For every affiliation, a check is made whether it's our organization's affiliation
def standard_case_affiliation_check(paper, au_affils, au_input, our_org):
    for c1 in au_affils:
        try:
            affiliation = (paper['static_data']['fullrecord_metadata']['addresses']['address_name'][int(c1) - 1])
            for org in affiliation['address_spec']['organizations']['organization']:
                if org['pref'] == 'Y' and org['content'] == our_org:
                    au_input += 1 / len(au_affils)
        except (KeyError, IndexError, TypeError):  # In case the address is not linked to an org profile
            pass
            """You can add the following code instead of "pass" for checking:
            print(f"Record {paper['UID']}: address not linked to an Affiliation:
            {paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']['organizations']
            ['organization'][0]['content']}")
            """
    return au_input


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
        f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery=AU=Garfield&count=0&firstRecord=1',
        headers={'X-APIKey': user_apikey}
    )
    if validation_request.status_code == 200:
        # If the API call with this key is a success, we're also return the amount of records remaining
        docs_left = validation_request.headers['X-REC-AmtPerYear-Remaining']
        app.apikey_bottom_label['text'] = f"API Authentication succeeded; Records left to retrieve: {docs_left}"
        return True
    else:
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
            elif records_amount > 100000:
                app.search_query_bottom_label['text'] = (f'Records found: {records_amount}. You can export '
                                                         f'a maximum of 100k records through Expanded API\n')
                return True
            else:
                return True
        else:
            validation_data = validation_request.json()
            error_message = validation_data['message']
            app.search_query_bottom_label['text'] = (f'Request failed with status code '
                                                     f'{validation_request.status_code}\n'
                                                     f'{error_message[error_message.find(": ") + 2:]}')
            return False
    else:
        print('Wrong API Key')
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
            else:
                app.our_org_bottom_label['text'] = f'Please check your Affiliation name'
                return False
        else:
            app.our_org_bottom_label['text'] = f'Please check your Affiliation name'
            return False
    else:
        print('Wrong API Key')
        return False


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
        time.sleep(100)
        wos_api_request(i, search_query, records, requests_required)
    print(f"{((i + 1) * 100) / requests_required:.1f}% complete")
    app.progress_bar.config(value=((i + 1) / requests_required) * 100)
    app.root.update_idletasks()


# This function starts when the "Run" button is clicked and launches all the others
def main_function():
    app.search_button.config(state='disabled', text='Retrieving...')
    if validate_api_key() is False:
        app.apikey_bottom_label['text'] = "Wrong API Key"
        app.search_button.config(state='active', text='Run')
    elif validate_search() is False:
        app.progress_label['text'] = 'Please check your search query'
        app.search_button.config(state='active', text='Run')
    elif validate_affiliation() is False:
        app.search_button.config(state='active', text='Run')
    else:
        our_org = app.our_org_window.get()
        search_query = app.search_query_window.get("1.0", "end-1c")

        # This is the initial API request
        initial_request = requests.get(
            f'https://api.clarivate.com/api/wos?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&count=0&'
            f'firstRecord=1',  headers={'X-APIKey': app.apikey_window.get()}
        )
        data = initial_request.json()
        requests_required = ((data['QueryResult']['RecordsFound'] - 1) // 10) + 1
        records = []

        # From the first response, extracting the total number of records found and calculating the number of requests
        # required. The program can take up to a few dozen minutes, depending on the number of records being analyzed
        for i in range(requests_required):
            wos_api_request(i, search_query, records, requests_required)
        fracount(records, our_org)
        output(our_org, search_query)
        app.search_button.config(state='active', text='Run')
        complete_message = f"Calculation complete. Please check the {our_org} - {date.today()}.xlsx file for results"
        if len(complete_message) > 90:
            if complete_message[:90] == ' ':
                safe_complete_message = f'{complete_message[:90]}\n{complete_message[90:]}'
            else:
                safe_complete_message = f'{complete_message[:90]}-\n{complete_message[90:]}'
        else:
            safe_complete_message = complete_message
        app.progress_label.config(text=safe_complete_message)


# Defining a class through threading so that the interface doesn't freeze when the data is being retrieved through API
class App(threading.Thread):

    def __init__(self,):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        self.root = tk.Tk()
        self.root.iconbitmap('./assets/clarivate.ico')
        self.root.title("Fractional Counting Calculator")
        self.root.geometry("540x500")
        self.root.resizable(False, False)
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        # Modifying certain style elements
        self.style.configure('TNotebook', background='#F0F0EB')
        self.style.map('TNotebook.Tab',
                       foreground=[('focus', '#000000'), ('!focus', '#000000')],
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
        self.style.configure('Horizontal.TProgressbar', font=('Calibri bold', 12), borderwidth=0,
                             troughcolor='#F0F0EB', background='#16AB03', foreground='#16AB03',
                             relief="flat", text='value', troughrelief='flat')

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
        self.search_query_window.insert('1.0', 'OG=Clarivate and PY=2008-2022')
        self.search_validate_button = ttk.Button(self.api_frame, text="Validate", style='Small.TButton',
                                                 command=self.check_search_query)
        self.search_query_bottom_label = ttk.Label(self.api_frame, text='', style='Regular.TLabel')
        self.our_org_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                       text="Affiliation name:")
        self.our_org_window = ttk.Entry(self.api_frame, font=('Calibri', 11))
        self.our_org_window.insert(0, 'Clarivate')
        self.our_org_bottom_label = ttk.Label(self.api_frame,
                                              text='This is the name of the organization that you\'d like to ' \
                                                   'analyze for its fractional output',
                                              style='Regular.TLabel')
        self.search_button = ttk.Button(self.api_frame,
                                        text='Run',
                                        style='Large.TButton',
                                        command=self.run_button)
        self.progress_bar = ttk.Progressbar(self.api_frame, mode="determinate")
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

        self.tabs.place(x=0, y=0, width=540, height=500)
        self.tab1.place(x=0, y=0, width=0, height=0)
        self.tab2.place(x=0, y=0, width=0, height=0)
        self.tabs.add(self.tab1, text='Retrieve via API')
        self.tabs.add(self.tab2, text='Load Excel file')
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

frac_counts = []


# A function for saving the data in an Excel file and for visualizing it with Plotly
def output(our_org, search_query):
    # Saving the collected data to a dataframe
    df = pd.DataFrame(frac_counts)

    # Gathering document counts by years
    df2 = (df[['UT', 'Publication_year']].groupby('Publication_year').count())
    df2.rename(columns={'UT': 'Whole Counting'}, inplace=True)
    df2['Fractional Counting'] = (df[['Fractional_value', 'Publication_year']].groupby('Publication_year').sum())
    df2.reset_index(inplace=True)

    # The results are saved to an Excel file
    safe_our_org = our_org.replace('\"', '').replace('*', '')
    filename = f'fractional counting - {safe_our_org} - {date.today()}'
    if len(filename) > 218:
        safe_filename = filename[:218]
    else:
        safe_filename = filename
    with pd.ExcelWriter(f'{safe_filename}.xlsx') as writer:
        df2.to_excel(writer, sheet_name='Annual Dynamics', index=False)
        df.to_excel(writer, sheet_name='Document-level Data', index=False)

    # Plotting the data on a bar plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df2['Publication_year'], y=df2['Whole Counting'], offset=0.0005, name='Whole Counting',
                         marker=dict(color='#5E33BF')),
                  secondary_y=False)
    fig.add_trace(go.Bar(x=df2['Publication_year'], y=df2['Fractional Counting'], name='Fractional Counting',
                         marker=dict(color='#16AB03')),
                  secondary_y=False)

    fig.update_traces(marker=dict(line=dict(width=3, color='white')))

    # Adding the fractional/whole ratio as a line above the bar plot
    fig.add_trace(go.Scatter(x=df2['Publication_year'], y=(df2['Fractional Counting']/df2['Whole Counting']),
                             line=dict(color="black", width=5),
                             name='Average Fractional Value (Research Involvement)'),
                  secondary_y=True)

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
    fig.update_layout({'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
                      barmode='group',
                      bargroupgap=.5,
                      font_family='Calibri',
                      font_color='#646363',
                      font_size=18,
                      title_font_family='Calibri',
                      title_font_color='#646363',
                      title=f'{safe_plot_title}<br><sup>{safe_plot_subtitle}</sup>',
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


# This function plots the graphs from the files stored locally and doesn't use the API retrieval
def offline_plotting():
    # Saving the collected data to a dataframe
    df = pd.read_excel(app.filename_entry.get(),
                       sheet_name='Annual Dynamics')

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df['Publication_year'], y=df['Whole Counting'], offset=0.0005,
                         name='Whole Counting', marker=dict(color='#5E33BF')),
                  secondary_y=False)
    fig.add_trace(go.Bar(x=df['Publication_year'], y=df['Fractional Counting'], name='Fractional Counting',
                         marker=dict(color='#16AB03')),
                  secondary_y=False)

    fig.update_traces(marker=dict(line=dict(width=3, color='#FFFFFF')))

    # Adding the fractional/whole ratio as a line above the bar plot
    fig.add_trace(go.Scatter(x=df['Publication_year'], y=(df['Fractional Counting'] / df['Whole Counting']),
                             line=dict(color="black", width=5),
                             name='Average Fractional Value (Research Involvement)'),
                  secondary_y=True)

    # Making cosmetic edits to the plot
    plot_title = (str(app.filename_entry.get()).split('/')[-1].split(' - ')[1])
    if len(plot_title) > 100:
        safe_plot_title = f'Whole and Fractional Research Output Comparison for {plot_title[:99]}<br>{plot_title[100:]}'
    else:
        safe_plot_title = f'Whole and Fractional Research Output Comparison for {plot_title}'
    fig.update_layout({'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
                      barmode='group',
                      bargroupgap=.5,
                      font_family='Calibri',
                      font_color='#646363',
                      font_size=18,
                      title_font_family='Calibri',
                      title_font_color='#646363',
                      title=safe_plot_title,
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
