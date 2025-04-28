"""
A Flask application with a simple graphical user interface to retrieve
Web of Science Researcher Profiles using Web of Science Researcher API.

Main app file: manage Flask interface actions and rendering.
"""

from flask import Flask, render_template, request
from data_processing import run_button
from api_operations import validate_search_query
from apikeys import RESEARCHER_APIKEY


app = Flask(__name__)

plots_list = []


@app.route(rule="/", methods=['POST', 'GET'])
def start_menu() -> str:
    """Manage Flask interface actions and rendering."""

    if request.method == 'POST' and 'search_query' in request.form.keys():
        button = request.form['button']
        search_query = request.form['search_query']
        return search_section(button, search_query)

    return render_template('index.html', search_query='')


def search_section(button: str, search_query: str) -> str:
    """Manage the actions and processes for the page search section."""

    full_profiles = 'check' in request.form.keys()

    if search_query != '' and button == 'validate':
        return render_validation_results(search_query, full_profiles)

    if search_query != '' and button == 'run':
        safe_filename = run_button(RESEARCHER_APIKEY, search_query, full_profiles)

        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            full_profiles=full_profiles
        )

    return render_template(
        'index.html',
        search_query='',
        full_profiles=full_profiles
    )


def render_validation_results(search_query: str, full_profiles: bool) -> str:
    """Get the validation API call results, render them on the webpage
    depending on whether the result was an error or ok."""

    response = validate_search_query(RESEARCHER_APIKEY, search_query)
    if response[0] == 200:
        return render_template(
            'index.html',
            message=f'Researcher Profiles found: {response[1]}',
            search_query=search_query,
            full_profiles=full_profiles
        )

    return render_template(
        'index.html',
        error_message=f'Request status: {response[0]}, message: {response[1]}',
        search_query=search_query,
        full_profiles=full_profiles
    )


if __name__ == '__main__':
    app.run(debug=True)
