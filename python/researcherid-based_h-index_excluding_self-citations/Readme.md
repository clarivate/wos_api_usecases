# ResearcherID-based Calculation for H-Index (excluding self-citations)

## A simple script to evaluate the H-index for a given ResearcherID both including and excluding coauthor self-citations. The script relies on retrieving the publication data via Web of Science Expanded API.

### How to use this script
Simply open the main.py file with your code editor and:
1. Create a new python file named apikey.py in the same project folder, and add only one line of code there, namely set up a constant named APIKEY and pass your Web of Science Expanded API key as a string value, i.e.:
```
APIKEY = "mY3xp4nd3d4p1k3y1$$0m37h1Ngl1k37h15"
```
2. Edit the Web of Science Core Collection advanced search query constant right in the code

And launch the code.

The program will query the Web of Science Expanded API, extract the necessary article metadata as well as the cited references for each of them, and analyse each of the documents linked to that specific ResearcherID to check if any of them were referencing other documents in the same set. For every case of identified self-citation, the "times_cited_without_self-citation" field for the cited paper is reduced by 1. Afterwards, both H-index including self-citations and H-index excluding self-citations are printed by the program, and the detailed document-level citation data is being saved to a .csv file in the same project folder.

Although this is a good step towards increasing the precision of self-citation calculation, we would like to address a few limitations of this approach:

1. Creating and updating ResearcherIDs is done by the authors themselves, and it cannot be guaranteed that a given ResearcherID search would return a 100% correct set of an author's papers. However, this algorithm can accept search queries by field different from Author Identifiers, like Author Name, for example.
2. As for the purpose of this code, the self-citation is defined as the identical documents appearing among both cited and citing documents, the self-citation and self-referencing in this particular case can be considered the same. This might not be the case for analyzing more complicated cases of self-referencing or self-citation.
3. It is important that the author-level analysis mentioned above works exactly what it is named for: author-level self-citations, and we suggest that the users understand the differentce between coauthor self-citation and author self-citation which are not the same phenomenons in bibliometrics. Author self-citation identifies a self-citation event only if the author being analyzed appears on both cited and citing paper. On contrast, coauthor self-citation identifies a self-citation event even if the author being analyzed didn't cite their own research, but their coauthors did. While it is techincally possible to include the coauthor-level self-citation into this algorithm, we decided that including too many output metrics might actually make it harder to measure self-citations with this program. For assesing the volumes of coauthor-level self-citations, please refer to [a more comprehensive self-citation analysis code available here](https://github.com/clarivate/wos_api_usecases/tree/main/various_types_of_self_citation).
4. Self-citation might appear the most obvious way of citation manipulation. However, excessive self-citation rate for a given paper does not necessarily indicate that a citation manipulation has occured, simliarly self-citation rate of acceptable percentage (normally below 20-30%) doesn't guarantee that there hasn't been any scientific misconduct. In order to explore the potential citation manipulations with more reliability, it is advised to run a check for high concentration of citations to a paper coming from specific author or group of authors, publication sources, organizations, etc.