# Cities Collaborations Analysis


## A simple script to evaluate a set of Web of Science docuents for the cities in which this research has been made - or to evaluate a specific organization for which cities it mostly collaborates with. The code relies on Web of Science article data obtained using Web of Sciencce Expanded API.

This is how the code works

#### The user needs to enter in the code:
1. Their Web of Science Expanded API key;
2. A search query - any search query that can be entered in Advanced Search of Web of Science user interface.
3. Optionally, the organization for analysis, but this field might be left blank.

And launch the code.

The program will query Web of Science Expanded API for the document data, extract the "City" fields from each of them, process this data and print out the top 10 cities associated this set of papers (or collaborating with the organizaition provided). The full list of cities will be saved into a .csv-file in the same project folder.

Three main use cases of this code are:
1. Checking which cities is research on a specific topic concentrated in.

Example: we want to figure out which cities of the world are the leading centers in research of superlubricity. This is what we change in the code:

search_query = 'TS=superlubricity'

our_org = ''

As of March, 3rd, 2022, the program prints out the following:

> This research is concentrated in the following cities:
> 
> Beijing: 278
> Lanzhou: 97
> Xian: 42
> Tel Aviv: 33
> Chengdu: 32
> Argonne: 26
> Shenzhen: 25
> Ecully: 24
> Nanjing: 21
> Shanghai: 19
> 
> Top 10 collaborating cities shown. All cities are saved to cities.csv file.*


2. Understand which cities does a specific organization collaborate with

Example: we want to check which cities have been most actively collaborating with Leiden University in 2020. This is what we change in the code:

search_query = 'OG=Leiden University and PY=2020'

our_org = 'Leiden University'

As of March, 3rd, 2022, the program prints out the following:

> Leiden University located in Leiden collaborates with:
>
> Leiden: 2128
> Amsterdam: 1754
> Utrecht: 988
> Rotterdam: 980
> London: 691
> Nijmegen: 673
> Groningen: 637
> Cambridge: 464
> Paris: 432
> The Hague: 424
>
> Top 10 collaborating cities shown. All cities are saved to cities.csv file.*


3. Figure out in which cities a specific organization is conducting its research

Example: we want to analyze where Pfiser was concentrating its research in 2020

search_query = 'OG=Pfizer and PY=2020'

our_org = 'Pfizer'

As of March, 3rd, 2022, the .csv file produced by the program will contain the following:

> Search Query:	OG=Pfizer and PY=2020
> Results Found:1606
> Organisation:	Pfizer
> Located in:
> City		Occurrences
> New York	572
> Groton	466
> Collegeville	289
> Cambridge	259
> San Diego	125
> La Jolla	75
> Andover	73
> Tadworth	55
> Pearl River	53
> San Francisco	50

...and 72 more cities, as well as a separate list of the cities in which the organizations which collaborate with Pfizer are located.


As always, we welcome any feedback to further improve this algorithm.