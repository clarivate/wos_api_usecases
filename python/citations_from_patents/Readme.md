# Citations from patents to scholarly documents report


## A simple script to create a list of Web of Science Core Collection documents with counts of times that each of them was cited by patents from Derwent Innovations Index database. The code relies on Web of Science Core Collection article data and Derwent Innovation Index patent families data obtained using Web of Science Expanded API.

This is how the code works:

#### The user needs to enter in the code:
1. Their Web of Science Expanded API key;
2. Web of Science advanced search query - can be an Author name, Author identifier, Afiiliation or Topical search, etc.

And launch the code.

The program will query Web of Science Expanded API for the document metadata, and then query each Web of Science record with more than 0 citations from Derwent Innovations Index, for the cited items and catch every citing document ID that comes from Derwent Innovations Index database. In the end, the program will print how many documents were found, and how many citations from patents they received. Also, the program generates a .csv file containing:
- the document identifiers, or UTs, of each of the documents returned by the search query that the user entered
- the number of citations that each of these documents received from patents
- the list of citing patent families IDs for each of these documents, separated by spaces.

The main use case of this code is checking which documents are cited by patents the most.

Although this code makes it much easier to check citations from patents, there are some important considerations to keep in mind while using this code:
1. The code checks every citing document that has more than 0 citations individually. This takes time to process. So, a search query returning 3-5K documents might take up to half an hour to process, while larger search queries (50K+ documents) might only be able to complete overnight.
2. The list of cited Web of Science documents - as well as the lists of citing Derwent Innovation Index patent families - can be copied and pasted into the Web of Science advanced search window to analyze the datasets in the Web of Science platform user interface.
3. InCites Benchmarking & Analytics also has a powerful feature to quickly calculate the number of citing patents in any of the six Analyze reports (Author, Organization, Location, Research Area, Publication Source, or Funding Agency) and a capability to apply various filters to your analysis.

This code has a further potential of development for some of the following use cases:
- to find out the inventors who cite specific research papers in their inventions
- to find assignees that own the IP citing specific research papers
- list the countries where the inventions, that cite specific research papers, have been protected with patents
- etc.

As always, we welcome your feedback on this code and invite everyone to contribute and share their ideas.