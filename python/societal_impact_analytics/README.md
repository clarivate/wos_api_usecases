# Societal Impact Analytics via Web of Science Expanded API

![Example visualisation](screenshots/example.png)

## A Flask application with a simple graphical user interface to analyse and visualise the policy documents and citations from policy documents data from Web of Science Core Collection and Policy Citation Index. The application retrieves the data using Web of Science Expanded API.

This application allows to:
- build a citation report like you would do on Web of Science, but for citation from policy documents
- find the authors in your organization that have the highest policy impact;
- understand the policy authors, sources, and countries that were citing your research in their policy documents;
- monitor trends in research and policy.

The application retrieves metadata using Web of Science Expanded API, visualises it in a variety of ways with Plotly package, and saves them into an Excel spreadsheet.

### How to use it
Download the code, open the project folder where you saved it and create a python file `apikeys.py` right in the project folder. There, you need to create a constant representing your Web of Science Expanded API key and pass its value as a string like in the example below:

```
EXPANDED_APIKEY = 'mYw3b0f$c14nc33xp4nd3d4p1k3y1$4$3cr37'
```

You might also need to install the project dependencies, which are:
- Flask;
- Pandas (and openpyxl);
- Requests;
- Plotly.

And launch the app.py file. Flask will create a development server on http://127.0.0.1:5000 which you can open locally in any browser. This is what the start page looks like:

![Start page](screenshots/index.png)

You can switch between the "SOCIETAL IMPACT" and "TRENDS" tabs on top o the page to access different search and analytical functionality. 

#### SOCIETAL IMPACT tab

On this page, you can enter a Web of Science Core Collection Advanced Search query, i.e., for an affiliation search on Clarivate for publication year of 2000-2025 (you can simply replace Clarivate with your organisation name):

```
OG=Clarivate and PY=2000-2025
```

And press the "Run" button. Please note that as Web of Science Expanded API has a limit of 100,000 records to be retrieved per search query, it is a good idea to validate your search if you're not sure how many records it's going to return.

The data retrieval should take quite some time. Because the application will first retrieve all the Web of Science document IDs and their policy citation counts, then retrieve the IDs of each citing policy document, and then based on the document IDs it will retrieve the policy document metadata, the data retrieval might take some time but the process can easily be run in the background. You can track the progress in your Python window or in the Run view of your IDE if you're launching the program from there. 

When the data extraction is complete, the program will refresh the page and add the key metrics summary as well as interactive visualisation plots with Plotly which you can switch between. It will also save an Excel file with all the metadata retrieved into a /downloads/woscc/ subfolder of the project folder.

You can also use the Load a Previously Saved Excel File form to visualise previously saved files.

These are some of the examples of the visualisations:

![Example visualisation - policy citation report](screenshots/policy_citation_report.png)

![Example visualisation - top authors by societal impact](screenshots/authors_by_societal_impact.png)

![Example visualisation - top citing policy authors](screenshots/citing_authors.png)

![Example visualisation - top citing policy sources](screenshots/citing_policy_sources.png)

![Example visualisation - top citing policy countries](screenshots/citing_policy_countries.png)

#### TRENDS tab

![Trends search page](screenshots/trends_search.png)

On this page, you can enter a simple Web of Science Core Collection topical search query, i.e.:

```
"Kyoto protocol*"
```

And press the "Run" button. Just like on the other tabs, Web of Science Expanded API has a limit of 100,000 records to be retrieved per search query, it is a good idea to validate your search if you're not sure how many records it's going to return.

The application will query both Web of Science Core Collection and Policy Citation Index with the same topical search you provided, retrieve the scholarly and policy documents, and fetch their publication years. You can track the progress in your Python window or in the Run view of your IDE if you're launching the program from there. 

When the data extraction is complete, the program will refresh the page and add an interactive trend graph with Plotly representing the research (purple columns) and policy (green columns) trends for the same topic. It will also save an Excel file with the trend data into a /downloads/trends/ subfolder of the project folder.


You can also use the Load a Previously Saved Excel File form to visualise previously saved searches.

Here is an example of the visualisation:

![Example visualisation - research and policy trends comparison](screenshots/research_and_policy_trend.png)


This application was created to demonstrate the capabilities of Web of Science APIs and custom XML data, and is not a commercial product of Clarivate. It will be reviewed and updated in the future but it will not have the same regular update frequency we normally offer for our commercial products. We do not recommend using this application as a ready-made solution as it is for reporting purposes or for supporting important grant funding decisions. We however encourage the bibliometric community provide feedback on improving this script and to use the script as a base for more advanced analytical projects.

For a consistent experience, intuitive user interface and world-class customer support, please refer to our products like Web of Science, InCites Benchmarking & Analytics, and Journal Citation Reports.
