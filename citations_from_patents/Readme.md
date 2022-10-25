# Citations from patents to scholarly documents report


## A simple script to create a list of Web of Science Core Collection documents with counts of times that each of them was cited by patents from Derwent Innovations Index database. The code relies on Web of Science Core Collection article data and Derwent Innovation Index patent families data obtained using Web of Science Expanded API.

This is how the code works:

#### The user needs to enter in the code:
1. Their Web of Science Expanded API key;
2. Web of Science advanced search query - can be an Author name, Author identifier, Afiiliation or Topical search, etc.

And launch the code.

The program will query Web of Science Expanded API for the document identifiers, query each of them for the cited items and catch every citing document that comes from Derwent Innovations Index database. In the end, the program will print how many documents were found, and how many citations from patents they received. Also, the program generates a .csv file containing:
- the document identifiers, or UTs, of each of the documents returned by the search query that the user entered
- the number of citations that each of these documents received from patents
- the list of citing patents for each of these documents separated by spaces.

The main use case of this code is checking which documents are cited by patents the most.

Although this code makes it much easier to check citations from patents, there are some important considerations to keep in mind while using this code:
1. The code checks every citing document, and thus takes time to process. So, a search query returning 3000 documents might take up to an hour to process, so it is wise to launch this code for processing larger search queries (10K+ documents) overnight.
2. The code only retrieves the document identifiers, not the actual documents, so it doesn't consume any Web of Science Expanded API usage - even if you launch it for processing hundreds of documents, it won't get you any closer to hitting the annual usage threshold
3. The list of cited Web of Science documents - as well as the lists of citing Derwent Innovation Index patent families - can be copied and pasted into the Web of Science advanced search window to analyze the datasets in the Web of Science platform user interface
4. InCites Benchmarking & Analytics also has a powerful feature to quickly calculate the number of citing patents in any of the six Analyze reports (Author, Organization, Location, Research Area, Publication Source, or Funding Agency) and a capability to apply various filters to your analysis.