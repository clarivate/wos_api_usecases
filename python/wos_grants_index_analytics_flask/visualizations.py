"""
Visualize processed dicts or Excel files of data as Plotly express
objects.
"""

import textwrap
import pandas as pd
import plotly.express as px
from plotly import offline

color_palette = ['#B175E1', '#18A381', '#3595F0', '#ED5564', '#5E33BF',
                 '#003F51', '#A39300', '#EC40DB', '#C8582A', '#1E48DD',
                 '#558B2F', '#282C75', '#EC407A', '#0277BD', '#165550',
                 '#9F7D1C', '#AD1457', '#00897B', '#1565C0', '#D81B60',
                 '#6B9E00', '#0378FF', '#0C1D66', '#EF6C00', '#933F1D',
                 '#8E9926', '#00A0B5', '#E53935', '#5C6BC0', '#C28B00',
                 '#00695C', '#F4511E', '#8E24AA', '#43A047', '#C2156E',
                 '#B67325', '#AB47BC', '#2E7D32', '#1B809F', '#C13800']


def word_wrap(x):
    """Wrap words for nicer formatting of longer titles on graphs.

    :param x: str or int.
    :return: str.
    """
    return '<br>'.join(textwrap.wrap(str(x), 40))


def visualize_data(df):
    """Create a number of html div object with various grant data
    visualizations with Plotly.

    :param df: pandas dataframe.
    :return: tuple[str].
    """
    # Visualizing Grants by Years.
    df['Grant Amount, USD'] = df['Grant Amount, USD'].replace(
        to_replace='',
        value=0
    )

    grants_by_years = (
        df.groupby('Publication Year')['Grant Amount, USD'].sum()
    )

    fig = px.bar(
        data_frame=grants_by_years,
        y='Grant Amount, USD',
        title='Grant Funding by Year, USD',
        hover_data={'Grant Amount, USD': ':,.2f'}
    )
    fig.update_traces(marker_color=color_palette[0])
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        font_color='#646363',
        font_size=18,
        title_font_color='#646363',
        legend_title_text=None,
        legend={'yanchor': "bottom", 'y': -0.4, 'xanchor': "center", 'x': 0.5}
    )
    fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C')
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')
    grants_by_years_plot = offline.plot(fig, output_type='div')

    # Visualizing top principal investigators by grant volumes
    grants_by_pi = (
        df.groupby('Principal Investigator')['Grant Amount, USD'].sum('')
        .to_frame().reset_index()
    )

    grants_by_pi.sort_values(
        'Grant Amount, USD',
        ascending=False,
        inplace=True
    )

    display_items_gbpi = min(grants_by_pi.shape[0], 20)
    fig = px.treemap(
        data_frame=grants_by_pi[:display_items_gbpi],
        names='Principal Investigator',
        parents=[None for x in range(display_items_gbpi)],
        color_discrete_sequence=color_palette,
        values='Grant Amount, USD',
        hover_data={'Grant Amount, USD': ':,.2f'},
        title='Top Principal Investigators by funding volumes, USD'
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )
    grants_by_pi_plot = offline.plot(fig, output_type='div')

    # Visualizing top organizations receiving grant funding.
    df['Principal Investigator Institution'] = (
        df['Principal Investigator Institution'].replace(
            to_replace='',
            value='(name unavailable)'
        )
    )
    grants_by_organizations = (
        df.groupby('Principal Investigator Institution')['Grant Amount, USD'].
        sum('').to_frame().reset_index()
    )
    grants_by_organizations.sort_values(
        'Grant Amount, USD',
        ascending=False,
        inplace=True
    )

    grants_by_organizations['Principal Investigator Institution'] = (
        grants_by_organizations['Principal Investigator Institution']
        .apply(word_wrap)
    )

    display_items_gbo = min(grants_by_organizations.shape[0], 15)
    fig = px.treemap(
        data_frame=grants_by_organizations[:display_items_gbo],
        names='Principal Investigator Institution',
        parents=[None for x in range(display_items_gbo)],
        color_discrete_sequence=color_palette,
        values='Grant Amount, USD',
        hover_data={'Grant Amount, USD': ':,.2f'},
        title='Top Principal Investigator Institutions by funding volumes, USD'
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )
    grants_by_organizations_plot = offline.plot(fig, output_type='div')

    # Visualizing top funding agencies by funding volume.
    df['Funding Agency'] = (df['Funding Agency'].replace(
        to_replace='',
        value='(name unavailable)'
    ))
    grants_by_funder = (
        df.groupby(['Funding Agency', 'Funding Country'])['Grant Amount, USD']
        .sum().to_frame().reset_index()
    )
    grants_by_funder.sort_values('Grant Amount, USD', ascending=False, inplace=True)
    grants_by_funder['Funding Agency'] = (grants_by_funder['Funding Agency']
                                          .apply(word_wrap))

    fig = px.treemap(
        data_frame=grants_by_funder,
        path=['Funding Country', 'Funding Agency'],
        values='Grant Amount, USD',
        color_discrete_sequence=color_palette,
        hover_data={'Grant Amount, USD': ':,.2f'},
        title='Top Grant Agencies by funding volumes, USD'
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )
    grants_by_funder_plot = offline.plot(fig, output_type='div')

    # Visualizing Average Grant Size by Years
    average_grant_volume_by_year = pd.merge(
        grants_by_years,
        df.groupby('Publication Year')['UT'].count(), on='Publication Year'
    )
    average_grant_volume_by_year['Average Grant Volume'] = (
            average_grant_volume_by_year['Grant Amount, USD'] /
            average_grant_volume_by_year['UT']
    )
    average_grant_volume_by_year = average_grant_volume_by_year.rename(
        columns={
            'UT': 'Number of Grants',
            'Grant Amount, USD': 'Total Funding Volume'
        }
    )

    fig = px.bar(
        data_frame=average_grant_volume_by_year,
        y='Average Grant Volume',
        hover_data={'Average Grant Volume': ':,.2f',
                    'Number of Grants': True,
                    'Total Funding Volume': ':,.2f'},
        title='Average Grant Volume by Year, USD'
    )

    fig.update_traces(marker_color=color_palette[0])
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        font_color='#646363',
        font_size=18,
        title_font_color='#646363',
        legend_title_text=None,
        legend={'yanchor': "bottom", 'y': -0.4, 'xanchor': "center", 'x': 0.5}
    )
    fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C')
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')
    average_grants_volume_by_years_plot = offline.plot(fig, output_type='div')

    # Visualizing Top Grants by Associated Web of Science Records
    df.sort_values('Related WoS Records Count', ascending=False, inplace=True)
    df['Document Title'] = (df['Document Title'].dropna().apply(word_wrap))

    fig = px.bar(
        data_frame=df[:50],
        x='UT',
        y='Related WoS Records Count',
        hover_name='Document Title',
        title='Top Grants by Associated Web of Science Records'

    )

    fig.update_traces(marker_color='#BC99FF')
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        font_color='#646363',
        font_size=18,
        title_font_color='#646363',
        legend_title_text=None,
        legend={'yanchor': "bottom", 'y': -0.4, 'xanchor': "center", 'x': 0.5}
    )
    fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C')
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')
    top_grants_by_associated_wos_records_plot = offline.plot(
        fig,
        output_type='div'
    )

    return (grants_by_years_plot,
            grants_by_pi_plot,
            grants_by_organizations_plot,
            grants_by_funder_plot,
            average_grants_volume_by_years_plot,
            top_grants_by_associated_wos_records_plot)


def visualize_excel(file):
    """Return graphs objects from previously saved Excel file.

    :param file:
    :return: tuple of str.
    """
    df = pd.read_excel(file)
    plots = visualize_data(df)
    return plots
