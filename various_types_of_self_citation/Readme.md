# Various types of Self-citation


## A simple script to evaluate the self-citation percentage for a set of Web of Science documents at the level of user's preference. The script relies on retrieving the publication data via Web of Science Expanded API


This script allows to evaluate the following types of self-citation to a given Web of Science document or a set of documents:
1. Coauthor-level self-citation (when there are the same author records appearing in both cited and citing paper)
2. Organization-level self-citation (when the authors in cited and citing papers might be different, but represent the same organization)
3. Journal self-citation (when the authors and/or organization in cited and citing papers might be different, but both records were published in the same title)

This is how it works:

#### In the code of the program, the user needs to enter:
1. Their Web of Science Expanded API key;
2. A Web of Science Core Collection advanced search query for a set of records they would like to analyze;

And launch the code.

The program will query Web of Science Expanded API to create objects of class CitedPaper and CitingPaper. Every CitingPaper class object would be a list item for of papers a CitedPaper class object which is a way the program tracks citation links between cited and citing papers. After that, the program will create lists of sets for the author, organization, and journal names for every cited and citing record, and apply sets.intersection() method to each of them to check if self-citation occured at any of the described levels, and for every case where a self-citation even would occur, the program will additionally query Web of Science Expanded API for the cited references of the citing paper to check the number of cited reference in it that lead to the cited document. The total self-citation is calculated as follows:

Self-citation of a set of documents = (number of self-citations of this type found in the citing documents) / (total times cited count for that set of cited papers)

Although this is a good step towards increasing the precision of self-citation calculation, we would like to address a few limitations of this approach:

1.  As the author name in Web of Science Core Collection might require additional disambiguation, an author-level self-citation analysis provides additional check for:
- document sets made by Clarivate Distinct Author Identification System, currently being used in Web of Science Author Search
- documents linked to ResearcherID profiles of the authors
- documents linked to ORCID profiles of the authors
But we would like to stress that neither of those approaches can guarantee 100% precision of author disambiguation at the moment.
2. Self-citation might appear the most obvious way of citation manipulation. However, excessive self-citation rate for a given paper does not necessarily indicate that a citation manipulation has occured, simliarly self-citation rate of acceptable percentage (normally below 20-30%) doesn't guarantee that there hasn't been any scientific misconduct. In order to explore the potential citation manipulations with more reliability, it is advised to run a check for high concentration of citations to a paper coming from specific author or group of authors, publication sources, organizations, etc.
