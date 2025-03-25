"""
A Flask application with a simple graphical user interface to analyse
and visualise organizational research output using fractional counting
approach that retrieves data using Web of Science Expanded API.

Main app file: manage Flask interface actions and rendering.
"""

from flask import Flask, render_template, request
from data_processing import run_button
from api_operations import validate_search_query
from visualizations import visualize_excel
from apikeys import EXPANDED_APIKEY


app = Flask(__name__)

plots_list = []


@app.route(rule="/", methods=['POST', 'GET'])
def start_menu():
    """Manage Flask interface actions and rendering.

    :return: render_template.
    """

    # Validating search query or running the search
    if request.method == 'POST' and 'search_query' in request.form.keys():
        button = request.form['button']
        search_query = request.form['search_query']
        org_name = request.form['org_name']
        return search_section(button, search_query, org_name)

    # Loading Excel file
    if request.method == 'POST' and 'filename' in request.form.keys():
        file = request.form['filename']
        return load_file_section(file)

    return render_template('index.html', search_query='')


def search_section(button, search_query, org_name):
    """Manage the actions and processes for the page search section.

    :param button: str.
    :param search_query: str.
    :param org_name: str.
    :return: render_template.
    """
    if search_query != '' and button == 'validate':
        return render_validation_results(search_query, org_name)
    if search_query != '' and button == 'run':
        plots_list.clear()
        org_name_quoted = False
        if org_name[0] == org_name[-1] == '"':
            org_name_quoted = True
            org_name = org_name[1:-1]
        safe_filename, plots = run_button(EXPANDED_APIKEY, search_query, org_name)
        for plot in plots:
            plots_list.append(plot)
        if org_name_quoted:
            return render_template(
                'index.html',
                filename=safe_filename,
                search_query=search_query,
                org_name=f'"{org_name}"',
                plot=plots_list[0],
                index=0
            )
        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            org_name=org_name,
            plot=plots_list[0],
            index=0
        )
    return render_template('index.html', search_query='')


def render_validation_results(search_query, org_name):
    """Get the validation API call results, render them on the webpage
    depending on whether the result was an error or ok.

    :param search_query: str.
    :param org_name: str.
    result: render_template.
    """
    response_1 = validate_search_query(EXPANDED_APIKEY, search_query)
    response_2 = validate_search_query(EXPANDED_APIKEY, f'OG={org_name}')
    if response_1[0] == 200 and (response_2[0] == 200 and response_2[1] != 0):
        return render_template(
            'index.html',
            message_1=f'Records found: {response_1[1]}',
            search_query=search_query,
            org_name=org_name
        )
    if response_1[0] == 200 and response_2[0] != 200:
        return render_template(
            'index.html',
            error_message_2=f'Please check the affiliation name: '
                            f'{response_2[1]}',
            search_query=search_query,
            org_name=org_name
        )
    if response_1[0] == 200 and response_2[1] == 0:
        return render_template(
            'index.html',
            error_message_2=f'Please check the affiliation name: '
                            f'{response_2[1]} records found',
            search_query=search_query,
            org_name=org_name
        )
    if response_1[0] != 200 and response_2[0] == 200 and response_2[1] != 0:
        return render_template(
            'index.html',
            error_message_1=f'Request status: {response_1[0]}, message: '
                            f'{response_1[1]}',
            search_query=search_query,
            org_name=org_name
        )
    if response_1[0] != 200 and response_2[0] == 200 and response_2[1] == 0:
        return render_template(
            'index.html',
            error_message_1=f'Request status: {response_1[0]}, message: '
                            f'{response_1[1]}',
            error_message_2=f'Please check the affiliation name: '
                            f'{response_2[1]} records found',
            search_query=search_query,
            org_name=org_name
        )

    return render_template(
        'index.html',
        error_message_1=f'Request status: {response_1[0]}, message: '
                        f'{response_1[1]}',
        error_message_2=f'Please check the affiliation name: {response_2[1]}',
        search_query=search_query,
        org_name=org_name
    )


def load_file_section(file):
    """Manage the actions and processes for the load file search
    section.

    :param file: str.
    :return: render_template.
    """
    plots_list.clear()
    if file == '':
        return render_template('index.html', search_query='')
    plots = visualize_excel(f'downloads/{file}')
    for plot in plots:
        plots_list.append(plot)
    return render_template('index.html', plot=plots_list[0], index=0)


if __name__ == '__main__':
    app.run(debug=True, port=5002)
