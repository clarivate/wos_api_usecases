"""
Visualize the data retrieved through the API and return it to the app.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly import offline


def visualize_data(df2, query):
    """Visualize the data from a dataframe using Plotly,
    return data as an html div.

    :param df2: pd.DataFrame.
    :param query: str.
    :return: str.
    """
    fig = make_subplots(rows=3, cols=2, specs=[
        [{'type': 'domain'}, {'type': 'domain'}],
        [{'type': 'domain'}, {'type': 'domain'}],
        [{'type': 'domain'}, {'type': 'domain'}]
    ])

    colors = ['#B175E1', '#18A381']

    fig.add_trace(go.Pie(
        labels=df2.index[[0, 1]],
        values=df2['Coauthor Name'][0:],
        name='Coauthor Name'
    ), 1, 1)
    fig.add_trace(go.Pie(
        labels=df2.index[[0, 1]],
        values=df2['ResearcherID'][0:],
        name='ResearcherID'
    ), 2, 1)
    fig.add_trace(go.Pie(
        labels=df2.index[[0, 1]],
        values=df2['ORCID'][0:],
        name='ORCID'
    ), 3, 1)
    fig.add_trace(go.Pie(
        labels=df2.index[[0, 1]],
        values=df2['Organization'][0:],
        name='Organization'
    ), 1, 2)
    fig.add_trace(go.Pie(
        labels=df2.index[[0, 1]],
        values=df2['Country'][0:],
        name='Country'
    ), 2, 2)
    fig.add_trace(go.Pie(
        labels=df2.index[[0, 1]],
        values=df2['Publication Source'][0:],
        name='Publication Source'
    ), 3, 2)

    fig.update_traces(hole=.83,
                      direction='clockwise',
                      sort=False,
                      marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)))

    fig.update_layout(
        title_text=f"Self-citations analysis for: {query}",

        # Add annotations in the center of the donut pies.
        annotations=[
            dict(
                text='Coauthor Name',
                x=0,
                y=0.89,
                font_size=16,
                showarrow=False
            ),
            dict(
                text='Coauthor RID',
                x=0.02,
                y=0.5,
                font_size=16,
                showarrow=False
            ),
            dict(
                text='Coauthor ORCID',
                x=0,
                y=0.13,
                font_size=16,
                showarrow=False
            ),
            dict(
                text='Organization',
                x=0.62,
                y=0.89,
                font_size=16,
                showarrow=False
            ),
            dict(
                text='Country',
                x=0.64,
                y=0.5,
                font_size=16,
                showarrow=False
            ),
            dict(
                text='Publication Source',
                x=0.6,
                y=0.13,
                font_size=16,
                showarrow=False
            )
        ])

    return offline.plot(fig, output_type='div')


def visualize_excel(file):
    """Return graphs objects from previously saved Excel file.

    :param file: str.
    :return: str.
    """
    df = pd.read_excel(file, sheet_name='Self-citation rates')
    query = pd.read_excel(file, sheet_name='Search query')

    return visualize_data(df, query)

