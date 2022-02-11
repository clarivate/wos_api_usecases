import requests
import urllib.parse
from datetime import date
from apikey import apikey   # Your API key, it's better not to store it in the program

search_query = 'ts=(energ* and fuel*) and CU=Poland and py=2020'  # Enter the WoS search query here
our_org = ''  # (OPTIONAL) Enter the organization you'd like to analyze for city collaboration.

headers = {
    'X-APIKey': apikey  # our API key is passed in the header of the API request
}

baseurl = "https://api.clarivate.com/api/wos"  # this is the base URL for WoS Expanded API

cities = []  # The cities are to be stored in a list
# If there is an organizational profile in the search query or "our_org" field, the program will store the list of
# cities associated with this org to keep them separate from the collaborating cities list
our_org_cities = []

# Just a simple loop to make sure data entry is easier: if "our_org" variable is empty and the search is made for "OG=",
# the program will assume the affiliation in the "OG=" search query is the one being analyzed
if our_org == '':
    org_analysis_flag = False
    if search_query.count('OG=') == 1:
        org_analysis_flag = True
        if search_query.count('=') == 1:
            our_org = search_query[search_query.find('OG=') + 3:]
        else:
            our_org_l = search_query[search_query.find('OG=') + 3:]
            if (
                    our_org_l.find(' AND ') > -1 or our_org_l.find(' OR ') > -1 or our_org_l.find(' NOT ') > -1 or
                    our_org_l.find(' and ') > -1 or our_org_l.find(' or ') > -1 or our_org_l.find(' not ') > -1
            ):
                existing_booleans = []
                if our_org_l.find(' AND ') > -1:
                    existing_booleans.append(our_org_l.find(' AND '))
                if our_org_l.find(' OR ') > -1:
                    existing_booleans.append(our_org_l.find(' OR '))
                if our_org_l.find(' NOT ') > -1:
                    existing_booleans.append(our_org_l.find(' NOT '))
                if our_org_l.find(' and ') > -1:
                    existing_booleans.append(our_org_l.find(' and '))
                if our_org_l.find(' or ') > -1:
                    existing_booleans.append(our_org_l.find(' or '))
                if our_org_l.find(' not ') > -1:
                    existing_booleans.append(our_org_l.find(' not '))
                our_org_ending_index = min(existing_booleans)
                our_org = our_org_l[:our_org_ending_index]
        if (our_org[0] == '(' and our_org[-1] == ')') or (our_org[0] == '"' and our_org[-1] == '"'):
            our_org = our_org[1:-1]
else:
    org_analysis_flag = True


# This function actually gets the cities values from the Web of Science records which we received through the API
def analyze_cities(data):
    for paper in data['Data']['Records']['records']['REC']:  # Analyzing every paper
        # This variable allows us to make one paper with multiple addresses with the same city counts only once.
        # Otherwise there would be duplication of city values in the results and we don't want that.
        cities_cache = []
        if paper['static_data']['fullrecord_metadata']['addresses']['count'] == 1:  # if there's only 1 address
            for org in (
                    paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec'][
                        'organizations']['organization']
            ):
                if org['content'] == our_org:  # storing the city belonging to organization being analyzed
                    our_org_cities.append(
                        paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']
                        ['city'].title()
                    )
            else:  # storing the cities belonging to every other org. Each of them stored as a dictionary in the list
                for city in cities:
                    if city['name'] == (
                            (paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec'][
                                'city']).title()
                    ):
                        city['occurrences'] += 1
                        break
                else:
                    cities.append(
                        {'name': paper['static_data']['fullrecord_metadata']['addresses']['address_name']
                         ['address_spec']['city'].title(), 'occurrences': 1}
                    )
        else:  # Standard case - when there are multiple addresses in the document record
            try:
                for address in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
                    for org in address['address_spec']['organizations']['organization']:
                        if org['pref'] == 'Y' and org['content'] == our_org:
                            # storing the city belonging to organization being analyzed
                            our_org_cities.append(address['address_spec']['city'].title())
                            break
                    else:
                        if address['address_spec']['city'].title() not in cities_cache:
                            cities_cache.append(address['address_spec']['city'].title())
                            # storing the cities belonging to every other org. Each of them stored as a dictionary in
                            # the list
                            for city in cities:
                                if city['name'] == address['address_spec']['city'].title():
                                    city['occurrences'] += 1
                                    break
                            else:
                                cities.append({'name': address['address_spec']['city'].title(), 'occurrences': 1})
                        else:
                            pass
            except KeyError:  # when there's no address field in the record
                pass


# Initial request to the API is made to figure out the total amount of requests required
initial_response = requests.get(
    f'{baseurl}?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&count=100&firstRecord=1', headers=headers
)
data = initial_response.json()  # First 100 records received
analyze_cities(data)
total_records = data['QueryResult']['RecordsFound']

# From the first response, extracting the total number of records found and calculating the number of requests required.
# The program can take up to a few dozen minutes, depending on the number of records being analyzed
for i in range((total_records - 1) // 100):
    subsequent_response = requests.get(
        f'{baseurl}?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&count=100&firstRecord={i}01',
        headers=headers
    )
    data = subsequent_response.json()
    analyze_cities(data)
    print(f"{((i + 1) * 100) // ((total_records - 1) // 100)}% complete")

# for the main organization being analyzed, we might get different city values for some of its records. The one
# appearing most frequently will be the primary city for that org - even if the headquarters might be located elsewhere.
primary_city = {'name': 'blank', 'occurrences': 0}
if org_analysis_flag:
    for city in our_org_cities:
        if our_org_cities.count(city) > primary_city['occurrences']:
            primary_city = {'name': city, 'occurrences': our_org_cities.count(city)}
    print(
        f'\nSearch query: {search_query}\nResults found: {total_records}\n'
        f'\n{our_org} located in {primary_city["name"]} collaborates with:\n'
    )
# For the case where no org is being analyzed (i.e., the records of a specific researcher or a topical search),
# no base organization is required, and each city that was involved gets into output.
else:
    print(
        f'\nSearch query: {search_query}\nResults found: {total_records}\n'
        f'\nThis research is concentrated in the following cities:\n'
    )

def occur(cities):  # function required as a key to sort the cities on the main list
    return cities['occurrences']


cities.sort(reverse=True, key=occur)  # sorting the cities by number of papers in which they occurred
for city in cities:
    if cities.index(city) < 10:  # printing only the 10 top cities
        print(f'{city["name"]}: {city["occurrences"]}')
print(f'\nTop 10 collaborating cities shown. All cities are saved to cities.csv file.')

# All the cities data gets exported in a .csv file. Make sure this file is closed when you run the code again.
today = date.today()
with open('cities.csv', 'w') as writing:
    writing.write(f'Organisation:,{our_org}\n'
                  f'Located:,{primary_city["name"]}\n'
                  f'Search Query:,{search_query}\n'
                  f'Results Found:,{total_records}\n'
                  f'Search date:,{today.strftime("%m %B %Y")}\n\n'
                  f'Collaborating Cities,Collaborations\n')
    for city in cities:
        writing.writelines(f'{city["name"]},{city["occurrences"]}\n')
