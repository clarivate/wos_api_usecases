# Most recent Web of Science records

![Example](screenshots/screenshot.png)


## A simple Python app that uses Web of Science Starter API and Flask to create an HTML page with 5 most recent Web of Science Core Collection records

### How to use this script
Simply open the main.py file with your code editor and:
1. Create a new python file named apikey.py in the same project folder, and add only one line of code there, namely set up a constant named STARTER_APIKEY and pass your Web of Science Starter API key as a string value, i.e.:
```
STARTER_APIKEY = "mY574r73r4p1k3y1$$0m37h1Ngl1k37h15"
```
2. Edit the Web of Science Core Collection advanced search query constant right in the code
3. Set the number of the most recent Web of Science documents that you want to display from this query.
And launch the code.

The script will create a development Flask page which you will be able to open at http://127.0.0.1/5000, and it will contain the summary of 5 most recent Web of Science documents according to your search query. With some styling, this summary would be ideal for placing an overview of the most recent scholarly articles published by your researchers on your webpage, and update it on anything up to a daily basis.

The summary contains the document title, being hyperlinked to that document record on Web of Science platform, the authors list, with hyperlinks to the author profiles, and the source title, with a hyperlink to a journal profile on Journal Citation Reports.

Please note that if a user doesn't have access to Web of Science, they might be unable to see the unclaimed researcher profiles that are also linked from the Flask page. In order to make sure the links exist only for the claimed researcher profiles, a separate check for this status is required. It can be done using Web of Science Expanded API or, preferably, Researcher API.

Also, in case the source is not a journal, or is a journal but is unavailable in Journal Citation Reports, the link to the latter won't be added.

As always, we welcome your feedback on this code.