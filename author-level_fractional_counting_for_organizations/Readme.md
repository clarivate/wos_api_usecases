Author-level fractional counting for organization
======

A simple script to calculate the number of papers for an organization using fractional counting approach and retrieving publication data via Web of Science Expanded API
------

The default way of counting papers and citations to them, being currently used in Web of Science, InCites, and other Clarivate resources, is called whole counting, or full counting method. In the case of full counting, a research output is fully attributed to each of the authors and/or each of the affiliated organizations. For example, a publication coauthored by two authors from two different universities counts as a full publication for each of the coauthors and each of the universities. In the fractional counting case, a research output is fractionally distributed between each coauthor and/or each organization. In a similar example, a publication coauthored by two authors from two different universities counts only as a half publication for each of the coauthors and each of the universities.

As already mentioned, the full counting method is the generally accepted one, but it can sometimes give unproportionally high scores to research made in extremely large collaborations, thus favoring the authors and organizations that participate in such projects. For more reading about multiauthorship and why this is important, please refer to Institue of Scientific Information's recent [Global Research Report – Multi-authorship and research analytics.](https://clarivate.com/webofsciencegroup/campaigns/global-research-report-multi-authorship-and-research-analysis/)

There are several types of fractional counting: author-level, organiation-level, etc. The choice of a fractional counting method often depends on the purpose of the study, for more information on various fractional counting methods and their advantages for certain research tasks please refer to the following paper:

[Ludo Waltman, Nees Jan van Eck,
Field-normalized citation impact indicators and the choice of an appropriate counting method,
Journal of Informetrics,
Volume 9, Issue 4,
2015,
Pages 872-894,
ISSN 1751-1577,
https://doi.org/10.1016/j.joi.2015.08.001.](https://www.sciencedirect.com/science/article/pii/S1751157715300456)

For the purposes of this algorithm, we apply the author-level fractional counting method for the papers of an organization. The algorithm retrieves the publication data via Web of Science Expanded API and uses the organization affiliation, or verified organization profile a.k.a. "Organization-Enhanced" field in Web of Science Core Collection to count the fractional number of research output for a given time period. This is how it works:

#### The user needs to enter:
1. Their Web of Science Expanded API key;
2. Their Web of Science Core Collection organization profile name;
3. The desired time period for analysis,

And launch the code.

The program will create a .csv-file in the same project folder, where each Web of Science Core Collection record will have its Web of Science Core Collection accession number (a unique record identifier in the Web of Science Core Collection), the number of coauthors of this paper from the organization, and the fraction of an organization's input into this specific paper in the rightmost column. The sum of the values in the rightmost column is the author-level fractional value for the research output of this organization for the specified period of time.

Although this is a good step in automating the routine work of calculating the research output using fractional counting method, we would like to address a few limitations:

1. The fractional counting value for a paper might sometimes show "0" if the paper is returned by Web of Science Core Collection Affiliation search but the record is not linked to the organization profile. If this is the case (the organization address in the metadata returned by the API will not have an "organization": ["pref": "Y"] field, and the same record in Web of Science user interface will not have a small triangle next to the organization address), the problem can be resolved by providing a "Suggest a correction" feedback right in the Web of Science interface.
2. The above can also happen even when the Web of Science record is linked to an organization profile. This can occur when the author name in the record is not linked to the organization. Most likely this would mean that there has been an issue between the publisher submitting publication metadata into Web of Science Core Collection and indexing this data by us, and the link between the author name and the organization name in this record can also be restored by providing a "Suggest a correction" feedback right in the Web of Science interface.
3. We do not encourage using this code right away for preparing the official research output reporting in the countries where the local regulators request such reports. Before submitting the external report based on this algorithm, we suggest double checking the numbers, and welcome any feedback to further improve this algorithm.