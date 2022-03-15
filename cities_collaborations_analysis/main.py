import requests
import urllib.parse
from apikey import apikey  # Your API key, it's better not to store it in the program

search_query = 'OG=Pfizer and PY=2020'  # Enter the WoS search query here
our_org = 'Pfizer'  # (OPTIONAL) Enter the organization you'd like to analyze for city collaboration.

headers = {'X-APIKey': apikey}  # our API key is passed in the header of the API request

baseurl = "https://api.clarivate.com/api/wos"  # this is the base URL for WoS Expanded API

cities = []  # The cities are to be stored in a list
# If there is an existing organizational profile mentioned in the "our_org" field, the program will store the list of
# cities associated with this org to keep them separate from the collaborating cities list
our_org_cities = []


# This function gets the cities values from the Web of Science records which we received through the API
def analyze_cities(data):
    for paper in data['Data']['Records']['records']['REC']:  # This is how we iterate over individual WoS records
        if paper['static_data']['fullrecord_metadata']['addresses']['count'] == 1:  # if there's only 1 address
            for org in (
                    paper['static_data']['fullrecord_metadata']['addresses']['address_name']['address_spec']
                    ['organizations']['organization']
            ):  # Iterating over individual organizations in the address field
                if org['pref'] == 'Y' and org['content'] == our_org:  # storing the city belonging to our organization
                    our_org_cities.append(
                        paper['static_data']['fullrecord_metadata']['addresses']['address_name']
                        ['address_spec']['city'].title()
                    )
                    break
            else:  # storing the cities belonging to every other org. Each of them stored as a list item
                cities.append(
                    paper['static_data']['fullrecord_metadata']['addresses']['address_name']
                    ['address_spec']['city'].title()
                )
        else:  # Standard case - when there are multiple addresses in the document record
            # These 2 variables allow us to make multiple addresses with the same city count only once for each paper.
            cities_cache = []
            our_cities_cache = []
            try:
                # Iterating over individual addresses in the Web of Science record
                for address in paper['static_data']['fullrecord_metadata']['addresses']['address_name']:
                    try:
                        # Iterating over individual organizations in the address field
                        for org in address['address_spec']['organizations']['organization']:
                            if org['pref'] == 'Y' and org['content'] == our_org:
                                # storing the city belonging to organization being analyzed
                                if address['address_spec']['city'].title() not in our_cities_cache:
                                    our_cities_cache.append(address['address_spec']['city'].title())
                                    our_org_cities.append(address['address_spec']['city'].title())
                                    break
                        else:
                            if address['address_spec']['city'].title() not in cities_cache:
                                cities_cache.append(address['address_spec']['city'].title())
                                # storing the cities belonging to every other org. Each of them stored as a list item
                                cities.append(address['address_spec']['city'].title())
                    except KeyError:  # When there's no org data in the address (i.e., only street address)
                        pass
            except KeyError:  # when there's no address field in the record
                pass


# Initial request to the API is made to figure out the total amount of requests required
initial_response = requests.get(
    f'{baseurl}?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&count=0&firstRecord=1', headers=headers
)
data = initial_response.json()
total_records = data['QueryResult']['RecordsFound']
# From the total number of records found in the first API response, calculating the number of requests required.
# The program can take up to a few dozen minutes to run, depending on the number of records being analyzed
requests_required = ((total_records - 1) // 100) + 1
for i in range(requests_required):
    subsequent_response = requests.get(
        f'{baseurl}?databaseId=WOS&usrQuery={urllib.parse.quote(search_query)}&count=100&firstRecord={i}01',
        headers=headers
    )
    data = subsequent_response.json()
    analyze_cities(data)
    print(f"{((i + 1) * 100) // (((total_records - 1) // 100) + 1)}% complete")

# Turning lists with stored cities into lists of dictionaries with their names and number of occurrences
our_org_cities_lod = []
cities_lod = []
for city in our_org_cities:
    if len(our_org_cities_lod) == 0:
        our_org_cities_lod.append({'name': city, 'occurrences': our_org_cities.count(city)})
    else:
        for city_in_lod in our_org_cities_lod:
            if city_in_lod['name'] == city:
                break
        else:
            our_org_cities_lod.append({'name': city, 'occurrences': our_org_cities.count(city)})

for city in cities:
    if len(cities_lod) == 0:
        cities_lod.append({'name': city, 'occurrences': cities.count(city)})
    else:
        for city_in_lod in cities_lod:
            if city_in_lod['name'] == city:
                break
        else:
            cities_lod.append({'name': city, 'occurrences': cities.count(city)})


# for the main organization being analyzed, we might get different city values for some of its records. The one
# appearing most frequently will be the primary city for that org - even if the headquarters might be located elsewhere.
def occur(our_org_cities_lod):
    return our_org_cities_lod['occurrences']


if our_org != '':
    our_org_cities_lod.sort(reverse=True, key=occur)
    print(
        f'\nSearch query: {search_query}\nResults found: {total_records}\n'
        f'\n{our_org} located in {our_org_cities_lod[0]["name"]} collaborates with:\n'
    )
# For the case where no org is being analyzed (i.e., the records of a specific researcher or a topical search),
# no base organization is required, and each city that was involved gets into output.
else:
    print(
        f'\nSearch query: {search_query}\nResults found: {total_records}\n'
        f'\nThis research is concentrated in the following cities:\n'
    )


def occur(cities_lod):  # function required as a key to sort the cities on the main list
    return cities_lod['occurrences']


cities_lod.sort(reverse=True, key=occur)  # sorting the cities by number of papers in which they occurred
for city in cities_lod:
    if cities_lod.index(city) < 10:  # printing only the 10 top cities
        print(f'{city["name"]}: {city["occurrences"]}')
print(f'\nTop 10 collaborating cities shown. All cities are saved to cities.csv file.')

# All the cities data gets exported in a .csv file. Make sure this file is closed when you run the code again.
with open('cities.csv', 'w') as writing:
    writing.write(f'Search Query:,{search_query}\n'
                  f'Results Found:,{total_records}\n')
    if our_org != '':
        writing.write(f'Organisation:,{our_org}\n'
                      f'Located in:,\n'
                      f'City,Occurrences\n')
    for city in our_org_cities_lod:
        writing.writelines(f'{city["name"]},{city["occurrences"]}\n')
    writing.write(f'\nCollaborating Cities,Collaborations\n')
    for city in cities_lod:
        writing.writelines(f'{city["name"]},{city["occurrences"]}\n')
