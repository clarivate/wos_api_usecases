# All Author IDs associated with an organization


## A simple script to retrieve all author identifiers associated with a certain Affiliation (or Organisational profile) in the Web of Science Core Collection. The code relies on Web of Science article data obtained using Web of Science Expanded API.

### How to use this script
Simply open the main.py file with your code editor and:
1. Create a new python file named apikey.py in the same project folder, and add only one line of code there, namely set up a constant named APIKEY and pass your Web of Science Expanded API key as a string value, i.e.:
```
APIKEY = "mY3xp4nd3d4p1k3y1$$0m37h1Ngl1k37h15"
```
2. Edit the Organization profile name as a string constant `OUR_ORG` right in the code
3. Add any additional parameters, such as publication years, subject area, source title, etc. Please use the Web of Science Advanced Search query syntax.

And launch the code.

The program will query Web of Science Expanded API for the document data, extract the necessary author-related fields from each of them, and create a .csv-file in the same project folder that will contain:
- the author's First and Last names
- the author's ResearcherID
- the author's ORCID (if it exists)
- the link to the author's record in Web of Science
- whether the author's record has been claimed by the author or not (True/False)
- the list of author's document IDs in Web of Science (also known as Accession Numbers, or UTs)

The main use case of this code is checking which author identifiers exist for your organization and how up to date each of them is.

Although this code makes it much easier to work on a set of author IDs associated with your organisations, there are some important considerations to keep in mind while using this code:
1. The code only relies on the links between "author" and "organization" fields in the Web of Science Core Collection record metadata. As there was no generally accepted practice to have these links in every published paper before mid-2007, this code might not return a lot of results for the documents published earlier than year 2008.
2. This also means that if your employee doesn't have any documents affiliated with your organization, they won't appear in the results.
3. This code does not rely on the current organization that the authors provide manually on their Web of Science author profiles or Publons profiles.
4. The document is not likely to appear in the .csv file if it is not linked to your organization profile.
5. The above can also happen even when the Web of Science record is linked to an organization profile, and the paper was published after the year 2007, but a single author name field which belongs to an author from your organization is not linked to your organization field. Most likely this would mean that there has been an issue between the publisher submitting publication metadata into Web of Science Core Collection and indexing this data by us, and the link between the author name and the organization name in this record can be restored by providing a "Suggest a correction" feedback right in the Web of Science interface.
6. The ORCID value can be stored in the Web of Science Core Collection record in two ways: either in the author summary record, or in the "contributors" section of the record. In the latter case, it's much harder to relate a specific contributor and their ORCID to a specific author of the document. The algorithm relies on a exact match in the author and contributor last names, but this approach might work incorrectly in case the author has several ways of writing their last name, or in case there are authors with the same last name on one document. So far this is the best approximation that could be used in such a simple code without involving fuzzy logic algorithms, but as always we encourage any feedback on how the author and contributor matching can be improved. 
7. Organization affiliation can sometimes be missing in the regular Address list but appear in Reprint, or Corresponding, address list of certain papers. Although this is quite a rear event, it is technically possible to add a function for counting the corresponding addresses.
8. We do not encourage using this code right away for preparing the official research output reporting. Before submitting the external report based on this algorithm, we suggest double checking the author IDs and corresponding numbers, and welcome any feedback to further improve this algorithm.