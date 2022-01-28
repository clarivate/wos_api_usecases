# Cities Collaborations Analysis


## A simple script to evaluate a set of Web of Science docuents for the cities in which this research has been made - or to evaluate a specific organization for which cities it mostly collaborates with. The code relies on Web of Science article data obtained using Web of Sciencce Expanded API

This is how the code works

#### The user needs to enter in the code:
1. Their Web of Science Expanded API key;
2. A search query - any search query that can be entered in Advanced Search of Web of Science user interface.
3. Optionally, the organization for analysis, but this field might be left blank.

And launch the code.

The program will query Web of Science Expanded API for the document data, extract the "City" fields from each of them, process this data and print out the top 10 cities associated (or collaborating with) this set of papers. The full list of cities will be saved into a .csv-file in the same project folder.

As always, we welcome any feedback to further improve this algorithm.