"""
Visualize processed dataframes or Excel files of data as Plotly express
objects.
"""

import textwrap
from collections import Counter, defaultdict
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


def word_wrap(x: str, width: int) -> str:
    """Wrap words for nicer formatting of longer titles on graphs."""

    return '<br>'.join(textwrap.wrap(str(x), width=width))


def visualize_wos_data(df, df2, query: str) -> tuple:
    """Create a number of html div objects with data visualizations
    with Plotly."""

    return (
        visualize_metrics(df2, query, 'WOS'),
        visualize_authors(df, query),
        visualize_years(df, query, 'WOS', df2),
        visualize_assignees(df2, query, 'WOS'),
        visualize_inventors(df2, query, 'WOS'),
        visualize_countries_applied(df2, query, 'WOS'),
        visualize_countries_granted(df2, query, 'WOS')
    )


def visualize_dii_data(df, query: str) -> tuple:
    """Create a number of html div objects with data visualizations
    with Plotly."""

    return (
        visualize_metrics(df, query, 'DIIDW'),
        visualize_years(df, query, 'DIIDW'),
        visualize_assignees(df, query, 'DIIDW'),
        visualize_inventors(df, query, 'DIIDW'),
        visualize_countries_applied(df, query, 'DIIDW'),
        visualize_countries_granted(df, query, 'DIIDW')
    )


def visualize_trends_data(df, query: str) -> tuple[str]:
    """Create an html div object with a bar chart data visualizations
    with Plotly."""

    return (
        visualize_years(df, query, 'BOTH'),
    )


def visualize_metrics(df: pd.DataFrame, query: str, db: str) -> str:
    """Create a treemap visualisation for the inventions' metrics."""

    number_of_inventions = df.shape[0]
    inventions_with_granted_patents = (
        df['granted_patents'][df['granted_patents'] != ''].dropna().shape[0]
    )

    success_rate = count_success_rate(df['patent_numbers'])
    quad_inventions = df[df['is_quadrilateral'] == True].dropna().shape[0]

    if db == 'WOS':
        title = f'Key metrics for inventions citing {query}'
    else:
        title = f'Key metrics for: {query}'

    output = (
        f'<p class="metrics__title">{title}:</p>'
        '<ul class="metrics__container">'
        '<li class="metric__box">'
        '<p class="metric__annotation">Number of Inventions:</p>'
        f'<p class="metric__value">{number_of_inventions}</p'
        '</li>'
        '<li class="metric__box">'
        '<p class="metric__annotation">Inventions with granted patents:</p>'
        f'<p class="metric__value">{inventions_with_granted_patents}</p>'
        '</li>'
        '<li class="metric__box">'
        '<p class="metric__annotation">Patent Application Success Rate:</p>'
        f'<p class="metric__value">{success_rate * 100:.1f}%</p>'
        '</li>'
        '<li class="metric__box">'
        f'<p class="metric__annotation">Quadrilateral Inventions:</p>'
        f'<p class="metric__value">{quad_inventions}</p>'
        '</li>'
        '</ul>'
    )

    return output


def count_success_rate(patent_numbers) -> float:
    """Calculate the patent applications success rate."""

    application_count = 0
    granted_count = 0
    patent_list = []

    for patent_str in patent_numbers:
        patent_list.extend(patent_str.split(', '))

    for patent in patent_list:
        parts = patent.split('-')
        if len(parts) < 2:
            continue
        kind_code = parts[1]

        if kind_code.startswith('A') or kind_code in ('W', 'U', 'S'):
            application_count += 1
        else:
            granted_count += 1

    return granted_count / application_count


def visualize_authors(df: pd.DataFrame, query: str) -> str:
    """Create a treemap visualisation for the top researchers from the
    dataset who received most citations from patents."""

    # Fill NaN values in 'authors' and 'citing_inventions'
    df['authors'] = df['authors'].fillna('')
    df['citing_inventions'] = df['citing_inventions'].fillna('')

    # Dictionary to store author-level metrics
    author_data = defaultdict(
        lambda: {
            'documents': 0,
            'docs_with_patent_citations': 0,
            'citations_from_patents': set()
        }
    )

    for _, row in df.iterrows():
        if not row['authors']:  # Skip rows with empty authors
            continue
        authors = row['authors'].split('; ')
        citing_inventions = (
            set(row['citing_inventions'].split()) if row['citing_inventions']
            else set()
        )

        for author in authors:
            author_data[author]['documents'] += 1
            if row['times_cited'] > 0:
                author_data[author]['docs_with_patent_citations'] += 1
            author_data[author]['citations_from_patents'].update(citing_inventions)

    # Convert to a DataFrame
    authors_df = pd.DataFrame([
        {
            'author': author,
            'Documents': data['documents'],
            'Citations from patents': len(data['citations_from_patents']),
            '% documents cited': (data['docs_with_patent_citations'] /
                                  data['documents']) * 100
        }
        for author, data in author_data.items()
    ])

    authors_df.sort_values('Citations from patents', ascending=False, inplace=True)
    display_items_top_authors = min(
        authors_df[authors_df['Citations from patents'] > 0].shape[0], 1000
    )

    fig = px.scatter(
        data_frame=authors_df[:display_items_top_authors],
        x='Documents',
        y='Citations from patents',
        size='% documents cited',
        title=word_wrap(
            x=f'Top Authors by technological impact for: {query}',
            width=120
        ),
        hover_name='author',
        hover_data={
            'Documents': True,
            'Citations from patents': True,
            '% documents cited': ':.2f'
        },
        template='plotly_white'
    )

    fig.update_traces(marker={'color': color_palette[0]})

    return offline.plot(fig, output_type='div')


def visualize_assignees(df: pd.DataFrame, query: str, db: str) -> str:
    """Create a treemap visualisation for the top assignees by their
    occurrences.
    """

    all_assignees = [
        name.strip()
        for names in df['assignee_names'].dropna()
        for name in names.split(',')
    ]

    assignee_counts = Counter(all_assignees)
    top_assignees = pd.DataFrame(
        assignee_counts.items(),
        columns=['Assignee Names', 'Occurrences']
    )
    top_assignees.sort_values('Occurrences', ascending=False, inplace=True)
    display_items_top_assignees = min(top_assignees.shape[0], 30)

    if db == 'WOS':
        title = (f'Top Assignees by inventions citing Web of Science '
                 f'research papers for: {query}')
    else:
        title = f'Top Assignees by number of inventions for: {query}'

    fig = px.treemap(
        data_frame=top_assignees[:display_items_top_assignees],
        names='Assignee Names',
        parents=[None for _ in range(display_items_top_assignees)],
        values='Occurrences',
        color_discrete_sequence=color_palette,
        title=word_wrap(x=title, width=120)
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )

    return offline.plot(fig, output_type='div')


def visualize_inventors(df: pd.DataFrame, query: str, db: str) -> str:
    """Create a treemap visualisation for the inventors by their
    occurrences.
    """

    all_inventors = [
        name.strip()
        for names in df['inventor_names'].dropna()
        for name in names.split(',')
    ]

    inventor_counts = Counter(all_inventors)
    top_inventors = pd.DataFrame(
        inventor_counts.items(),
        columns=['Inventor Names', 'Occurrences']
    )
    top_inventors.sort_values('Occurrences', ascending=False, inplace=True)
    display_items_top_inventors = min(top_inventors.shape[0], 30)

    if db == 'WOS':
        title = (f'Top Inventors by patent families citing Web of Science '
                 f'research papers for: {query}')
    else:
        title = f'Top Inventors by number of patent families for: {query}'

    fig = px.treemap(
        data_frame=top_inventors[:display_items_top_inventors],
        names='Inventor Names',
        parents=[None for _ in range(display_items_top_inventors)],
        values='Occurrences',
        color_discrete_sequence=color_palette,
        title=word_wrap(x=title, width=120)
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )

    return offline.plot(fig, output_type='div')


def visualize_countries_applied(df: pd.DataFrame, query: str, db: str) -> str:
    """Visualise country data with Plotly choropleth."""

    country_codes_df = pd.read_excel('country_codes.xlsx')
    df['countries_applied'] = df['countries_applied'].apply(lambda x: x.split(', '))
    occurrences = df['countries_applied'].explode().value_counts().reset_index()
    mapping = dict(zip(country_codes_df['A2'], country_codes_df['A3']))
    occurrences['countries_applied'] = (occurrences['countries_applied']
                                        .map(mapping).dropna())

    if db == 'WOS':
        title = (f'Countries by patent documents citing Web of Science '
                 f'research papers for: {query}')
    else:
        title = f'Countries by number of patent documents for: {query}'

    fig = px.choropleth(
        occurrences,
        locations='countries_applied',
        color='count',
        color_continuous_scale=['#3595f0', '#B175E1'],
        projection='natural earth',
        labels={'countries_applied_list': 'Country', 'count': 'Occurrences'},
        title=word_wrap(x=title, width=120)
    )

    return offline.plot(fig, output_type='div')


def visualize_countries_granted(df: pd.DataFrame, query: str, db: str) -> str:
    """Visualise country data with Plotly choropleth - only the
    countries where there were granted patents.
    """

    country_codes_df = pd.read_excel('country_codes.xlsx')
    df['countries_granted'] = (df['countries_granted'].dropna()
                               .apply(lambda x: x.split(', ')))
    occurrences = (df['countries_granted'].explode().value_counts()
                   .reset_index())
    mapping = dict(zip(country_codes_df['A2'], country_codes_df['A3']))
    occurrences['countries_granted'] = (occurrences['countries_granted']
                                        .map(mapping).dropna())

    if db == 'WOS':
        title = (f'Countries by granted patents citing Web of Science '
                 f'research papers for: {query}')
    else:
        title = f'Countries by granted patents for: {query}'

    fig = px.choropleth(
        occurrences,
        locations='countries_granted',
        color='count',
        color_continuous_scale=['#3595f0', '#B175E1'],
        projection='natural earth',
        labels={'countries_granted': 'Country', 'count': 'Occurrences'},
        title=word_wrap(x=title, width=120)
    )

    return offline.plot(fig, output_type='div')


def visualize_years(df: pd.DataFrame, query: str, db: str, df2=None) -> str:
    """Visualize trends in research and innovation."""

    if db == 'BOTH':
        mapping = {
            'year': 'Year',
            'wos': 'Web of Science Documents',
            'dii_prtyyear': 'Patent Documents (Earliest Priority Year)',
            'dii_pubyear': 'Patent Documents (Publication Year)'
        }
        df.rename(columns=mapping, inplace=True)

        columns = [
            'Web of Science Documents',
            'Patent Documents (Earliest Priority Year)',
            'Patent Documents (Publication Year)'
        ]

        title = f'Research and Innovations Trend for topic: {query}'

    elif db == 'WOS':
        wos_pub_years = pd.Series(df['pub_year'].value_counts())
        dii_pub_years = pd.Series(df2['publication_year'].value_counts())
        dii_priority_years = pd.Series(df2['earliest_priority'].value_counts())
        df = pd.DataFrame({
            'Web of Science Documents': wos_pub_years,
            'Citing Patent Documents (Earliest Priority Year)': dii_pub_years,
            'Citing Patent Documents (Publication Year)': dii_priority_years
        }).fillna(0).astype('int64').reset_index().rename(columns={'index': 'Year'})
        columns = [
            'Web of Science Documents',
            'Citing Patent Documents (Earliest Priority Year)',
            'Citing Patent Documents (Publication Year)'
        ]

        title = f'Research output and Citing Patents Trend for: {query}'

    else:
        dii_pubyear_counts = pd.Series(df['publication_year'].value_counts())
        dii_priority_counts = pd.Series(df['earliest_priority'].value_counts())

        df = pd.DataFrame({
            'Patent Documents (Earliest Priority Year)': dii_priority_counts,
            'Patent Documents (Publication Year)': dii_pubyear_counts
        }).fillna(0).reset_index().rename(columns={'index': 'Year'}).astype('int64')
        columns = [
            'Patent Documents (Earliest Priority Year)',
            'Patent Documents (Publication Year)'
        ]
        title = f'Patents by years for: {query}'

    fig = px.bar(
        data_frame=df,
        x=df.columns[0],
        y=columns,
        barmode='group',
        color_discrete_sequence=color_palette[:df.shape[1]-1],
        title=word_wrap(x=title, width=120),
    )

    # Making cosmetic edits to the plot
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        font_color='#646363',
        font_size=18,
        title_font_color='#646363',
        title_font_size=18,
        legend_title_text=None,
        legend={
            'yanchor': 'bottom',
            'y': -0.4,
            'xanchor': 'center',
            'x': 0.5
        }
    )
    fig.update_yaxes(title_text=None, showgrid=True, gridcolor='#9D9D9C')
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

    return offline.plot(fig, output_type='div')


def visualize_excel(file: str) -> tuple:
    """Return graphs objects from previously saved Excel file."""

    if file.split('/')[1] == 'woscc':
        return visualize_wos_data(
            pd.read_excel(file, sheet_name='Base Records'),
            pd.read_excel(file, sheet_name='Citing Inventions'),
            pd.read_excel(file, sheet_name='Search Query')['Search Query'][0]
        )

    if file.split('/')[1] == 'dii':
        return visualize_dii_data(
            pd.read_excel(file, sheet_name='Patent Families'),
            pd.read_excel(file, sheet_name='Search Query')['Search Query'][0]
        )

    return visualize_trends_data(
        pd.read_excel(file, sheet_name='Trends'),
        pd.read_excel(file, sheet_name='Search Query')['Search Query'][0]
    )
