"""
Visualize processed dataframes or Excel files of data as Plotly express
objects.
"""

import textwrap
from collections import Counter, defaultdict
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        visualize_citation_report(df, df2, query),
        visualize_cited_authors(df, query),
        visualize_citing_authors(df2, query),
        visualize_citing_sources(df2, query),
        visualize_citing_source_countries(df2, query)
    )


def visualize_trends_data(df, query: str) -> tuple[str]:
    """Create an html div object with a bar chart data visualizations
    with Plotly."""

    return (visualize_trends_years(df, query),)


def visualize_citation_report(df: pd.DataFrame, df2: pd.DataFrame, query: str) -> str:
    """Create a treemap visualisation for the inventions' metrics."""

    wos_documents = df.shape[0]
    citations_from_policy_docs = df['times_cited'].sum()
    citing_policy_documents = df2.shape[0]

    title = f'Policy Citation Report for: {query}'

    wos_pub_years = pd.Series(df['pub_year'].value_counts())
    pci_pub_years = pd.Series(df2['publication_year'].value_counts())
    df = pd.DataFrame({
        'Web of Science Documents': wos_pub_years,
        'Citing Policy Documents': pci_pub_years
    }).fillna(0).astype('int64').reset_index().rename(columns={'index': 'Year'})

    plot_title = 'Policy Citations and Publications Over Time'

    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Web of Science Documents'],
            name='Web of Science Documents',
            marker={'color': color_palette[0]}
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Citing Policy Documents'],
            name='Citing Policy Documents',
            line={'color': '#5E33BF', 'width': 5}
        ),
        secondary_y=True
    )

    fig.update_traces(marker={'line': {'width': 3, 'color': 'white'}})

    # Making cosmetic edits to the plot
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        font_color='#646363',
        font_size=16,
        title=plot_title,
        title_font_color='#646363',
        title_font_size=18,
        legend_title_text=None,
        hoverlabel={'font_color': 'white'},
        legend={
            'yanchor': 'bottom',
            'y': -0.4,
            'xanchor': 'center',
            'x': 0.5
        }
    )
    fig.update_yaxes(
        title_text='Web of Science Documents',
        title_font={'size': 12},
        showgrid=True,
        gridcolor='#9D9D9C',
        secondary_y=False
    )
    fig.update_yaxes(
        title_text='Policy Citations',
        title_font={'size': 12},
        range=[0, df['Citing Policy Documents'].max()],
        showgrid=False,
        secondary_y=True
    )
    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

    output = (
        f'<p class="metrics__title">{title}:</p>'
        '<ul class="metrics__container">'
        '<li class="metric__box">'
        '<p class="metric__annotation">Number of Web of Science documents:</p>'
        f'<p class="metric__value">{wos_documents}</p'
        '</li>'
        '<li class="metric__box">'
        '<p class="metric__annotation">Citations From Policy Documents:</p>'
        f'<p class="metric__value">{citations_from_policy_docs}</p>'
        '</li>'
        '<li class="metric__box">'
        '<p class="metric__annotation">Citing Policy Documents:</p>'
        f'<p class="metric__value">{citing_policy_documents}</p>'
        '</li>'
        '<li class="metric__box">'
        '<p class="metric__annotation">Average Policy Citations Per Item:</p>'
        f'<p class="metric__value">{citations_from_policy_docs / wos_documents:.2f}</p>'
        '</li>'
        '</ul>'
        f'{offline.plot(fig, output_type='div')}'
    )

    return output


def visualize_cited_authors(df: pd.DataFrame, query: str) -> str:
    """Create a treemap visualisation for the top researchers from the
    dataset who received most citations from policy documents."""

    # Fill NaN values in 'authors' and 'citing_inventions'
    df['authors'] = df['authors'].fillna('')
    df['citing_policy_documents'] = df['citing_policy_documents'].fillna('')

    # Dictionary to store author-level metrics
    author_data = defaultdict(
        lambda: {
            'documents': 0,
            'docs_with_policy_citations': 0,
            'citations_from_policy_docs': set()
        }
    )

    for _, row in df.iterrows():
        if not row['authors']:  # Skip rows with empty authors
            continue
        authors = row['authors'].split('; ')
        citing_policy_docs = (
            set(row['citing_policy_documents'].split())
            if row['citing_policy_documents'] else set()
        )

        for author in authors:
            author_data[author]['documents'] += 1
            if row['times_cited'] > 0:
                author_data[author]['docs_with_policy_citations'] += 1
            author_data[author]['citations_from_policy_docs'].update(citing_policy_docs)

    # Convert to a DataFrame
    authors_df = pd.DataFrame([
        {
            'author': author,
            'Documents': data['documents'],
            'Citations from policy documents': len(data['citations_from_policy_docs']),
            '% documents cited': (data['docs_with_policy_citations'] /
                                  data['documents']) * 100
        }
        for author, data in author_data.items()
    ])

    authors_df.sort_values(
        'Citations from policy documents',
        ascending=False,
        inplace=True
    )

    display_items_top_authors = min(
        authors_df[authors_df['Citations from policy documents'] > 0].shape[0],
        1000
    )

    fig = px.scatter(
        data_frame=authors_df[:display_items_top_authors],
        x='Documents',
        y='Citations from policy documents',
        size='% documents cited',
        title=word_wrap(
            x=f'Top Authors by societal impact for: {query}',
            width=120
        ),
        hover_name='author',
        hover_data={
            'Documents': True,
            'Citations from policy documents': True,
            '% documents cited': ':.2f'
        },
        template='plotly_white'
    )

    fig.update_traces(marker={'color': color_palette[0], 'sizemin': 3})
    fig.update_layout(hoverlabel={'font_color': 'white'})

    return offline.plot(fig, output_type='div')


def visualize_citing_authors(df: pd.DataFrame, query: str) -> str:
    """Create a treemap visualisation for the top citing authors by
    their occurrences."""

    all_authors = [
        name.strip()
        for names in df['citing_author_names'].dropna()
        for name in names.split('; ')
    ]

    author_counts = Counter(all_authors)
    top_authors = pd.DataFrame(
        author_counts.items(),
        columns=['Citing Author Names', 'Occurrences']
    )
    top_authors.sort_values('Occurrences', ascending=False, inplace=True)
    display_items_top_authors = min(top_authors.shape[0], 30)

    title = (f'Top authors of policy documents citing Web of Science '
             f'research papers for: {query}')

    fig = px.treemap(
        data_frame=top_authors[:display_items_top_authors],
        names='Citing Author Names',
        parents=[None for _ in range(display_items_top_authors)],
        values='Occurrences',
        color_discrete_sequence=color_palette,
        title=word_wrap(x=title, width=120)
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )
    fig.update_layout(hoverlabel={'font_color': 'white'})

    return offline.plot(fig, output_type='div')


def visualize_citing_sources(df: pd.DataFrame, query: str) -> str:
    """Create a treemap visualisation for the inventors by their
    occurrences.
    """

    source_counts = Counter(df['source_name'])
    top_sources = pd.DataFrame(
        source_counts.items(),
        columns=['Citing Source Names', 'Occurrences']
    )
    top_sources.sort_values('Occurrences', ascending=False, inplace=True)
    display_items_top_sources = min(top_sources.shape[0], 30)

    title = (f'Top Policy Sources citing Web of Science '
             f'research papers for: {query}')

    fig = px.treemap(
        data_frame=top_sources[:display_items_top_sources],
        names='Citing Source Names',
        parents=[None for _ in range(display_items_top_sources)],
        values='Occurrences',
        color_discrete_sequence=color_palette,
        title=word_wrap(x=title, width=120)
    )
    fig.update_traces(
        textfont={'color': '#FFFFFF',
                  'size': 16},
        textinfo="label+value"
    )
    fig.update_layout(hoverlabel={'font_color': 'white'})

    return offline.plot(fig, output_type='div')


def visualize_citing_source_countries(df: pd.DataFrame, query: str) -> str:
    """Visualise country data with Plotly choropleth."""

    country_codes_df = pd.read_excel('country_codes.xlsx')
    df['source_country'] = df['source_country'].apply(
        lambda x: x.split(', ') if isinstance(x, str) else x)
    occurrences = df['source_country'].explode().value_counts().reset_index()
    mapping = dict(zip(country_codes_df['Country'], country_codes_df['A3']))
    occurrences['source_country'] = (
        occurrences['source_country'].map(mapping).dropna()
    )

    title = (f'Countries by policy documents citing Web of Science '
             f'research papers for: {query}')

    fig = px.choropleth(
        occurrences,
        locations='source_country',
        color='count',
        color_continuous_scale=['#3595f0', '#B175E1'],
        projection='natural earth',
        labels={'countries_applied_list': 'Country', 'count': 'Occurrences'},
        title=word_wrap(x=title, width=120)
    )
    fig.update_layout(hoverlabel={'font_color': 'white'})

    return offline.plot(fig, output_type='div')


def visualize_trends_years(df: pd.DataFrame, query: str) -> str:
    """Visualize trends in research and policy."""

    mapping = {
        'year': 'Year',
        'wos': 'Web of Science Documents',
        'pci': 'Policy Citation Index Documents'
    }
    df.rename(columns=mapping, inplace=True)
    title = f'Research and Policy Trend for topic: {query.split("=")[-1]}'

    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Web of Science Documents'],
            name='Web of Science Documents',
            marker={'color': color_palette[0]}
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Policy Citation Index Documents'],
            name='Policy Citation Index Documents',
            marker={'color': color_palette[1]},
            offset=.0005,
            opacity=.7
        ),
        secondary_y=True
    )

    # Making cosmetic edits to the plot
    fig.update_layout(
        {'plot_bgcolor': '#FFFFFF', 'paper_bgcolor': '#FFFFFF'},
        barmode='group',
        bargap=.5,
        font_color='#646363',
        font_size=18,
        title=title,
        title_font_color='#646363',
        title_font_size=18,
        legend_title_text=None,
        hoverlabel={'font_color': 'white'},
        legend={
            'yanchor': 'bottom',
            'y': -0.4,
            'xanchor': 'center',
            'x': 0.5
        }
    )

    fig.update_yaxes(
        title_text='Web of Science Documents',
        title_font={'size': 12},
        showgrid=True,
        gridcolor='#9D9D9C',
        secondary_y=False
    )

    fig.update_yaxes(
        title_text='Policy Citation Index Documents',
        title_font={'size': 12},
        showgrid=False,
        secondary_y=True
    )

    fig.update_xaxes(title_text=None, linecolor='#9D9D9C')

    return offline.plot(fig, output_type='div')


def visualize_excel(file: str) -> tuple:
    """Return graphs objects from previously saved Excel file."""

    if file.split('/')[1] == 'woscc':
        return visualize_wos_data(
            pd.read_excel(file, sheet_name='Base Records'),
            pd.read_excel(file, sheet_name='Citing Policy Documents'),
            pd.read_excel(file, sheet_name='Search Query')['Search Query'][0]
        )

    return visualize_trends_data(
        pd.read_excel(file, sheet_name='Trends'),
        pd.read_excel(file, sheet_name='Search Query')['Search Query'][0]
    )
