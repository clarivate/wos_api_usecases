"""
A Flask application with a simple graphical user interface to analyse
and visualise patents analytics and relations between scholarly articles
and patent documents. The application retrieves data using Web of
Science Expanded API.

Main app file: manage Flask interface actions and rendering.
"""

from flask import Flask, render_template, request
from data_processing import (
    run_button_wos,
    run_button_dii,
    run_button_trends
)
from api_operations import (
    validate_search_query_wos,
    validate_search_query_dii
)
from visualizations import visualize_excel


app = Flask(__name__)

plots_list = []


@app.route(rule='/')
def wos_search() -> str:
    """Render landing page."""

    return render_template('index.html')


@app.route(rule='/dii')
def dii_search() -> str:
    """Render patent search page."""

    return render_template('dii.html')


@app.route(rule='/trends')
def trends_search() -> str:
    """Render trends search page."""

    return render_template('trends.html')


@app.route(rule="/", methods=['POST', 'GET'])
def start_menu_wos() -> str:
    """Manage Flask interface actions and rendering for Technological
    Impact tab (Web of Science Core Collection search).
    """

    # Validating search query or running the search
    if request.method == 'POST' and 'search_query' in request.form.keys():
        button = request.form['button']
        search_query = request.form['search_query']
        return search_section_wos(button, search_query)

    # Loading Excel file
    if request.method == 'POST' and 'filename' in request.form.keys():
        file = request.form['filename']
        return load_file_section_wos(file)

    # Switching between visualizations
    if request.method == 'POST' and 'button' in request.form.keys():
        visualizations = {
            'key_metrics': plots_list[0],
            'top_authors': plots_list[1],
            'years': plots_list[2],
            'top_assignees_treemap': plots_list[3],
            'top_inventors_treemap': plots_list[4],
            'top_countries_applied': plots_list[5],
            'top_countries_granted': plots_list[6]
        }
        if request.form['button'] in visualizations:
            for key, value in visualizations.items():
                if request.method == 'POST' and request.form['button'] == key:
                    return render_template(
                        'index.html',
                        plot=value,
                        index=plots_list.index(value))
    return render_template('index.html', search_query='')


@app.route(rule="/dii", methods=['POST', 'GET'])
def start_menu_dii() -> str:
    """Manage Flask interface actions and rendering for Inventions tab
    (Derwent Innovations Index search).
    """

    # Validating search query or running the search
    if request.method == 'POST' and 'search_query' in request.form.keys():
        button = request.form['button']
        search_query = request.form['search_query']
        return search_section_dii(button, search_query)

    # Loading Excel file
    if request.method == 'POST' and 'filename' in request.form.keys():
        file = request.form['filename']
        return load_file_section_dii(file)

    # Switching between visualizations
    if request.method == 'POST' and 'button' in request.form.keys():
        visualizations = {
            'key_metrics': plots_list[0],
            'years': plots_list[1],
            'top_assignees_treemap': plots_list[2],
            'top_inventors_treemap': plots_list[3],
            'top_countries_applied': plots_list[4],
            'top_countries_granted': plots_list[5]
        }
        if request.form['button'] in visualizations:
            for key, value in visualizations.items():
                if request.method == 'POST' and request.form['button'] == key:
                    return render_template(
                        'dii.html',
                        plot=value,
                        index=plots_list.index(value))
    return render_template('dii.html', search_query='')


@app.route(rule="/trends", methods=['POST', 'GET'])
def start_menu_trends() -> str:
    """Manage Flask interface actions and rendering for Trends tab
    (Same Web of Science Core Collection and Derwent Innovations
    Topical Index search).
    """

    # Validating search query or running the search
    if request.method == 'POST' and 'search_query' in request.form.keys():
        button = request.form['button']
        search_query = f"TS={request.form['search_query']}"
        return search_section_trends(button, search_query)

    # Loading Excel file
    if request.method == 'POST' and 'filename' in request.form.keys():
        file = request.form['filename']
        return load_file_section_trends(file)

    return render_template('trends.html', search_query='')


def search_section_wos(button: str, search_query: str) -> str:
    """Manage the actions and processes for the page search section
    - Technological Impact tab.
    """

    if search_query != '' and button == 'validate':
        return render_validation_results(search_query, 'WOS')

    if search_query != '' and button == 'run':
        plots_list.clear()
        safe_filename, plots = run_button_wos(search_query)
        plots_list.extend(plots)

        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            plot=plots_list[0],
            index=0
        )

    return render_template('index.html', search_query='')


def search_section_dii(button: str, search_query: str) -> str:
    """Manage the actions and processes for the page search section
    - Inventions tab.
    """

    if search_query != '' and button == 'validate':
        return render_validation_results(search_query, 'DIIDW')

    if search_query != '' and button == 'run':
        plots_list.clear()
        safe_filename, plots = run_button_dii(search_query)
        plots_list.extend(plots)

        return render_template(
            'dii.html',
            filename=safe_filename,
            search_query=search_query,
            plot=plots_list[0],
            index=0
        )

    return render_template('dii.html', search_query='')


def search_section_trends(button: str, search_query: str) -> str:
    """Manage the actions and processes for the page search section
    - Trends tab.
    """

    if search_query != '' and button == 'validate':
        return render_validation_results(search_query, 'BOTH')

    if search_query != '' and button == 'run':
        plots_list.clear()
        safe_filename, plots = run_button_trends(search_query)
        plots_list.extend(plots)
        return render_template(
            'trends.html',
            filename=safe_filename,
            search_query=search_query[3:],
            plot=plots_list[0],
            index=0
        )
    return render_template('trends.html', search_query='')


def render_validation_results(search_query: str, db: str) -> str:
    """Get the validation API call results, render them on the webpage
    depending on whether the result was an error or ok - for Scholarly
    Documents tab.
    """

    if db == 'BOTH':
        return render_trends_query(search_query)

    if db == 'WOS':
        return render_wos_query(search_query)

    return render_dii_query(search_query)


def render_trends_query(search_query: str) -> str:
    """Interpret the validation API request to both databases, render
    the webpage and messages accordingly.
    """

    response_1 = validate_search_query_wos(search_query)
    response_2 = validate_search_query_dii(search_query)
    if response_1[0] == response_2[0] == 200:
        return render_template(
            'trends.html',
            message_1=f'Web of Science documents found: {response_1[1]}',
            message_2=f'Derwent Innovation Index Patent Families found: '
                      f'{response_2[1]}',
            search_query=search_query[3:]
        )
    if response_1[0] == 200:
        return render_template(
            'trends.html',
            message_1=f'Web of Science documents found: {response_1[1]}',
            error_message_2=f'Derwent Innovation Index request status:'
                            f'{response_2[0]}, message: {response_2[1]}',
            search_query=search_query[3:]
        )
    if response_2[0] == 200:
        return render_template(
            'trends.html',
            error_message_1=f'Web of Science request status: {response_1[0]}, '
                            f'message: {response_1[1]}',
            message_2=f'Derwent Innovation Index Patent Families found: '
                      f'{response_2[1]}',
            search_query=search_query[3:]
        )
    return render_template(
        'trends.html',
        error_message_1=f'Web of Science request status: {response_1[0]}, '
                        f'message: {response_1[1]}',
        error_message_2=f'Derwent Innovation Index request status:'
                        f'{response_2[0]}, message: {response_2[1]}',
        search_query=search_query[3:]
    )


def render_wos_query(search_query: str) -> str:
    """Interpret the validation API request to Web of Science Core
    Collection, render the webpage and messages accordingly.
    """
    response = validate_search_query_wos(search_query)
    if response[0] == 200:
        return render_template(
            'index.html',
            message_1=f'Records found: {response[1]}',
            search_query=search_query
        )
    return render_template(
        'index.html',
        error_message_1=f'Request status: {response[0]}, message: '
                        f'{response[1]}',
        search_query=search_query
    )


def render_dii_query(search_query: str) -> str:
    """Interpret the validation API request to Derwent Innovations
    Index, render the webpage and messages accordingly.
    """
    response = validate_search_query_dii(search_query)
    if response[0] == 200:
        return render_template(
            'dii.html',
            message_1=f'Records found: {response[1]}',
            search_query=search_query
        )
    return render_template(
        'dii.html',
        error_message_1=f'Request status: {response[0]}, message: '
                        f'{response[1]}',
        search_query=search_query
    )


def load_file_section_wos(file: str) -> str:
    """Manage the actions and processes for the load file search
    section - Scholarly Documents tab.
    """

    plots_list.clear()
    if file == '':
        return render_template('index.html', search_query='')
    plots = visualize_excel(f'downloads/woscc/{file}')
    plots_list.extend(plots)

    return render_template('index.html', plot=plots_list[0], index=0)


def load_file_section_dii(file: str) -> str:
    """Manage the actions and processes for the load file search
    section - Inventions tab.
    """

    plots_list.clear()
    if file == '':
        return render_template('dii.html', search_query='')
    plots = visualize_excel(f'downloads/dii/{file}')
    plots_list.extend(plots)

    return render_template('dii.html', plot=plots_list[0], index=0)


def load_file_section_trends(file: str) -> str:
    """Manage the actions and processes for the load file search
    section - Trends tab.
    """

    plots_list.clear()
    if file == '':
        return render_template('trends.html', search_query='')
    plots = visualize_excel(f'downloads/trends/{file}')
    plots_list.extend(plots)

    return render_template('trends.html', plot=plots_list[0], index=0)


if __name__ == '__main__':
    app.run(debug=True)
