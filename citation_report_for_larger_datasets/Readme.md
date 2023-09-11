# Citation Report for Larger Datasets


## A simple script that calculates 4 basic metrics that can be found in Web of Science Citation Report. The code relies on Web of Science Core Collection aricle data obtained using Web of Science Starter API.

This is how the code works:

#### The user needs to enter in the code:
1. Their Web of Science Starter API key (we recommend to create another file `apikey.py` in the same project folder, store your API key value there, and import it into the main python file). 
2. Web of Science advanced search query - can be an Topical search, Affiliation name, Author name, Author identifier, etc, i.e.:

```
# Search query for which to calculate the citation report
SEARCH_QUERY = 'OG=The World Bank'
```

And launch the code.

The program will query Web of Science Starter API for the document metadata, and calculate the key 4 metrics that are the most popular ones in Web of Science Citation Report:

- Number of Web of Science documents
- Sum of the Times Cited
- H-Index
- and Avarage citations per item

It's going to print them in the Run screen of your IDE or right in the command screen if you launched the file directly:

```
Total Documents: 20767
Sum of the Times Cited: 623528
H-Index: 315
Average Citations Per Item: 30.0249434198488
```

In the end, the program will also create a documents.csv file in the same project folder. That file will contain the Web of Science document IDs and the times this document has been cited.

The main use case of this code is analyzing citations for the datasets larger than 10,000 records. As Web of Science Starter API - Institutional Plan currently has a limit of 5,000 requests per day, and the maximum possible value for the `page` API query parameter is 1000, the maximum dataset available for such an analysis is 50,000 Web of Science records (in which case the data retrieval might take up to an hour, depending also on your internet connection). 

We also recommend this code to Python beginners to study how to send API queries with Python, how to extract necessary metadata, how to process metadata, and save it into .csv.