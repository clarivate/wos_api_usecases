"""
A Flask app that allows retrieving Web of Science Core Collection data
into a VOSviewer-compatible tab-delimited text file.

Main app file: manage Flask interface actions and rendering, manage the
main function that is launched on clicking the "Run" button.
"""

from flask import Flask, render_template, request
from apikeys import EXPANDED_APIKEY
from api_operations import validate_search_query
from data_processing import run_button

app = Flask(__name__)


@app.route(rule='/', methods=['POST', 'GET'])
def start_menu():
    """Manage Flask interface actions and rendering.

    :return: Flask render_template.
    """
    if request.method == 'POST' and 'search_query' in request.form.keys():
        button = request.form['button']
        search_query = request.form['search_query']
        return search_section(button, search_query)
    return render_template('index.html')


def search_section(button, search_query):
    """Manage the actions and processes for the page search section.

        :param button: str.
        :param search_query: str.
        :return: render_template object.
        """
    cited_refs = 'check' in request.form.keys()
    if search_query != '' and button == 'validate':
        response = validate_search_query(EXPANDED_APIKEY, search_query)
        if response[0] == 200:
            return render_template(
                'index.html',
                message=f'Records found: {response[1]}',
                search_query=search_query,
                cited_refs=cited_refs
            )
        return render_template(
            'index.html',
            message=f'Request status: {response[0]}, message: {response[1]}',
            search_query=search_query,
            cited_refs=cited_refs
        )
    if search_query != '' and button == 'run':
        safe_filename = run_button(EXPANDED_APIKEY, search_query, cited_refs)
        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            cited_refs=cited_refs
        )
    return render_template(
        'index.html',
        search_query='',
        cited_refs=cited_refs
    )


if __name__ == '__main__':
    app.run(debug=True)
