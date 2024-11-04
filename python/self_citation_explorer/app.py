"""
A Flask app that allows retrieving, processing, and visualizing the
Web of Science Grants Index data.

Main app file: manage Flask interface actions and rendering, manage the
main function that is launched on clicking the "Run" button.
"""


from flask import Flask, render_template, request
from data_processing import run_button
from visualizations import visualize_excel
from api_operations import validate_search_query
from apikeys import EXPANDED_APIKEY

app = Flask(__name__)


@app.route(rule="/", methods=['POST', 'GET'])
def start_menu():
    """Manage Flask interface actions and rendering.

    :return: render_template.
    """

    # Validating search query or running the search
    if request.method == 'POST' and 'search_query' in request.form.keys():
        button = request.form['button']
        search_query = request.form['search_query']
        return search_section(button, search_query)

    # Loading Excel file
    if request.method == 'POST' and 'filename' in request.form.keys():
        file = request.form['filename']
        return load_file_section(file)

    return render_template('index.html', search_query='')


def search_section(button, search_query):
    """Manage the actions and processes for the page search section.

    :param button: str.
    :param search_query: str.
    :return: render_template.
    """

    # Validate search query
    if search_query != '' and button == 'validate':
        response = validate_search_query(EXPANDED_APIKEY, search_query)
        if response[0] == 200:
            return render_template(
                'index.html',
                message=f'Records found: {response[1]}',
                search_query=search_query
            )

        return render_template(
            'index.html',
            message=f'Request status: {response[0]}, message: {response[1]}',
            search_query=search_query
        )

    # Run search query
    if search_query != '' and button == 'run':
        safe_filename, plot = run_button(EXPANDED_APIKEY, search_query)
        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            plot=plot
        )

    return render_template('index.html', search_query='')


def load_file_section(file):
    """Manage the actions and processes for the load file search
    section.

    :param file: str.
    :return: render_template.
    """
    if file == '':
        return render_template('index.html', search_query='')
    plot = visualize_excel(f'downloads/{file}')
    return render_template('index.html', plot=plot, index=0)


if __name__ == '__main__':
    app.run(debug=True)
