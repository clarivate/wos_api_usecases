# Fractional Counting Calculator

![Example](python/author-level_fractional_counting_for_organizations/screenshots/clarivate.png)


## A program with a simple GUI to calculate and visualize the number of papers of an organization using fractional counting approach that retrieves the publication data via Web of Science Expanded API


The default way of counting papers and citations to them, being currently used in Web of Science, InCites, and other Clarivate resources, is called whole counting, or full counting method. In the case of full counting, a research output is fully attributed to each of the authors and/or each of the affiliated organizations. For example, a publication coauthored by two authors from two different universities counts as a full publication for each of the coauthors and each of the universities. In the fractional counting case, a research output is fractionally distributed between each coauthor and/or each organization. In a similar example, a publication coauthored by two authors from two different universities counts only as a half publication for each of the coauthors and each of the universities.

As already mentioned, the full counting method is the generally accepted one, but it can sometimes give unproportionally high scores to research made in extremely large collaborations, thus favoring the authors and organizations that participate in such projects. For more reading about multiauthorship and why this is important, please refer to Institute of Scientific Information's recent [Global Research Report – Multi-authorship and research analytics.](https://clarivate.com/webofsciencegroup/campaigns/global-research-report-multi-authorship-and-research-analysis/)

There are several types of fractional counting: author-level, organization-level, etc. The choice of a fractional counting method often depends on the purpose of the study, for more information on various fractional counting methods and their advantages for certain research tasks please refer to the following paper:

[Ludo Waltman, Nees Jan van Eck,
Field-normalized citation impact indicators and the choice of an appropriate counting method,
Journal of Informetrics,
Volume 9, Issue 4,
2015,
Pages 872-894,
ISSN 1751-1577,
https://doi.org/10.1016/j.joi.2015.08.001.](https://www.sciencedirect.com/science/article/pii/S1751157715300456)

For the purposes of this algorithm, we apply the author-level fractional counting method for the papers of an organization. The algorithm retrieves the publication data via Web of Science Expanded API and uses the organization affiliation, or verified organization profile a.k.a. "Organization-Enhanced" field in Web of Science Core Collection to count the fractional number of research output for a given time period. This is how it works:

#### The user needs to launch the main.py file and, on the RETRIEVE THROUGH API tab, enter:
1. Their Web of Science Expanded API key;
2. The Web of Science Core Collection advanced search query that they would like to run;
3. The name of the Affiliaiton that they would like to analyze for its fractional output

![Screenshot](/screenshots/GUI1.png)

And click the Run button.

The program will create an Excel file in the same project folder, where each Web of Science Core Collection record will have its Accession Number (a unique record identifier in the Web of Science Core Collection), the number of coauthors of this paper from the organization, and the fraction of an organization's input into this specific paper in the rightmost column. It will also create a separate tab in this file with the sum of the values for the fractional and full counting research out of this organization broken down by years.

![Screenshot](/screenshots/annual_dynamics_sheet.png)

![Screenshot](/screenshots/document_level_data_sheet.png)

Using Plotly library, the program also visualises the annual research output of the organization using both whole and fractional counting methods. Please note that the number of university's authors per paper is not visualized, but it's available for each document in the excel file on the document level data sheet.

It is also possible to use the LOAD EXCEL FILE tab to visualize the data previously retrieved and saved into Excel files:

![Screenshot](/screenshots/GUI2.png)


Although this is a good step in automating the routine work of calculating the research output using fractional counting method, we would like to address a few limitations:

1. Author-level fractional counting relies on links between "author" and "organization" fields in the Web of Science Core Collection record metadata. As there was no generally accepted practice to have this links in every published paper before mid-2007, this method of fractional counting will not return reliable results for the Web of Science Core Collection records with publication years before 2008.
2. The fractional counting value for a paper might sometimes show "0" if the paper is returned by Web of Science Core Collection Affiliation search but the record is not linked to the organization profile. If this is the case (the organization address in the metadata returned by the API will not have an "organization": ["pref": "Y"] field, and the same record in Web of Science user interface will not have a small triangle next to the organization address), the problem can be resolved by providing a "Suggest a correction" feedback right in the Web of Science interface.
3. The above can also happen even when the Web of Science record is linked to an organization profile, and the paper was published after the year 2007, but a single author name field which belongs to an author from your organization is not linked to your organization field. Most likely this would mean that there has been an issue between the publisher submitting publication metadata into Web of Science Core Collection and indexing this data by us, and the link between the author name and the organization name in this record can also be restored by providing a "Suggest a correction" feedback right in the Web of Science interface.
4. Organization affiliation can sometimes be missing in the regular Address list but appear in Reprint, or Corresponding, address list of certain papers. Although this is quite a rear event, it is technically possible to add a function for counting the corresponding addresses, but at the moment there is no consensus on how the presence and the amount of reprint addresses should affect the denominator of the fractional counting formula.
5. We do not encourage using this code right away for preparing the official research output reporting in the countries where the local regulators request such reports. Before submitting the external report based on this algorithm, we suggest double checking the numbers, and welcome any feedback to further improve this algorithm.
