import requests
from flask import Flask
from apikey import STARTER_APIKEY

# Search query for which to calculate the citation report
SEARCH_QUERY = 'OG=Clarivate'

initial_request = requests.get(f'https://api.clarivate.com/apis/wos-starter/v1/documents?q={SEARCH_QUERY}'
                               f'&limit=50&page=1&db=WOS&sortField=PY+D', headers={'X-ApiKey': STARTER_APIKEY})
initial_json = initial_request.json()
app = Flask(__name__)


def create_authors_list(doc):
    """Convert the list of authors into a shortened str and adds "et al." if the author count
    is over 3.

    :param doc: dict from API JSON.
    :return: str.
    """
    if len(doc['names']['authors']) < 4:
        return ', '.join([author['wosStandard'] for author in doc['names']['authors']])
    return f"{', '.join([author['wosStandard'] for author in doc['names']['authors'][:4]])} et al."


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
def text():
    font_tag = '<p style="font-family:\'Source Sans Pro\'; line-height: 0.5">'
    output = (f'{font_tag}Most Recent Documents of: {SEARCH_QUERY}:<br><br></p>')
    for i, wos_document in enumerate(initial_json['hits'][:5]):
        authors = create_authors_list(wos_document)
        title = format_title_length(wos_document)
        output += (f'{font_tag}{i + 1}:  Title: <a href={wos_document["links"]["record"]}>'
                   f'{title}</a><br></p>')
        output += f'{font_tag}    By: {authors}<br>'
        output += (f'{font_tag}    Published in: {wos_document["source"]["sourceTitle"]}'
                   f'<br><br></p>')
    return output

app.run()
