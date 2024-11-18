"""
A Flask app that allows retrieving, processing, analyzing and
visualizing the Web of Science cited references data.

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

    :return: flask.render_template.
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
            'top_journals_treemap': plots_list[0],
            'top_publishers_treemap': plots_list[1],
            'top_authors': plots_list[2],
            'refs_by_year': plots_list[3],
            'top_cited_docs_by_citations_plot': plots_list[4]
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
    :return: render_template.
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
        for plot in plots:
            plots_list.append(plot)
        return render_template(
            'index.html',
            filename=safe_filename,
            search_query=search_query,
            plot=plots_list[0],
            index=0
        )
    return render_template('index.html', search_query='')


def load_file_section(file):
    """Manage the actions and processes for the load file search
    section.

    :param file:
    :return: flask.render_template
    """
    plots_list.clear()
    if file == '':
        return render_template('index.html', search_query='')
    plots = visualize_excel(f'downloads/{file}')
    for plot in plots:
        plots_list.append(plot)
    return render_template('index.html', plot=plots_list[0], index=0)


if __name__ == '__main__':
    app.run(debug=True)
