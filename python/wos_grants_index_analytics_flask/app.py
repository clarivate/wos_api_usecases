"""
A Flask app that allows retrieving, processing, and visualizing the
Web of Science Grants Index data.

Main app file: manage Flask interface actions and rendering.
"""

from flask import Flask, render_template, request
from data_processing import run_button
from visualizations import visualize_excel
from api_operations import validate_search_query
from apikeys import EXPANDED_APIKEY

app = Flask(__name__)

plots_list = []


@app.route(rule="/", methods=['POST', 'GET'])
def start_menu() -> str:
    """Manage Flask interface actions and rendering.

    :return: Flask render_template.
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

    # Switching between visualizations
    if request.method == 'POST' and 'button' in request.form.keys():
        visualizations = {
            "grant_funding_by_year": plots_list[0],
            "top_principal_investigators": plots_list[1],
            "top_pi_institutions": plots_list[2],
            "top_funders": plots_list[3],
            "average_grant_volume_per_year": plots_list[4],
            "top_grants_by_associated_wos_records": plots_list[5]
        }
        if request.form['button'] in visualizations:
            for key, value in visualizations.items():
                if request.method == 'POST' and request.form['button'] == key:
                    return render_template(
                        'index.html',
                        plot=value,
                        index=plots_list.index(value))

    return render_template('index.html', search_query='')


def search_section(button: str, search_query: str) -> str:
    """Manage the actions and processes for the page search section.

    :param button: str.
    :param search_query: str.
    :return: flask.render_template.
    """
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
    if search_query != '' and button == 'run':
        plots_list.clear()
        safe_filename, plots = run_button(EXPANDED_APIKEY, search_query)
        plots_list.extend(plots)
        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            plot=plots_list[0]
        )
    return render_template('index.html', search_query='')


def load_file_section(file: str) -> str:
    """Manage the actions and processes for the load file search
    section.

    :param file: str.
    :return: flask.render_template
    """

    plots_list.clear()
    if file == '':
        return render_template('index.html', search_query='')
    plots = visualize_excel(f'downloads/{file}')
    plots_list.extend(plots)

    return render_template('index.html', plot=plots_list[0], index=0)


if __name__ == '__main__':
    app.run(debug=True)
