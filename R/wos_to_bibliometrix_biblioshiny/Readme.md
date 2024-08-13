# Web of Science to Bibliometrix / Biblioshiny exporter


## A simple R script that retrieves Web of Science documents metadata into a raw text format acceptable by both Bibliometrix R package and Biblioshiny app. Uses Web of Science Expanded API to extract the documents metadata.

This is how the code works:

#### After downloading the script, the user needs to:
1. Create a new R file called apikeys.R in the same project folder, and add only one line of code there, namely set up a hidden variable named .starter_apikey and pass their Web of Science Starter API key as a string value, i.e.:
```
.expanded_apikey <- "mY3xp4nd3d4p1k3y1$$0m37h1Ngl1k37h15"
```
We recommend to store your API key value in a separate file to prevent inadvertent sharing. 
2. Edit your Web of Science advanced search query right in the code - can be an Topical search, Affiliation name, Author name, Author identifier, etc, i.e.:

```
# Search query for which to form a dataframe
SEARCH_QUERY = "TS=bibiometric*"
```
3. Set the retrieve_cited_reference_flag to TRUE if you want to also pull the cited references data. This will significantly increase the analytical capabilities of both Bibliometrix and Biblioshiny, but please note that the way Web of Science expanded API works is that it queries every single Web of Science document for its cited references individually, so setting this flag to TRUE will also significantly increase the time it would take to retrieve all the necessary metadata.

And launch the code.

The program will query Web of Science Expanded API for the document metadata, parse the necessary metadata fields, and save them into a plain text file that you can also export from Web of Science platform user interface Export button, except for in this case the process is going to be fully automated.

It is also possible to modify this code so that it works with Web of Science Starter API, but Expanded API is the one that returns all the Web of Science metadata fields you can work with on Bibliometrix and Biblioshiny.

As always, we welcome any feedback on this code.