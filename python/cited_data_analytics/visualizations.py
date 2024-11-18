"""
Visualize processed dataframes or Excel files of data as Plotly express
objects.
"""

import textwrap
import pandas as pd
import plotly.express as px
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


def visualize_data(df, query):
    """Create a number of html div object with various grant data
    visualizations with Plotly.

    :param df: pd.DataFrame.
    :param query: str.
    :return: tuple[str]
    """

    return (
        visualize_top_sources(df, query),
        visualize_top_publishers(df, query),
        visualize_top_authors(df, query),
        visualize_refs_by_years(df, query),
        visualize_top_refs_by_citations(df, query)
    )


def visualize_top_sources(df, query):
    """Create a treemap visualisation for top cited sources.

    :param df: pd.DataFrame.
    :param query: str.
    :return: str.
    """
    top_sources = df.groupby('CitedWork').size().to_frame().reset_index()
    top_sources.rename(columns={0: 'Occurrences'}, inplace=True)
    top_sources.sort_values('Occurrences', ascending=False, inplace=True)
    top_sources['CitedWork'] = top_sources['CitedWork'].apply(
        word_wrap,
        width=30
    )
    display_items_top_sources = min(df.shape[0], 50)

    fig = px.treemap(
        data_frame=top_sources[:display_items_top_sources],
        names='CitedWork',
        parents=[None for x in range(display_items_top_sources)],
        values='Occurrences',
        color_discrete_sequence=color_palette,
        title=word_wrap(
            x=f'Top Sources by Cited References for search query: {query}',
            width=75
        )
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )

    return offline.plot(fig, output_type='div')


def visualize_top_publishers(df, query):
    """Create a treemap visualisation for top cited publishers.

    :param df: pd.DataFrame.
    :param query: str.
    :return: str.
    """
    top_sources = (df.groupby(['Publisher', 'CitedWork']).size().to_frame().
                   reset_index())
    top_sources.rename(columns={0: 'Occurrences'}, inplace=True)
    top_sources.sort_values('Occurrences', ascending=False, inplace=True)
    top_sources['CitedWork'] = top_sources['CitedWork'].apply(
        word_wrap,
        width=30
    )
    top_publishers = df.groupby('Publisher').size().to_frame().reset_index()
    top_publishers.rename(columns={0: 'P_Occurrences'}, inplace=True)
    top_publishers = pd.merge(top_publishers, top_sources, on='Publisher')
    top_publishers.sort_values('Occurrences', ascending=False, inplace=True)
    top_publishers.sort_values('P_Occurrences', ascending=False, inplace=True)
    top_publishers['CitedWork'] = top_publishers['CitedWork'].apply(
        word_wrap,
        width=30
    )
    display_items_tp = min(top_publishers.shape[0], 2000)

    fig = px.treemap(
        data_frame=top_publishers[:display_items_tp],
        path=['Publisher', 'CitedWork'],
        values='Occurrences',
        color_discrete_sequence=color_palette,
        title=word_wrap(
            x=f'Top Publishers by Cited References for search query: {query}',
            width=75
        )
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )

    return offline.plot(fig, output_type='div')


def visualize_top_authors(df, query):
    """Create a bar graph visualisation for top cited first authors.

    :param df: pd.DataFrame.
    :param query: str.
    :return: str.
    """
    top_authors = df.groupby('CitedAuthor').size().to_frame().reset_index()
    top_authors.rename(columns={0: 'Occurrences'}, inplace=True)
    top_authors.sort_values('Occurrences', ascending=False, inplace=True)
    display_items_ta = min(top_authors.shape[0], 30)

    fig = px.bar(
        data_frame=top_authors[:display_items_ta],
        x='CitedAuthor',
        y='Occurrences',
        title=word_wrap(
            x=f'Top Authors by Cited References for search query: {query}',
            width=75
        )
    )
    fig.update_traces(marker_color=color_palette[0])
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        font_color='#646363',
        font_size=18,
        title_font_color='#646363',
        title_font_size=16,
        legend_title_text=None,
        legend={'yanchor': "bottom", 'y': -0.4, 'xanchor': "center", 'x': 0.5}
    )
    fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C')
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

    return offline.plot(fig, output_type='div')


def visualize_refs_by_years(df, query):
    """Create a bar graph visualisation for cited references by year of
    their publication.

    :param df: pd.DataFrame.
    :param query: str.
    :return: str.
    """
    refs_by_years = df.groupby('Year').size().to_frame().reset_index()
    refs_by_years.rename(columns={0: 'Occurrences'}, inplace=True)
    refs_by_years.sort_values('Year', inplace=True)
    refs_by_years = refs_by_years[(refs_by_years['Year'] != '1000') &
                                  (refs_by_years['Year'] != 1000)]

    fig = px.bar(
        data_frame=refs_by_years,
        x='Year',
        y='Occurrences',
        title=word_wrap(
            x=f'Cited References by Year for search query: {query}',
            width=75
        )
    )
    fig.update_traces(marker_color=color_palette[0])
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        font_color='#646363',
        font_size=18,
        title_font_color='#646363',
        legend_title_text=None,
        title_font_size=16,
        legend={'yanchor': "bottom", 'y': -0.4, 'xanchor': "center", 'x': 0.5}
    )
    fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C')
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

    return offline.plot(fig, output_type='div')


def visualize_top_refs_by_citations(df, query):
    """Create a bar graph visualisation for top cited references by
    times cited - globally in Web of Science Core Collection and
    locally in the dataset defined by the initial search query.

    :param df: pd.DataFrame.
    :param query: str.
    :return: str.
    """
    global_tc = (df.sort_values('TimesCited', ascending=False)
                 .drop_duplicates().reset_index())
    if isinstance(global_tc, tuple):
        global_tc = global_tc[0]

    local_tc = df.reset_index().groupby('UID').size().to_frame().reset_index()
    local_tc.rename(columns={0: 'Occurrences'}, inplace=True)
    local_tc = pd.merge(local_tc, global_tc, on='UID', how='left')
    local_tc.sort_values('Occurrences', ascending=False, inplace=True)
    if isinstance(local_tc, tuple):
        local_tc = local_tc[0]
    display_items_local_tc = min(df.shape[0], 30)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=local_tc['UID'][:display_items_local_tc],
            y=local_tc['Occurrences'],
            name='Local Citations',
            marker={'color': color_palette[0]}
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(
            x=local_tc['UID'][:display_items_local_tc],
            y=local_tc['TimesCited'],
            name='Global Citations',
            marker={'color': color_palette[1]},
            offset=.0005,
            opacity=.7
        ),
        secondary_y=True
    )

    fig.update_xaxes(title_text='', linecolor='#9D9D9C')
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        barmode='group',
        bargap=.5,
        font_color='#646363',
        font_size=16,
        title_font_color='#646363',
        title=word_wrap(
            f'Most cited documents globally in Web of Science '
            f'Core Collection and locally for the dataset defined '
            f'by search query: {query}',
            width=75
        ),
        title_font_size=16,
        legend_title_text=None,
    )
    fig.update_yaxes(
        title_text='Local Citations',
        showgrid=True,
        gridcolor='#9D9D9C',
        secondary_y=False
    )
    fig.update_yaxes(
        title_text='Global Citations',
        showgrid=False,
        secondary_y=True
    )

    return offline.plot(fig, output_type='div')


def visualize_excel(file):
    """Return graphs objects from previously saved Excel file.

    :param file:
    :return: tuple[str].
    """
    df = pd.read_excel(file, sheet_name='Cited References', index_col=0)
    query = pd.read_excel(file, sheet_name='Search Query')['Search Query'][0]

    return visualize_data(df, query)
