# Various types of Self-citation


## A simple script to evaluate the self-citation percentage for the paper at the level of user's preference. The script relies on retrieving the publication data via Web of Science Expanded API


This script allows to evaluate the following types of self-citation to a given paper:
1. Author-level self-citation (when there are the same author records appearing in both cited and citing papers)
2. Organization-level self-citation (when the authors in cited and citing papers might be different, but represent the same organization)
3. Journal self-citation (when the authors and/or organization in cited and citing papers might be different, but both records were published in the same title)

This is how it works:

#### In the code of the program, the user needs to enter:
1. Their Web of Science Expanded API key;
2. An Accession Number of the Web of Science Core Collection record they would like to analyze;

And launch the code.

The program will create lists of sets for the author, organization, and journal names for every cited and citing record, and apply sets.intersection() method to each of them to check if self-citation occured at any of the described levels. The self-citation is calculated as follows:

Self-citation of a paper = (number of self-citations of this type found in the records which cite the paper) / (times cited count for that paper)

Although this is a good step towards increasing the precision of self-citation calculation, we would like to address a few limitations of this approach:

1.  As the author name in Web of Science Core Collection might require additional disambiguation, an author-level self-citation analysis provides additional check for:
- document sets made by Clarivate Distinct Author Identification System, currently being used in Web of Science Author Search
- documents linked to ResearcherID profiles of the authors
- documents linked to ORCID profiles of the authors
But we would like to stress that neither of those approaches can guarantee 100% precision of author disambiguation at the moment.
2. Self-citation calculation formula currently relies on the number of self-citations in the citing records in its numerator, and the times cited count for a paper in its denominator. As a single citing document might contain more than one refernce to the cited document, the number of citing documents might sometimes be less than the actual number of citations that the paper has received. This means that the formula might sometimes return lower scores of self-citation.
3. Self-citation might appear the most obvious way of citation manipulation. However, excessive self-citation rate for a given paper does not necessarily indicate that a citation manipulation has occured, simliarly self-citation rate of acceptable percentage (normally below 20-30%) indicate that there hasn't been any scientific misconduct. In order to explore the potential citation manipulations with more reliability, it is advised to run a check for high concentration of citations to a paper coming from specific author or group of authors, publication sources, organizations, etc.
4. The algorithm currently works for checking single papers, an improvement to the code for calculating self-citations for a set of papers is currently under development. We welcome any additional feedback to further improve this algorithm.