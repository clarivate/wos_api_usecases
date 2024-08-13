# Most recent Web of Science records

![Example](/most_recent_wos_items/screenshots/screenshot.png)


## A simple Python script that uses Web of Science Starter API and Flask to create an HTML page with 5 most recent Web of Science Core Collection records

Simply edit the Web of Science Core Collection advanced search query constant in the code, and set the number of the most recent Web of Science documents that you want to display from this query. Ideal for placing an overview of the most recent scholarly articles published by your researchers on your webpage, and update it on anything up to a daily basis.

The summary contains the document title, being hyperlinked to that document record on Web of Science platform, the authors list, with hyperlinks to the author profiles, and the source title, with a hyperlink to a journal profile on Jurnal Citation Reports.

Please note that if a user doesn't have access to Web of Science, they might be unable to see the unclaimed researcher profiles that are also linked from the Flask page. In order to make sure the links exist only for the claimed researcher profiles, a separate check for this status is required. It can be done using Web of Science Expanded API or, preferrably, Researcher API.

Also, in case the source is not a journal, or is a journal but is unavailable in Journal Citaton Reports, the link to the latter won't be added.

As always, we welcome your feedback on this code.