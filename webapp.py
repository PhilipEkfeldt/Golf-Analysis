import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd

data_2018 =pd.read_csv('data/player_category_sg_2018', header=[0, 1], index_col=[0,1])

options = pd.DataFrame()

options['label'] = data_2018.index.get_level_values(level = 1)
options['value'] = data_2018.index.get_level_values(level = 0)

optionsP = options.to_dict('records')
def sort_index(string):
    return int(string.replace('=', '-').partition("-")[2])

def getSortValue(category):
    return distance_categories.index(category)

distance_categories = sorted(data_2018.columns.levels[0], key= sort_index )
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

max_player = pd.DataFrame( columns=['cat', 'player_name', 'adjusted_strokes_gained']) 

min_player = pd.DataFrame( columns=['cat', 'player_name', 'adjusted_strokes_gained'])

for cat in distance_categories:
    min_df = data_2018[cat][data_2018[cat]['shot_count'] > 30]
    min_row = min_df.loc[[min_df['adjusted_strokes_gained'].idxmin(axis=0)]].reset_index()[['player_name', 'adjusted_strokes_gained']]
    min_row['cat'] = cat
    min_player = min_player.append(min_row, ignore_index=True, sort=False)
    
    max_df = data_2018[cat][data_2018[cat]['shot_count'] > 30]
    max_row = max_df.loc[[max_df['adjusted_strokes_gained'].idxmax(axis=0)]].reset_index()[['player_name', 'adjusted_strokes_gained']]
    max_row['cat'] = cat
    max_player = max_player.append(max_row, ignore_index=True, sort=False)

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.layout = html.Div(children=[
    html.H1(
        children='Strokes Gained - Distance Categories',
        style={
            'textAlign': 'center'
        }),
    html.H3(
        children='Data source: PGA Tour Shotlink',
        style={
            'textAlign': 'center'
        }
        ),
    dcc.Dropdown(
        id="player_selection",
        options=optionsP,
        multi=True,
        value = ['8793']
    ),
    dcc.Checklist(
    id = "max_min",
    options=[
        {'label': 'Show max', 'value': 'ShowMax'},
        {'label': 'Show min', 'value': 'ShowMin'},
    ],
    values=[]
    ),
    dcc.Graph(
        id='chart',
    )
])
@app.callback(
    dash.dependencies.Output('chart', 'figure'),
    [dash.dependencies.Input('player_selection', 'value'),
    dash.dependencies.Input('max_min', 'values')])
def update_graph(player_selection, max_min):
    plots = []
    for player in player_selection:
        playerdf = data_2018[data_2018.index.get_level_values('PlayerNr') == int(player)]
        if(len(playerdf) > 0):
            player_name = playerdf.index.get_level_values('player_name')[0]
            playerdf = playerdf.transpose().unstack(level=1)
            playerdf.columns = ['adj_sg', 'shot_count']
            playerdf['cat_ind'] = pd.Series(playerdf.index.values).apply(getSortValue).values
            playerdf = playerdf.sort_values('cat_ind')
            pplot = go.Scatter (  
                x = playerdf.index.values, 
                y = playerdf['adj_sg'].round(3), 
                name = player_name,
                text =  "Nr of shots: " + playerdf['shot_count'].astype(int).astype(str),
            )
            plots.append(pplot)


    if "ShowMax" in max_min:
        plots.append( go.Scatter( x = max_player['cat'], y = max_player['adjusted_strokes_gained'].round(3), name = "Max", text = max_player['player_name']) )

    if "ShowMin" in max_min:
        plots.append( go.Scatter( x = min_player['cat'], y = min_player['adjusted_strokes_gained'].round(3), name = "Min", text = min_player['player_name'] ) )

    layout = go.Layout(
            title="Average strokes gained per shot in category",
            xaxis=dict(
                title='Category (yards from hole)',
                titlefont=dict(
                    family='Courier New, monospace',
                    size=18,
                    color='#7f7f7f'
                     )
                ),
            yaxis=dict(
                title='Strokes gained per shot',
                titlefont=dict(
                    family='Courier New, monospace',
                    size=18,
                    color='#7f7f7f'
                    )
                )
            )
    return {"data":plots, "layout": layout } 

if __name__ == '__main__':
    app.run_server(debug=True)