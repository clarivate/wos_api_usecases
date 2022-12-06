# Compare research and innovation trends


## A script that demonstrates the power of unifying the research data from Web of Science and patents data from Derwent Innovation. It queries both databases with the same topical search, analyses the annual research and innovation dynamics for it, visualises them as a bar chart using Plotly, and also saves the trend data as a .csv file for further analysis. The code uses Web of Science Lite API and Derwent API.

This is how the code works:

#### The user needs to enter in the code:
1. Their Web of Science Lite API key, as well as Derwent API login and password;
2. A topical search query.

And launch the code.

The program will query Web of Science Lite API for the scholarly document data, then query the Derwent API for the patent data. It will extract the fields of publication year from each of them, and use the Plotly library to draw a bar chart to visualize their annual dynamics, and also create a .csv-file in the same project folder that will contain the following columns for each year:
- A number of Web of Science documents that contain the topical search keyword and were published that year
- A number of patent families that contain the topical search keyword and received their earliest priority that year
- A number of patent families that contain the topical search keyword and were published that year

We considered it important to distinguish the earliest priority years and punlication years for the patent families as there is normally a 18 months gap between the patent application submission and its publication by the patent office. We have to stress that in scholarly publishing, there is also normally a significant gap between the mauscript submission and its publication, but there is no standard timeframes for the manuscipt processing from submission to publication, and their range varies greatly from a few weeks to a few years in certain cases.

The main use case of this code is comparing the trends in research and innovation for a given topic. In certain cases, like, for instance, topics of fullerenes, cubesats, or exosomes, there would be an obvious exponential growth in research output, followed by a similar exponential growth in the number of registered inventions. The gaps between these trends can sometimes reach several years. While, in other cases, like in blokchain research or convolutional neural networks research, the exponential growth trends would more or less go hand in hand, with an obvious domination of patent documents in the earlier years. Here are some examples of the graphs that the code produces:

![Exosomes](/screenshots/)

![Metasurfaces](/screenshots/Metasurfaces.png)

![Microplastics](/screenshots/Microplastics.png)

![MXene](/screenshots/Mxene.png)

![Nanorobots](/screenshots/Nanorobots.png)

![Selective serotonin reuptake inhibitors](/screenshots/Selective Serotonin Reuptake Inhibitors.png)

A few important considerations regarding this alrorithm:
1. Although it is possible to send similar topical search queries to both Web of Science and Derwent Innovation, the code currently only sends simple one-word queries, like "exosomes", or multi-word ones, like "selective serotonin reuptake inibitor", using common truncation symbols like asterisk is also possible, like in "cubesat*". Currently the code doesn't support the boolean search operators, like AND, OR, NOT, SAME, or proximity operators, some of which work differently for each of the databases. However, it is possible to improve the algorithm to also accept the more complex queries.
2. The code sends a search query to Web of Science Core Collection which is equal to "Topic" basic search, or "TS=" advanced search. The query sent to Derwent Innovation is a bit more complex, relying on a number of search fields which, added together, are similar to the "Text Fields" fielded search or "ALL=" expert search in Derwent Innovation. For more information on the Derwent search fields, please refer to [Derwent Innovation help file]( https://www.derwentinnovation.com/tip-innovation/support/help/patent_fields.htm#all_text_fields)
3. The code works with Web of Science Lite API, but it is also possible to adapt it to work with Web of Science Starter or Expanded API.
4. Derwent API works with Derwent Innovation, the professional platform for patent analysis. Clarivate also offers Derwent Innovations Index, a database available on subscription at Web of Science platform, which is related but different resource. Derwent Innovations Index data can be retrieved using Web of Science Expanded API, for an interesting use case of analyzing patent citations please refer to this simple code: [Citations from Patents Report](https://github.com/clarivate/wos_api_usecases/tree/main/citations_from_patents)

As always, we welcome any feedback to further improve this algorithm.