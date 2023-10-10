"""
Most recent Web of Science records

A simple Python script that uses Web of Science Starter API and Flask to create an HTML page with
5 most recent Web of Science Core Collection records

Simply edit the Web of Science Core Collection advanced search query constant in the code, and it
will bring up a page with 5 most recent Web of Science documents for this query. Ideal for placing
an overview of the most recent scholarly articles published by your researchers on your webpage,
and update it on a daily basis.

The summary contains the document title, being hyperlinked to that document record on Web of Science
platform, the authors list, and the source title.

As always, we welcome your feedback on this code.
"""

import requests
from flask import Flask
from apikey import STARTER_APIKEY

# Search query for which to calculate the citation report
SEARCH_QUERY = 'OG=Clarivate'
RECORDS_TO_DISPLAY = 5

initial_request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents?q={SEARCH_QUERY}'
                               f'&limit=50&page=1&db=WOS&sortField=PY+D', headers={'X-ApiKey': STARTER_APIKEY})
initial_json = initial_request.json()
for wos_document in initial_json['hits'][:RECORDS_TO_DISPLAY]:
    if 'issn' not in wos_document['identifiers']:
        wos_document['journal_link'] = None
    else:
        journal_request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/journals?'
                                       f'issn={wos_document["identifiers"]["issn"]}',
                                       headers={'X-ApiKey': STARTER_APIKEY})
        journal_json = journal_request.json()
        if journal_json['hits']:
            wos_document['source']['sourceTitle'] = f"<a href={journal_json['hits'][0]['links'][0]['url']}" \
                + wos_document['source']['sourceTitle'] + '</a>'

app = Flask(__name__)


def create_authors_list(doc):
    """Convert the list of authors into a shortened str and adds "et al." if the author count
    is over 3.

    :param doc: dict from API JSON.
    :return: str.
    """
    authors = []
    for author in doc['names']['authors']:
        if 'researcherId' in author:
            profile_link = (f'https://www.webofscience.com/wos/author/record/'
                            f'{author["researcherId"]}')
            authors.append(f'<a href={profile_link}>{author["wosStandard"]}</a>')
        else:
            authors.append(author["wosStandard"])
    if len(doc['names']['authors']) < 4:
        return ', '.join(authors)
    return f"{', '.join(authors[:3])} et al."


def format_title_length(doc):
    """Shorten the title str if it's over 100 symbols.
    is over 3.

    :param doc: dict from API JSON.
    :return: str.
    """
    if len(doc['title']) > 100:
        return f"{doc['title'][:100]}..."
    return doc['title']


@app.route("/")
def most_recent_wos_records():
    font_tag = '<p style="font-family:\'Source Sans Pro\'; line-height: 0.5">'
    output = f'{font_tag}Most Recent Documents of: {SEARCH_QUERY}:<br><br></p>'
    for i, record in enumerate(initial_json['hits'][:RECORDS_TO_DISPLAY]):
        authors = create_authors_list(record)
        title = format_title_length(record)

        output += (f'{font_tag}{i + 1}:  Title: <a href={record["links"]["record"]}>'
                   f'{title}</a><br></p>')
        output += f'{font_tag}    By: {authors}<br>'
        output += (f'{font_tag}    Published in: {record["source"]["sourceTitle"]}'
                   f'<br><br></p>')
    return output


app.run()
