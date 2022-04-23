# All Author IDs associated with an organization


## A simple script to retrieve all author identifiers associated with a certain Affiliation (or Organizational profile) in the Web of Science Core Collection. The code relies on Web of Science article data obtained using Web of Science Expanded API.

This is how the code works

#### The user needs to enter in the code:
1. Their Web of Science Expanded API key;
2. Organization profile name - any Affiliation that exists in the Web of Science Core Collection.
3. Any additional parameters, such as publication years, subject area, source title, etc. Please use the Web of Science Advanced Search query syntax.

And launch the code.

The program will query Web of Science Expanded API for the document data, extract the necessary author-related fields from each of them, and create a .csv-file in the same project folder that will contain:
- the author's First and Last names
- the author's ResearcherID (if it exists)
- the author's ORCID (if it exists)
- the link to the author's record in Web of Science
- whether the author's record has been claimed by the author or not (True/False)
- the list of author's document IDs in Web of Science (also known as Ascession Numbers, or UTs)

The main use case of this code is checking which author identifiers exist for your organization and how up to date each of them is.

Although this code makes it much easier to work on a set of author IDs associated with your organizations, there are some important considerations to keep in mind while using this code:
1. The code only relies on the links between "author" and "organization" fields in the Web of Science Core Collection record metadata. As there was no generally accepted practice to have these links in every published paper before mid-2007, this code might not return a lot of results for the documents published earlier than year 2008.
2. This also means that if your employee doesn't have any documents affiliated with your organization, they won't appear in the results.
3. This code does not rely on the current organization that the authors provide manually on their Web of Science author profiles or Publons profiles.
4. The document is not likely to appear in the .csv file if it is not linked to your organization profile.
5. The above can also happen even when the Web of Science record is linked to an organization profile, and the paper was published after the year 2007, but a single author name field which belongs to an author from your organization is not linked to your organization field. Most likely this would mean that there has been an issue between the publisher submitting publication metadata into Web of Science Core Collection and indexing this data by us, and the link between the author name and the organization name in this record can be restored by providing a "Suggest a correction" feedback right in the Web of Science interface.
4. Organization affiliation can sometimes be missing in the regular Address list but appear in Reprint, or Corresponding, address list of certain papers. Although this is quite a rear event, it is technically possible to add a function for counting the corresponding addresses.
5. We do not encourage using this code right away for preparing the official research output reporting. Before submitting the external report based on this algorithm, we suggest double checking the author IDs and corresponding numbers, and welcome any feedback to further improve this algorithm.