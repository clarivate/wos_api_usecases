"""
A Flask app that allows retrieving, processing, and visualizing the
Web of Science Grants Index data.

Main app file: manage Flask interface actions and rendering, manage the
main function that is launched on clicking the "Run" button.
"""

from datetime import date
import pandas as pd
from flask import Flask, render_template, request
from data_processing import get_usd_rates, fetch_data
from visualizations import visualize_data, visualize_excel
from api_operations import validate_search_query, retrieve_wos_metadata_via_api
from apikeys import EXPANDED_APIKEY

app = Flask(__name__)

plots_list = []


@app.route(rule="/", methods=['POST', 'GET'])
def start_menu():
    """Manage Flask interface actions and rendering

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
            "top_grant_receivers": plots_list[1],
            "top_funders": plots_list[2],
            "average_grant_volume_per_year": plots_list[3],
            "top_grants_by_associated_wos_records": plots_list[4]
        }
        if request.form['button'] in visualizations:
            for key, value in visualizations.items():
                if request.method == 'POST' and request.form['button'] == key:
                    return render_template(
                        'index.html',
                        plot=value,
                        index=plots_list.index(value))
    return render_template('index.html', search_query='')


def search_section(button, search_query):
    """Manage the actions and processes for the page search section.

    :param button: str.
    :param search_query: str.
    :return: render_template object.
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
        safe_filename, plots = run_button_main_function(EXPANDED_APIKEY, search_query)
        for plot in plots:
            plots_list.append(plot)
        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            plot=plots_list[0]
        )
    return render_template('index.html', search_query='')


def load_file_section(file):
    """Manage the actions and processes for the load file search
    section.

    :param file:
    :return:
    """
    plots_list.clear()
    if file == '':
        return render_template('index.html', search_query='')
    plots = visualize_excel(f'downloads/{file}')
    for plot in plots:
        plots_list.append(plot)
    return render_template('index.html', plot=plots_list[0], index=0)


def run_button_main_function(apikey, search_query):
    """When the 'Run' button is pressed, manage all the API operations,
    data processing, and visualizations

    :param apikey: str.
    :param search_query: str.
    :return: str, tuple.
    """
    records_per_page = 100
    grants_list = []
    usd_rates = get_usd_rates()
    initial_json = retrieve_wos_metadata_via_api(apikey, search_query, records_per_page)
    for record in initial_json['Data']['Records']['records']['REC']:
        grants_list.append(fetch_data(record, usd_rates))
    total_results = initial_json['QueryResult']['RecordsFound']
    requests_required = ((total_results - 1) // records_per_page) + 1
    print(f'Total Web of Science API requests required: {requests_required}.')
    for i in range(1, requests_required):
        first_record = int(f'{i}01')
        subsequent_json = retrieve_wos_metadata_via_api(
            apikey,
            search_query,
            records_per_page,
            first_record
        )
        for record in subsequent_json['Data']['Records']['records']['REC']:
            fetch_data(record, usd_rates)
        print(f'Request {i + 1} of {requests_required} complete.')

    df = pd.DataFrame(grants_list)
    safe_filename = search_query.replace('*', '').replace('"', '')
    df.to_excel(
        excel_writer=f'downloads/{safe_filename} - {date.today()}.xlsx',
        sheet_name='Grants Data',
        index=False
    )
    plots = visualize_data(df)
    return f'{safe_filename} - {date.today()}.xlsx', plots


if __name__ == '__main__':
    app.run(debug=True)
