import requests
import threading
import urllib.parse
import time
import pandas as pd
import tkinter as tk
from tkinter import ttk
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
        requests_left = validation_request.headers['X-RateLimit-Remaining-Day']
        if int(requests_left) < 100:
            app.apikey_bottom_label['text'] = f"API Authentication succeeded; Requests left today: {requests_left}"
        else:
            app.apikey_bottom_label['text'] = f"API Authentication succeeded"
        records_amount = validation_data['metadata']['total']
        if records_amount > 0:
            app.our_org_bottom_label['text'] = f"Researcher Profiles found: {records_amount}"
            return records_amount
        else:
            app.our_org_bottom_label['text'] = f'Please check your Affiliation name'
            return False
    else:
        app.our_org_bottom_label['text'] = f'Please check your Affiliation name'
        return False


# Sending the API requests to the server
def researcher_api_request(i, requests_required, our_org, researchers):
    try:
        request = requests.get(f'https://api.clarivate.com/apis/wos-researcher/researchers?q=OG~'
                               f'"{urllib.parse.quote(our_org)}"&page={i + 1}&limit=50',
                               headers={'X-APIKey': app.apikey_window.get()})
        data = request.json()
        fetch_researchers_data(data, researchers)
        progress = ((i + 1) / requests_required) * 100
        app.progress_bar.config(value=progress)
        app.style.configure('Clarivate.Horizontal.TProgressbar', text=f'{progress:.1f}%')
        app.root.update_idletasks()
        print(f'{((i + 1) * 100) / requests_required:.1f}% complete')
    except(requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, KeyError):
        print(f'Resending Researcher API request #{i + 1}')
        time.sleep(1)
        researcher_api_request(i, requests_required, our_org, researchers)


# The main function that launches all the others
def main_function():
    app.search_button.config(state='disabled', text='Retrieving...')
    app.progress_label['text'] = ''
    records_amount = validate_affiliation()
    if records_amount is False:
        app.search_button.config(state='active', text='Run')
    else:
        if app.progress_label['text'] == 'Please check your search query':
            app.progress_label['text'] = ''
        our_org = app.our_org_window.get()
        requests_required = (records_amount // 50) + 1
        researchers = []
        for i in range(requests_required):
            researcher_api_request(i, requests_required, our_org, researchers)
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

    with pd.ExcelWriter(f'researchers - {our_org} - {date.today()}.xlsx') as writer:
        df.to_excel(writer, sheet_name='Authors', index=False)


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
        self.our_org_label = None
        self.our_org_window = None
        self.our_org_validate_button = None
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
        self.root.geometry("540x300")
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
        self.our_org_bottom_label = ttk.Label(self.api_frame,
                                              text='Enter your organization name to retrieve the researcher profiles',
                                              style='Regular.TLabel')
        self.search_button = ttk.Button(self.api_frame,
                                        text='Run',
                                        style='Large.TButton',
                                        command=self.run_button)
        self.progress_bar = ttk.Progressbar(self.api_frame, style='Clarivate.Horizontal.TProgressbar',
                                            mode="determinate")
        self.progress_label = ttk.Label(self.api_frame, style='Regular.TLabel')

        # Placing widgets
        self.api_frame.place(x=0, y=0, width=540, height=300)
        self.apikey_top_label.place(x=5, y=5, width=535, height=24)
        self.apikey_window.place(x=5, y=29, width=400, height=30)
        self.apikey_unhide_button.place(x=406, y=29, width=30, height=30)
        self.apikey_button.place(x=440, y=29, width=90, height=30)
        self.apikey_bottom_label.place(x=5, y=59, width=400, height=24)
        self.our_org_label.place(x=5, y=83, width=400, height=30)
        self.our_org_window.place(x=5, y=113, width=400, height=30)
        self.our_org_validate_button.place(x=410, y=113, width=120, height=30)
        self.our_org_bottom_label.place(x=5, y=143, width=500, height=24)
        self.search_button.place(x=220, y=180, width=100, height=35)
        self.progress_bar.place(x=5, y=230, width=525, height=30)
        self.progress_label.place(x=5, y=260, width=525, height=40)

        self.root.mainloop()

    def check_api_key(self):
        threading.Thread(target=validate_api_key).start()

    def check_affiliation(self):
        threading.Thread(target=validate_affiliation).start()

    def run_button(self):
        threading.Thread(target=main_function).start()


app = App()
