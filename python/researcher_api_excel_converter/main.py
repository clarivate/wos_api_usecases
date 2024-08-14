import requests
import threading
import urllib.parse
import time
import pandas as pd
import tkinter as tk
from tkinter import ttk, BooleanVar, IntVar
from datetime import date


# Getting the necessary metadata fields from the data obtained by the API
def fetch_researchers_data(data, researchers):
    for record in data['hits']:
        researchers.append({
            'rid': record['rid'][0],
            'fullname': record['fullName'],
            'primary_affiliation': ", ".join(record['primaryAffiliation']),
            'link': record['self'],
            'h-index': record['hIndex'],
            'documents_count': record['documentsCount']['count'],
            'documents_count_link': record['documentsCount']['self'],
            'times_cited': record['totalTimesCited'],
        })


# Getting full reearcher profile data through individual researcher API calls
def fetch_full_researchers_data(data, researcher):
    researcher['orcid'] = '; '.join(data['ids']['orcids'])
    researcher['claim_status'] = data['claimStatus']
    researcher['first_name'] = data['name']['firstName']
    researcher['last_name'] = data['name']['lastName']
    altnames = []
    for altname in data['name']['alternativeNames']:
        altnames.append(altname['name'])
    researcher['alt_names'] = '; '.join(altnames)
    researcher['published_years'] = {}
    for published_year in data['metricsAllTime']['documents']['publishedYears']:
        researcher['published_years'][published_year['year']] = published_year['numberOfDocuments']
    researcher['citing_publications'] = data['metricsAllTime']['totalCitingPublications']
    researcher['citing_publications_excluding_self'] = data['metricsAllTime']['totalCitingWithoutSelf']
    researcher['times_cited_excluding_self'] = data['metricsAllTime']['totalTimesCitedWithoutSelf']
    primary_org_addresses = []
    primary_org_countries = []
    for primary_org in data['organization']['primaryAffiliation']:
        primary_org_addresses.append(primary_org['address'])
        primary_org_countries.append(primary_org['country'])
    researcher['primary_org_addresses'] = '; '.join(primary_org_addresses)
    researcher['primary_org_countries'] = '; '.join(primary_org_countries)
    departments = []
    for department in data['organization']['departments']:
        departments.append(department)
    researcher['departments'] = '; '.join(departments)
    researcher['affiliations'] = {}
    for i in range(len(data['organization']['affiliations'])):
        researcher['affiliations'][i] = {}
        researcher['affiliations'][i]['start_year'] = data['organization']['affiliations'][i]['startYear']
        researcher['affiliations'][i]['end_year'] = data['organization']['affiliations'][i]['endYear']
        researcher['affiliations'][i]['organization'] = data['organization']['affiliations'][i]['organization']
        researcher['affiliations'][i]['num_docs'] = data['organization']['affiliations'][i]['numberOfDocuments']
    researcher['author_position_first'] = data['authorPosition']['first']['numberOfDocuments']
    researcher['author_position_last'] = data['authorPosition']['last']['numberOfDocuments']
    researcher['author_position_corresponding'] = data['authorPosition']['corresponding']['numberOfDocuments']


# A function for hiding/unhiding symbols in the API Key field
def unhide_symbols():
    if app.apikey_window['show'] == "*":
        app.apikey_window['show'] = ""
    else:
        app.apikey_window['show'] = "*"


# A function that checks the existing search query vs the daily API threshold. Launched each time the checkbutton is
# checked/unchecked
def check_vs_limits():
    researcher_profiles_found = app.researcher_profiles_found.get()
    search_requests_required = app.search_requests_required.get()
    requests_left = app.requests_left.get()
    if app.retrieve_full_profile_data.get() and (researcher_profiles_found + search_requests_required) > requests_left:
        app.our_org_bottom_label['text'] = f"Researcher Profiles found: {researcher_profiles_found}\n" \
                                           f"Warning: this would require " \
                                           f"{researcher_profiles_found + search_requests_required} API " \
                                           f"requests to retrieve, you only have {requests_left} remaining \ntoday."
        app.search_button.config(state='disabled', text='Run')
    elif app.retrieve_full_profile_data.get() == 0 and search_requests_required > requests_left:
        app.our_org_bottom_label['text'] = f"Researcher Profiles found: {researcher_profiles_found}\n" \
                                           f"Warning: this would require " \
                                           f"{researcher_profiles_found + search_requests_required} API " \
                                           f"requests to retrieve, you only have {requests_left} remaining \ntoday."
        app.search_button.config(state='disabled', text='Run')
    elif app.retrieve_full_profile_data.get() and (researcher_profiles_found + search_requests_required) <= \
            requests_left and researcher_profiles_found > 0:
        app.our_org_bottom_label['text'] = f"Researcher Profiles found: {researcher_profiles_found}\n\n"
        app.search_button.config(state='active', text='Run')
    elif app.retrieve_full_profile_data.get() == 0 and search_requests_required <= requests_left and \
            researcher_profiles_found > 0:
        app.our_org_bottom_label['text'] = f"Researcher Profiles found: {researcher_profiles_found}\n\n"
        app.search_button.config(state='active', text='Run')
    elif researcher_profiles_found == 0 and search_requests_required > 0 and requests_left > 0:
        app.our_org_bottom_label['text'] = f'Please check your Affiliation name\n\n'
    else:
        pass


# A function for checking the validity of the API key
def validate_api_key():
    user_apikey = app.apikey_window.get()
    validation_request = requests.get(
        f'https://api.clarivate.com/apis/wos-researcher/researchers?q=Lastname~"Garfield"&limit=1&page=1',
        headers={'X-APIKey': user_apikey}
    )
    if validation_request.status_code == 200:
        # If the API call with this key is a success, we're also return the amount of records remaining
        requests_left = validation_request.headers['X-RateLimit-Remaining-Day']
        if int(requests_left) < 100:
            app.apikey_bottom_label['text'] = f"API authentication succeeded; Requests left today: {requests_left}"
        else:
            app.apikey_bottom_label['text'] = f"API authentication succeeded"
        return True
    else:
        app.apikey_bottom_label['text'] = "Wrong API Key"
        return False


# A function to make sure the affiliation name provided by the user is a valid one
def validate_affiliation():
    user_apikey = app.apikey_window.get()
    our_org = app.our_org_window.get()
    validation_request = requests.get(f'https://api.clarivate.com/apis/wos-researcher/researchers?q=OG~'
                                      f'"{urllib.parse.quote(our_org)}"&page=1&limit=50',
                                      headers={'X-APIKey': user_apikey})
    if validation_request.status_code == 200:
        validation_data = validation_request.json()
        requests_left = int(validation_request.headers['X-RateLimit-Remaining-Day'])
        researcher_profiles_found = int(validation_data['metadata']['total'])
        search_requests_required = ((researcher_profiles_found - 1) // 50) + 1
        if app.retrieve_full_profile_data.get():
            app.requests_left.set(requests_left)
            app.researcher_profiles_found.set(researcher_profiles_found)
            app.search_requests_required.set(search_requests_required)
            if requests_left < 1000:
                app.apikey_bottom_label['text'] = f"API Authentication succeeded; Requests left today: {requests_left}"
            else:
                app.apikey_bottom_label['text'] = f"API Authentication succeeded"
            if (researcher_profiles_found + search_requests_required) > requests_left:
                app.our_org_bottom_label['text'] = f"Researcher Profiles found: {researcher_profiles_found}\n" \
                                                   f"Warning: this would require " \
                                                   f"{researcher_profiles_found + search_requests_required} API " \
                                                   f"requests to retrieve, you only have {requests_left} remaining\n" \
                                                   f"today."
                app.search_button.config(state='disabled', text='Run')
                return researcher_profiles_found
            elif (researcher_profiles_found + search_requests_required) <= requests_left and \
                    researcher_profiles_found > 0:
                app.our_org_bottom_label['text'] = f"Researcher Profiles found: {researcher_profiles_found}\n\n"
                app.search_button.config(state='active', text='Run')
                return researcher_profiles_found
            else:
                app.our_org_bottom_label['text'] = f'Please check your Affiliation name\n\n'
                return False
        else:
            app.requests_left.set(requests_left)
            app.researcher_profiles_found.set(researcher_profiles_found)
            app.search_requests_required.set(search_requests_required)
            if requests_left < 1000:
                app.apikey_bottom_label['text'] = f"API Authentication succeeded; Requests left today: {requests_left}"
            else:
                app.apikey_bottom_label['text'] = f"API Authentication succeeded"
            if app.researcher_profiles_found.get() > 0:
                app.our_org_bottom_label['text'] = f"Researcher Profiles found: {researcher_profiles_found}\n\n"
                app.search_button.config(state='active', text='Run')
                return researcher_profiles_found
            else:
                app.our_org_bottom_label['text'] = f'Please check your Affiliation name\n\n'
                return False
    else:
        app.our_org_bottom_label['text'] = f'Please check your Affiliation name\n\n'
        return False


# Sending the API requests to the server
def researcher_api_request(i, requests_required, our_org, researchers):
    try:
        request = requests.get(f'https://api.clarivate.com/apis/wos-researcher/researchers?q=OG~'
                               f'"{urllib.parse.quote(our_org)}"&page={i + 1}&limit=50',
                               headers={'X-APIKey': app.apikey_window.get()})
        data = request.json()
        fetch_researchers_data(data, researchers)
    except(requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending Researcher API request #{i + 1}')
        time.sleep(1)
        researcher_api_request(i, requests_required, our_org, researchers)


# Sending requests to individual researcher profiles to get the full data
def individual_profile_api_request(researcher, researchers):
    try:
        request = requests.get(f'https://api.clarivate.com/apis/wos-researcher/researchers/'
                               f'{researcher["rid"]}', headers={'X-APIKey': app.apikey_window.get()})
        data = request.json()
        fetch_full_researchers_data(data, researcher)
    except(requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
        print(f'Resending individual researcher profile {researcher["rid"]}request #{researchers.index(researcher)}')
        time.sleep(1)
        individual_profile_api_request(researcher, researchers)


# The main function that launches all the others
def main_function():
    app.search_button.config(state='disabled', text='Retrieving...')
    app.progress_label['text'] = ''
    researcher_profiles_found = validate_affiliation()
    if researcher_profiles_found is False:
        app.search_button.config(state='active', text='Run')
    else:
        if app.progress_label['text'] == 'Please check your search query':
            app.progress_label['text'] = ''
        our_org = app.our_org_window.get()
        requests_required = ((researcher_profiles_found - 1) // 50) + 1
        researchers = []
        for i in range(requests_required):
            researcher_api_request(i, requests_required, our_org, researchers)
            if app.retrieve_full_profile_data.get():
                progress = ((i + 1) / (requests_required + researcher_profiles_found)) * 100
            else:
                progress = ((i + 1) / requests_required) * 100
            print(f'{progress:.1f}% complete')
            app.progress_bar.config(value=progress)
            app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
            app.root.update_idletasks()
        if app.retrieve_full_profile_data.get():
            for researcher in researchers:
                individual_profile_api_request(researcher, researchers)
                progress = ((requests_required + researchers.index(researcher) + 1) /
                            (requests_required + researcher_profiles_found)) * 100
                print(f'{progress:.1f}% complete')
                app.progress_bar.config(value=progress)
                app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
                app.root.update_idletasks()
        output(researchers, our_org)
        app.search_button.config(state='active', text='Run')
        complete_message = f"Retrieval complete. Please check the 'researchers - {our_org} - {date.today()}.xlsx' " \
                           f"file for results"
        if len(complete_message) > 97:
            if complete_message[97] == ' ' or complete_message[98] == ' ':
                safe_complete_message = f'{complete_message[:97]}\n{complete_message[97:]}'
            else:
                safe_complete_message = f'{complete_message[:97]}-\n{complete_message[97:]}'
        else:
            safe_complete_message = complete_message
        app.progress_label['text'] = safe_complete_message


# Saving the data into an excel file
def output(researchers, our_org):
    df = pd.DataFrame(data=researchers)

    # Making a few manipulations to the data - hiding the documents API link and the profiles API link, adding a WoS UI
    # profile link
    df = df.drop(['link', 'documents_count_link'], axis=1)
    df['wos_platform_link'] = 'https://www.webofscience.com/wos/author/record/' + df['rid']
    df['rid'] = df['rid'] + ' '

    if app.retrieve_full_profile_data.get():
        df2 = pd.concat([df['rid'], df['fullname'], df['published_years'].apply(pd.Series)], axis=1)
        df3 = pd.concat([df['rid'], df['fullname'], df['affiliations'].apply(pd.Series)], axis=1)
        temp_dfs = []
        for col in df3.columns:
            if col != 'rid':
                temp_dfs.append(pd.concat((df3['rid'], df['fullname'], df3[col].apply(pd.Series)), axis=1))
        df4 = temp_dfs[0]
        for i in range(1, len(temp_dfs)):
            df4 = pd.concat((df4, temp_dfs[i]), axis=0)
        df4 = df4.drop(0, axis=1)
        df4 = df4.dropna(axis=0)
        df4 = df4.sort_values(['rid'])
        base_columns = ['rid', 'fullname']
        years_columns = [col for col in df2.columns if col not in base_columns]
        sorted_years = sorted(years_columns, key=lambda x: x)
        df2 = df2[base_columns + sorted_years]
        df = df.drop(['published_years', 'affiliations'], axis=1)
        df = df[['rid', 'fullname', 'first_name', 'last_name', 'alt_names', 'claim_status', 'primary_affiliation',
                 'primary_org_addresses', 'primary_org_countries', 'departments', 'documents_count', 'times_cited',
                 'times_cited_excluding_self', 'citing_publications', 'citing_publications_excluding_self', 'h-index',
                 'author_position_first', 'author_position_last', 'author_position_corresponding', 'orcid',
                 'wos_platform_link']]

        with pd.ExcelWriter(f'researchers - {our_org} - detailed profiles - {date.today()}.xlsx') as writer:
            df.to_excel(writer, sheet_name='Authors', index=False)
            df2.to_excel(writer, sheet_name='Publications by Years', index=False)
            df4.to_excel(writer, sheet_name='Known Affiliations', index=False)

    else:
        with pd.ExcelWriter(f'researchers - {our_org} - {date.today()}.xlsx') as writer:
            df.to_excel(writer, sheet_name='Authors', index=False)


# Defining a class through threading so that the interface doesn't freeze when the data is being retrieved through API
class App(threading.Thread):

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
        self.our_org_label = None
        self.our_org_window = None
        self.our_org_validate_button = None
        self.retrieve_full_profile_data = None
        self.researcher_profiles_found = None
        self.search_requests_required = None
        self.requests_left = None
        self.full_profiles_checkbutton = None
        self.our_org_bottom_label = None
        self.search_button = None
        self.progress_bar = None
        self.progress_label = None
        self.start()

    def run(self):
        self.root = tk.Tk()

        # Setting up style and geometry
        self.root.iconbitmap('./assets/clarivate.ico')
        self.root.title("Researcher API to Excel Converter")
        self.root.geometry("540x370")
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

        # Setting up widgets
        self.api_frame = ttk.Frame(self.root, style='White.TFrame')
        self.apikey_top_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                          text="Web of Science Researcher API Key:")
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
        self.our_org_label = ttk.Label(self.api_frame, style='Bold.TLabel',
                                       text="Affiliation name:")
        self.our_org_window = ttk.Entry(self.api_frame, font=('Calibri', 11))
        self.our_org_validate_button = ttk.Button(self.api_frame, text="Validate", style='Small.TButton',
                                                  command=self.check_affiliation)
        self.retrieve_full_profile_data = BooleanVar()
        self.researcher_profiles_found = IntVar()
        self.search_requests_required = IntVar()
        self.requests_left = IntVar()
        self.full_profiles_checkbutton = ttk.Checkbutton(self.api_frame,
                                                         text='  Retrieve full researcher profiles metadata (takes '
                                                              'significantly more time)',
                                                         variable=self.retrieve_full_profile_data,
                                                         command=check_vs_limits,
                                                         onvalue=True,
                                                         offvalue=False,
                                                         style='Clarivate.TCheckbutton')
        self.our_org_bottom_label = ttk.Label(self.api_frame, text='', style='Regular.TLabel')
        self.search_button = ttk.Button(self.api_frame,
                                        text='Run',
                                        style='Large.TButton',
                                        command=self.run_button)
        self.progress_bar = ttk.Progressbar(self.api_frame, style='Clarivate.Horizontal.TProgressbar',
                                            mode="determinate")
        self.progress_label = ttk.Label(self.api_frame, style='Regular.TLabel')

        # Placing widgets
        self.api_frame.place(x=0, y=0, width=540, height=370)
        self.apikey_top_label.place(x=5, y=5, width=535, height=24)
        self.apikey_window.place(x=5, y=29, width=400, height=30)
        self.apikey_unhide_button.place(x=406, y=29, width=30, height=30)
        self.apikey_button.place(x=440, y=29, width=90, height=30)
        self.apikey_bottom_label.place(x=5, y=59, width=400, height=24)
        self.our_org_label.place(x=5, y=83, width=400, height=30)
        self.our_org_window.place(x=5, y=113, width=400, height=30)
        self.our_org_validate_button.place(x=410, y=113, width=120, height=30)
        self.full_profiles_checkbutton.place(x=5, y=143, width=500, height=30)
        self.our_org_bottom_label.place(x=5, y=173, width=525, height=48)
        self.search_button.place(x=220, y=250, width=100, height=35)
        self.progress_bar.place(x=5, y=300, width=525, height=30)
        self.progress_label.place(x=5, y=330, width=525, height=40)

        self.root.mainloop()

    def check_api_key(self):
        threading.Thread(target=validate_api_key).start()

    def check_affiliation(self):
        threading.Thread(target=validate_affiliation).start()

    def run_button(self):
        threading.Thread(target=main_function).start()


app = App()
