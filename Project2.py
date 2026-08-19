import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from dash import Dash, html, dcc, Input, Output, callback, dash_table

df = pd.read_csv('netflix_titles.csv')

df = df[df['type'] != 'TV Show']
df['director'] = df['director'].fillna('Unknown')
df["cast_list"] = df["cast"].fillna("").str.split(", ")
df['country'].fillna('Unkown')
df["cast_display"] = df["cast_list"].apply(lambda x: "<br>".join(x))
df.head()

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Div(
            "Select a director to see the genre breakdown for their movies. Click a pie slice to filter the table below.",
            style={
                "backgroundColor": "#f3f6fb",
                "border": "1px solid #d9e2f3",
                "borderRadius": "8px",
                "padding": "10px 12px",
                "marginBottom": "12px",
                "fontSize": "14px",
                "color": "#2b3a55"
            }
        ),
        dcc.Dropdown(
            id='director-dropdown',
            value='Christopher Nolan',
            options=[{'label': i, 'value': i} for i in sorted(df['director'].dropna().unique())]
        ),
        html.Div(
            "Choose a mode:",
            style={
                "backgroudColor": "#f3f6fb",
                "marginTop": "12px",
                "marginBottom": "6px",
                "fontSize": "14px",
                "fontWeight": "bold",
                "color": "#49552b"
            }
        ),
        dcc.RadioItems(
            id='view-mode',
            options=[
                {'label': 'Director view', 'value': 'director'},
                {'label': 'Actor view', 'value': 'actor'}
            ],
            value='director',
            inline=True
        ),
        html.Div(
            id='actor-picker-label',
            children="Choose an actor from this director's cast to view their other movies:",
            style={
                "backgroudColor": "#f3f6fb",
                "marginTop": "12px",
                "marginBottom": "6px",
                "fontSize": "14px",
                "fontWeight": "bold",
                "color": "#2b3a55"
            }
        ),
        dcc.Dropdown(
            id='actor-dropdown',
            placeholder='Select an actor',
            clearable=True,
            options=[]
        ),
        dcc.Graph(id="Director-Genre-Graph"),
        dcc.Graph(id="Actor-Rating-Graph", style={"display": "none"})
    ], style={"flex": "1", "paddingRight": "20px"}),

    html.Div([
        html.H3(
            id="table-title",
            children="Click a pie slice above to see matching movies",
            style={"marginTop": "0px"}
        ),

        dash_table.DataTable(
            id="movie-data-table",
            columns=[
                {"name": "title", "id": "title"},
                {"name": "cast", "id": "cast"},
                {"name": "release_year", "id": "release_year"},
                {"name": "country", "id": "country"}
            ],
            data=[],
            style_cell={
                "textAlign": "left",
                "padding": "10px",
                "whiteSpace": "pre-wrap"
            },
            page_size=10
        )
    ], style={"flex": "1", "paddingLeft": "20px"})

], style={"display": "flex", "flexDirection": "row", "alignItems": "flex-start"})


@callback(
    Output("Director-Genre-Graph", "figure"),
    Output("Actor-Rating-Graph", "figure"),
    Output("Actor-Rating-Graph", "style"),
    Input("director-dropdown", "value"),
    Input("actor-dropdown", "value"),
    Input("view-mode", "value")
)
def update_graph(selected_director, selected_actor, view_mode):
    hidden_style = {"display": "none"}
    visible_style = {"display": "block"}

    if not selected_director:
        empty_graph = px.bar(title="Select a director")
        return empty_graph, px.bar(title="Select a director"), hidden_style

    if view_mode == "actor":
        if not selected_actor:
            empty_graph = px.bar(title="Select an actor to view genre counts")
            return empty_graph, px.bar(title="Select an actor to view ratings"), visible_style

        actor_df = df[df["cast"].fillna("").str.contains(selected_actor, case=False, na=False)].copy()
        actor_df = actor_df[actor_df["director"] == selected_director].copy()

        genres = actor_df["listed_in"].fillna("").str.split(",").explode().str.strip()
        genre_counts = genres.value_counts().reset_index()
        genre_counts.columns = ["genre", "count"]

        genre_fig = px.bar(
            genre_counts,
            x="genre",
            y="count",
            color="genre",
            title=f"Genres for movies starring {selected_actor}",
            labels={"genre": "Genre", "count": "Number of Movies"}
        )

        rating_df = actor_df.dropna(subset=["rating"]).copy()
        rating_df["rating"] = rating_df["rating"].astype(str)
        rating_counts = rating_df["rating"].value_counts().reset_index()
        rating_counts.columns = ["rating", "count"]

        rating_fig = px.bar(
            rating_counts,
            x="rating",
            y="count",
            color="rating",
            title=f"Ratings for {selected_actor}",
            labels={"rating": "Rating", "count": "Number of Movies"}
        )

        return genre_fig, rating_fig, visible_style

    filtered_df = df[df["director"] == selected_director].copy()
    genres = filtered_df["listed_in"].fillna("").str.split(",").explode().str.strip()
    genre_counts = genres.value_counts().reset_index()
    genre_counts.columns = ["genre", "count"]

    pie_fig = px.pie(
        genre_counts,
        values="count",
        names="genre",
        title=f"Genre Distribution for {selected_director}<br>Number of movies: {filtered_df.shape[0]}"
    )

    return pie_fig, px.bar(title="Actor rating chart is available in actor view"), hidden_style


def format_cast(value):
    if pd.notna(value) and str(value).strip():
        names = [name.strip() for name in str(value).split(", ") if name.strip()]
        return "• " + "\n• ".join(names)
    return ""


@callback(
    Output("actor-dropdown", "options"),
    Output("actor-dropdown", "value"),
    Input("director-dropdown", "value")
)
def update_actor_dropdown(selected_director):
    if not selected_director:
        return [], None

    actor_names = sorted({
        name.strip()
        for cast_names in df.loc[df["director"] == selected_director, "cast"].fillna("").str.split(", ")
        for name in cast_names
        if name and name.strip()
    })

    return [{"label": actor, "value": actor} for actor in actor_names], None


@callback(
    Output("actor-picker-label", "style"),
    Output("actor-dropdown", "style"),
    Input("view-mode", "value")
)
def toggle_actor_picker(view_mode):
    if view_mode == "actor":
        return {
            "marginTop": "12px",
            "marginBottom": "6px",
            "fontSize": "14px",
            "fontWeight": "bold",
            "color": "#2b3a55"
        }, {"display": "block"}
    return {"display": "none"}, {"display": "none"}


@callback(
    Output("movie-data-table", "data"),
    Output("table-title", "children"),
    Input("Director-Genre-Graph", "clickData"),
    Input("director-dropdown", "value"),
    Input("actor-dropdown", "value"),
    Input("view-mode", "value")
)
def update_table_on_click(click_data, selected_director, selected_actor, view_mode):
    if not selected_director:
        return [], "Select a director to view records."

    if view_mode == "actor":
        if not selected_actor:
            return [], "Select an actor to view their movies."

        related_df = df[df["cast"].fillna("").str.contains(selected_actor, case=False, na=False)].copy()
        related_df = related_df.sort_values("release_year", ascending=False)
        display_df = related_df[["title", "cast", "release_year", "country"]].copy()
        display_df["cast"] = display_df["cast"].apply(format_cast)
        return display_df.to_dict("records"), f"Movies featuring {selected_actor}"

    table_df = df[df["director"] == selected_director].copy()

    if table_df.empty:
        return [], f"No movies found for {selected_director}"

    if click_data is not None:
        clicked_genre = click_data["points"][0]["label"]
        table_df = table_df[
            table_df["listed_in"].fillna("").str.contains(clicked_genre, case=False, na=False)
        ]
        title_text = f"Movies matching genre: '{clicked_genre}' by {selected_director}"
    else:
        title_text = f"Showing all movies for {selected_director}"

    display_df = table_df[["title", "cast", "release_year", "country"]].copy()
    display_df["cast"] = display_df["cast"].apply(format_cast)

    return display_df.to_dict("records"), title_text

if __name__ == '__main__':
    app.run(debug=True)
