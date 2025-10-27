"""
A Flask application with a simple graphical user interface to retrieve
Web of Science Researcher Profiles using Web of Science Researcher API.

Main app file: manage Flask interface actions and rendering.
"""

from flask import Flask, Response, render_template, request
import time, state, json
from data_processing import main
from api_operations import validate_search_query


app = Flask(__name__)

plots_list = []


@app.route("/stream")
def stream():
    def generate():
        last_progress = -1
        last_task = ""
        while True:
            if (state.progress != last_progress) or (state.current_task != last_task):
                data = {
                    "task": state.current_task,
                    "progress": state.progress
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_progress = state.progress
                last_task = state.current_task
            time.sleep(0.2)
    return Response(generate(), mimetype="text/event-stream")


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

    options = {
        'full_profiles': 'full_profiles' in request.form.keys(),
        'documents': 'documents' in request.form.keys(),
        'peer_reviews': 'peer_reviews' in request.form.keys()
    }

    if search_query != '' and button == 'validate':
        return render_validation_results(search_query, options)

    if search_query != '' and button == 'run':
        safe_filename = main(search_query, options)

        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            full_profiles=options['full_profiles'],
            documents=options['documents'],
            peer_reviews=options['peer_reviews']
        )

    return render_template(
        'index.html',
        search_query='',
        full_profiles=options['full_profiles'],
        documents=options['documents'],
        peer_reviews=options['peer_reviews']
    )


def render_validation_results(search_query: str, options: dict) -> str:
    """Get the validation API call results, render them on the webpage
    depending on whether the result was an error or ok."""

    response = validate_search_query(search_query)
    if response[0] == 200:

        # Calculating the number of API calls estimation
        search_api_calls = (response[1] - 1) // 50 + 1
        full_profiles_api_calls = int(options['full_profiles']) * response[1]
        documents_api_calls = int(options['documents']) * response[1]
        peer_reviews_api_calls = int(options['peer_reviews']) * response[1]
        estimation = (
                search_api_calls + full_profiles_api_calls +
                documents_api_calls + peer_reviews_api_calls
        )

        documents_warning = ' (but probably more)' if options['documents'] else ''

        return render_template(
            'index.html',
            message=f'Researcher Profiles found: <strong>{response[1]}'
                    f'</strong>.<br>'
                    f'Your request is going to take <strong> at least '
                    f'{estimation}</strong> API calls{documents_warning}.<br>'
                    f'You\'ve got <strong>{response[2]}</strong> API calls '
                    f'left until the end of today.<br>',
            search_query=search_query,
            full_profiles=options['full_profiles'],
            documents=options['documents'],
            peer_reviews=options['peer_reviews']
        )

    return render_template(
        'index.html',
        error_message=f'Request status: {response[0]}, message: {response[1]}',
        search_query=search_query,
        full_profiles=options['full_profiles'],
        documents=options['documents'],
        peer_reviews=options['peer_reviews']
    )


if __name__ == '__main__':
    app.run(debug=True)
