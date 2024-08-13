# Retrieve Web of Science search query results into an R dataframe using Web of Science Starter API


## A simplest possible script that retrieves Web of Science documents metadata into an R dataframe. If you're new to R and/or Starter API, try this script to figure out how to send API requests, to paginate, convert into a dataframe, and try basic plotting.

This is how the code works:

#### After downloading the script, the user needs to:
1. Create a new R file called apikeys.R in the same project folder, and add only one line of code there, namely set up a hidden variable named .starter_apikey and pass their Web of Science Starter API key as a string value, i.e.:
```
.starter_apikey <- "mY574r73r4p1k3y1$$0m37h1Ngl1k37h15"
```
We recommend to store your API key value in a separate file to prevent inadvertent sharing. 
2. Edit your Web of Science advanced search query right in the code - can be an Topical search, Affiliation name, Author name, Author identifier, etc, i.e.:

```
# Search query for which to form a dataframe
SEARCH_QUERY = 'TS=bibiometric*'
```

And launch the code.

The program will query Web of Science Starter API for the document metadata, calculate the number of requests required to pull all the data, send the necessary amount of requests, and merge the results into a single dataframe.

In the end, the program will also allow you to view that dataframe and try some basic plotting by visualising the publication dynamics for this search based on the publication year of each record.

We recommend this code to beginner R coders to study how to send API queries with R, how to paginate, how to create and merge dataframes, and how to plot the data.