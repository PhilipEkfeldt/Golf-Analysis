import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
#Load data
data_2018 =pd.read_csv('data/player_category_sg_2018', header=[0, 1], index_col=[0,1])

#Player dictionary
player_options = pd.DataFrame()

player_options['label'] = data_2018.index.get_level_values(level = 1)
player_options['value'] = data_2018.index.get_level_values(level = 0)

player_options = player_options.to_dict('records')


def sort_index(string):
    return int(string.replace('=', '-').partition("-")[2])

def getSortValue(category):
    return distance_categories.index(category)

#Sort categories in correct order
distance_categories = sorted(data_2018.columns.levels[0], key= sort_index )

#Stylesheet 
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    {
        'href': 'https://codepen.io/chriddyp/pen/bWLwgP.css',
        'rel': 'stylesheet',
    }
]

#Define max and min player based on darta
max_player = pd.DataFrame( columns=['cat', 'player_name', 'adj_sg']) 

min_player = pd.DataFrame( columns=['cat', 'player_name', 'adj_sg'])

for cat in distance_categories:
    min_df = data_2018[cat][data_2018[cat]['shot_count'] > 30]
    min_row = min_df.loc[[min_df['adj_sg'].idxmin(axis=0)]].reset_index()[['player_name', 'adj_sg']]
    min_row['cat'] = cat
    min_player = min_player.append(min_row, ignore_index=True, sort=False)
    
    max_df = data_2018[cat][data_2018[cat]['shot_count'] > 30]
    max_row = max_df.loc[[max_df['adj_sg'].idxmax(axis=0)]].reset_index()[['player_name', 'adj_sg']]
    max_row['cat'] = cat
    max_player = max_player.append(max_row, ignore_index=True, sort=False)
#Create app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
#Layout
app.layout = html.Div(children=[
    html.H2(
        children='Strokes Gained - Distance Categories',
        style={
            'textAlign': 'center'
        }),
    html.H4(
        children='Data source: PGA Tour Shotlink',
        style={
            'textAlign': 'center'
        }
        ),
    dcc.Dropdown(
        id="player_selection",
        options=player_options,
        multi=True,
        value = ['8793']
    ),
    dcc.Checklist(
    id = "max_min",
    options=[
        {'label': 'Show max', 'value': 'ShowMax'},
        {'label': 'Show min', 'value': 'ShowMin'},
        {'label': 'Show 95% confidence interval', 'value': 'Show95'},

    ],
    labelClassName='checkable',
    values=[],
    ),
    dcc.Graph(
        id='chart',
    )
])
#Callback to update chart
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
            playerdf.columns =  [ '95_up', '95_low', 'adj_sg', 'shot_count', 'std', 'std_err']
            playerdf['cat_ind'] = pd.Series(playerdf.index.values).apply(getSortValue).values
            playerdf = playerdf.sort_values('cat_ind')
            #Show confidence interval
            if 'Show95' in max_min:
                pplot = go.Scatter (  
                    x = playerdf.index.values, 
                    y = playerdf['adj_sg'].round(3), 
                    name = player_name,
                    text =  "Nr of shots: " + playerdf['shot_count'].astype(int).astype(str),
                    error_y=dict(
                    type='data',
                    symmetric=True,
                    array=1.96*playerdf['std_err'],
                    )        
                )
            else:
                    pplot = go.Scatter (  
                    x = playerdf.index.values, 
                    y = playerdf['adj_sg'].round(3), 
                    name = player_name,
                    text =  "Nr of shots: " + playerdf['shot_count'].astype(int).astype(str),
                    
                ) 
            plots.append(pplot)

    #Checkbox settings
    if "ShowMax" in max_min:
        plots.append( go.Scatter( x = max_player['cat'], y = max_player['adj_sg'].round(3), name = "Max", text = max_player['player_name']) )

    if "ShowMin" in max_min:
        plots.append( go.Scatter( x = min_player['cat'], y = min_player['adj_sg'].round(3), name = "Min", text = min_player['player_name'] ) )
    
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