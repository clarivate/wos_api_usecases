# ResearcherID-based Calculation for H-Index (excluding self-citations)

## A simple script to evaluate the H-index for a given ResearcherID both including and excluding coauthor self-citations. The script relies on retrieving the publication data via Web of Science Expanded API.


This is how it works:

#### In the code of the program, the user needs to enter:
1. Their Web of Science Expanded API key;
2. A Web of Science Core Collection advanced search query for a ResearcherID they would like to analyze;

And launch the code.

The program will query the Web of Science Expanded API, extract the necessary article metadata, an check each of the article linked to that specific ResearcherID as well as each article that cite them to check if self-citation occured at coauthor level. In case a self-citation is identified, an additional request is sent to Web of Science Expanded API to check the cited reference of the citing article and to correctly evaluate the number of citations (not citing documents) which are actually a self-citation.

Although this is a good step towards increasing the precision of self-citation calculation, we would like to address a few limitations of this approach:

1. Creating and updating ResearcherIDs is done by the authors themselves, and it cannot be guaranteed that a given ResearcherID search would return a 100% correct set of an author's papers. However, this algorithm can accept search queries by field different from ResearcherID, like Author Name, for example.
2. It is important that the coauthor-level analysis mentioned above works exactly what it is named for: coauthor-level self-citations, and we suggest that the users understand the differentce between coauthor self-citation and author self-citation which are not the same phenomenons in bibliometrics. Author self-citation identifies a self-citation event only if the author being analyzed appears on both cited and citing paper. On contrast, coauthor self-citation identifies a self-citation event even if the author being analyzed didn't cite their own research, but their coauthors did. While it is techincally possible to include only the author-level self-citation into this algorithm, we decided that including too many output metrics might actually make it harder to measure self-citations wiht this program. So, we decided to use the same coauthor-level self-citation approach used in the following two scholarly papers which we consider very important to understanding the self-citation methodology:

[Dag W. Aksnes,
A macro study of self-citation,
Scientometrics,
Volume 56, No. 2,
2003,
Pages 235-246,
https://doi.org/10.1023/A:1021919228368.](https://link.springer.com/article/10.1023%2FA%3A1021919228368)

[Wolfgang Glänzel, Bart Thus
Doesco-authorshipinflatetheshareofself-citations?,
Scientometrics,
Volume 61, No. 3,
2004,
Pages 395-404,
https://doi.org/10.1023/B:SCIE.0000045117.13348.b1.](https://link.springer.com/article/10.1023%2FB%3ASCIE.0000045117.13348.b1)

3. Self-citation might appear the most obvious way of citation manipulation. However, excessive self-citation rate for a given paper does not necessarily indicate that a citation manipulation has occured, simliarly self-citation rate of acceptable percentage (normally below 20-30%) doesn't guarantee that there hasn't been any scientific misconduct. In order to explore the potential citation manipulations with more reliability, it is advised to run a check for high concentration of citations to a paper coming from specific author or group of authors, publication sources, organizations, etc.