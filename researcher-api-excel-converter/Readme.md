# Researcher API to Excel converter

![Example](/researcher-api-excel-converter/screenshots/GUI.png)


## A program with a simple GUI that extracts the researchers data from an organizational search using Researcher API, and organises it into an Excel table

This is a very simple program that requires a Researcher API key, and an Affiliation name. It's running a search on every researcher profile that is affiliated with that organization, returns the researcher metadata, and saves it in an .xlsx file in the project folder


#### The user needs to launch the main.py file and enter:
1. Their Researcher API key;
2. The name of the Affiliaiton for which they would like to retrieve the researchers data

![Screenshot](/researcher-api-excel-converter/screenshots/GUI2.png)

And click the Run button.

The program will create an Excel file in the same project folder, where each Researcher record will have their ResearcherID, their full name, their primary affiliation, their H-index, documents found, and times cited, as well as a link to their researcher profile on Web of Science platform user interface, resolved through the ResearcherID.

![Screenshot](/researcher-api-excel-converter/screenshots/GUI2/results.png)

It is important that the data available through the /researchers{rid} endpoint contains additional data fields, such as Published Names, research output by years, times cited without self-citations, and more. It is possible to develop a functionality to retrieve this extended researcher metadata (as well basic document-level and peer reviews data), as the relevant links to the correct endpoints are also returned by a get-request to the default /researchers endpoint, but each of these requests will take additional time.

As always, we welcome any feedback on this code.
