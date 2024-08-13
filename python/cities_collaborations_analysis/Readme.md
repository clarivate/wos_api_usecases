# Cities Collaborations Analysis

![Example](/cities_collaborations_analysis/screenshots/topical.png)

## A simple script to evaluate a set of Web of Science docuents for the cities in which this research has been made - or to evaluate a specific organization for which cities it mostly collaborates with. The code relies on Web of Science article data obtained using Web of Science Expanded API.

This is how the code works

#### The user needs to launch the main.py file and, on the RETRIEVE THROUGH API tab, enter:
1. Their Web of Science Expanded API key;
2. A search query - any search query that can be entered in Advanced Search of Web of Science user interface.
3. Optionally, select:
    - if they would like to remove the collaborating cities, thus isolating the cities associated only with a specific organiztion,
	- or if they want to keep only the collaborating cities on the visualization
	- or if they don't want the program to break down the the organization for analysis, and rather visualize every city that appears in the dataset
4. If they selected anything but the third option in the previous step, the user also needs to enter the name of the affiliation with regards to which the cities will be split into own or collaborating ones.

![GUI](/cities_collaborations_analysis/screenshots/GUI1.png)

And launch the code.

The program will query Web of Science Expanded API for the document data, extract the "City" fields from each of them, process this data and use the Plotly library to draw an interactive world map and mark participating cities (or collaborating with the organizaition provided) with circles. The size of the circle depends on the number of occurrences of this city in the dataset.

The full list of cities will also be saved into an Excel file in the same project folder. The saved Excel files can later be loaded with the second tab of the application, "LOAD EXCEL FILE".

Three main use cases of this code are:
1. Checking in which cities is a research on a specific topic concentrated.
2. Understand which cities does a specific organization collaborate with
3. Figure out in which cities a specific organization is conducting its research

Here is another example of the graphs that the code produces:

![Screenshot](/cities_collaborations_analysis/screenshots/collaborating.png)

As always, we welcome any feedback to further improve this algorithm.
