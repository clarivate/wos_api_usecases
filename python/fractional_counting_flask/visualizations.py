"""
Visualize processed dataframes or Excel files of data as Plotly express
objects.
"""

import textwrap
import pandas as pd
import plotly.graph_objects as go
from plotly import offline
from plotly.subplots import make_subplots

color_palette = ['#B175E1', '#18A381', '#3595F0', '#ED5564', '#5E33BF',
                 '#003F51', '#A39300', '#EC40DB', '#C8582A', '#1E48DD',
                 '#558B2F', '#282C75', '#EC407A', '#0277BD', '#165550',
                 '#9F7D1C', '#AD1457', '#00897B', '#1565C0', '#D81B60',
                 '#6B9E00', '#0378FF', '#0C1D66', '#EF6C00', '#933F1D',
                 '#8E9926', '#00A0B5', '#E53935', '#5C6BC0', '#C28B00',
                 '#00695C', '#F4511E', '#8E24AA', '#43A047', '#C2156E',
                 '#B67325', '#AB47BC', '#2E7D32', '#1B809F', '#C13800']


def word_wrap(x, width):
    """Wrap words for nicer formatting of longer titles on graphs.

    :param x: str or int.
    :param width: int.
    :return: str.
    """
    return '<br>'.join(textwrap.wrap(str(x), width=width))


def visualize_data(df, query, org_name):
    """Create a number of html div objects with - currently only one -
    data visualizations with Plotly.

    :param df: pd.DataFrame.
    :param query: str.
    :param org_name: str.
    :return: tuple[str]
    """

    return (
        visualize_fractional_counts(df, query, org_name),
    )


def visualize_fractional_counts(df2, query, org):
    """Create a treemap visualisation for top cited sources.

    :param df2: pd.DataFrame.
    :param query: str.
    :param org: str.
    :return: str.
    """

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=df2['Publication_year'],
            y=df2['Whole Counting'],
            offset=0.0005,
            name='Whole Counting',
            marker={'color': color_palette[0]}
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(
            x=df2['Publication_year'],
            y=df2['Fractional Counting'],
            name='Fractional Counting',
            marker={'color': color_palette[1]}
        ),
        secondary_y=False
    )

    fig.update_traces(marker={'line': {'width': 3, 'color': 'white'}})

    # Adding the fractional/whole ratio as a line above the bar plot
    fig.add_trace(
        go.Scatter(
            x=df2['Publication_year'],
            y=(df2['Fractional Counting'] / df2['Whole Counting']),
            line={'color': 'black', 'width': 5},
            name='Average Fractional Value (Research Involvement)'
        ),
        secondary_y=True
    )

    plot_title = f'Whole and Fractional Research Output Comparison for {org}'
    plot_subtitle = f'Search query: {query}'

    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        barmode='group',
        bargroupgap=.5,
        font_color='#646363',
        font_size=18,
        title_font_color='#646363',
        title=f'{plot_title}<br><sup>{plot_subtitle}</sup>',
        legend_title_text=None,
        legend={
            'yanchor': 'bottom',
            'y': -0.4,
            'xanchor': 'center',
            'x': 0.5
        }
    )
    fig.update_yaxes(
        title_text=None,
        showgrid=True,
        gridcolor='#9D9D9C',
        secondary_y=False
    )
    fig.update_yaxes(
        range=[0, 1],
        showgrid=False,
        tickformat=',.0%',
        secondary_y=True
    )
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

    return offline.plot(fig, output_type='div')


def visualize_excel(file):
    """Return graphs objects from previously saved Excel file.

    :param file: str.
    :return: tuple[str].
    """

    df = pd.read_excel(file, sheet_name='Annual Dynamics')
    query = pd.read_excel(file, sheet_name='Query Parameters')['Search Query'][0]
    org = pd.read_excel(file, sheet_name='Query Parameters')['Affiliation'][0]

    return visualize_data(df, query, org)
