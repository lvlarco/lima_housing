# dashtools requirements
import pathlib

# import packages
import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from datetime import date, datetime, timedelta

# Read in the data
data_file = r'precio_trimestral_apartamentos.csv'
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
data = pd.read_csv(DATA_PATH.joinpath(data_file), index_col='Month')
data.index = pd.to_datetime(data.index)
district_cols = data.columns.insert(0, 'All Districts')

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
app.title = 'Apartment Prices in Lima'
server = app.server

app.layout = html.Div(
    id="app-container",
    style={'padding': '3vh 8vh 8vh 8vh'},
    children=[
        html.Div(
            id="header-area",
            children=[
                html.H1(
                    id="header-title",
                    children='Apartment Prices in Lima by Districts'),
                html.P(
                    children=['This application allows you to look at average apartment prices '
                              'in the city of Lima. Data extracted from the Banco Central de Reserva '
                              "del Peru's website.", html.Br(),
                              'Note: You must select a date range of more than 3 months if selecting a '
                              'custom time range.']
                )
            ],
            style={
                "margin-bottom": "30px",
            }
        ),
        html.Div(
            id="menu-area",
            children=[
                dbc.Row([
                    dbc.Col(
                        [
                            html.H5(
                                className="menu-title",
                                children='District'
                            ),
                            dcc.Dropdown(
                                id="district-filter",
                                className="dropdown",
                                options=[{"label": district, "value": district} for district in district_cols],
                                value='All Districts',
                                clearable=False,
                                disabled=False
                            )
                        ],
                        width=dict(size=3, offset='auto')
                    ),
                    dbc.Col(
                        [
                            html.H5(
                                className="menu-title",
                                children="Date Range"
                            ),
                            dcc.DatePickerRange(
                                id="date-range",
                                display_format='MMM YYYY',
                                # initial_visible_month=date(int(data.index.max().year), 1, 1),
                                min_date_allowed=data.index.min().date(),
                                max_date_allowed=data.index.max().date(),
                                start_date=data.index.min().date(),
                                end_date=data.index.max().date(),
                                month_format='MMM YYYY',
                                number_of_months_shown=2,
                                with_portal=True,
                                # updatemode='bothdates'
                            )
                        ],
                        width=dict(size='auto', offset='auto')
                    ),
                ]
                ),
                dbc.Col([
                    dbc.Alert(children='Select a timeframe longer than 3 months',
                              id='range-alert',
                              color='danger',
                              is_open=False),
                    dbc.Button('Search',
                               id='button-search',
                               disabled=False,
                               n_clicks=0)
                ],
                    width=dict(size=5, offset='auto')
                )
            ]
            ,
            style={
                "margin-bottom": "40px",
            }
        ),
        dbc.Row([
            dbc.Col([
                html.H4(
                    id='district-header',
                    children=['District Data:']
                ),
                html.H2(
                    id='district-name',
                    children=''
                ),
                html.H6(
                    id='district-info',
                    children='Please select a district for more information'
                ),
                html.H3(
                    id='district-return',
                    children=''
                )
            ],
                width=dict(size=2, offset=0)
            ),
            dbc.Col(
                dcc.Loading(
                    children=dbc.Col(
                        id="graph-container",
                        children=dcc.Graph(
                            id="price-chart",
                            figure=px.line(data),
                            config={"displayModeBar": True}
                        ),
                        width=dict(size='auto', offset='auto')
                    )
                ), style={'align': 'left'}
            )
        ])
    ]
)


@app.callback(Output(component_id='date-range', component_property='initial_visible_month'),
              Input(component_id="date-range", component_property="start_date"),
              Input(component_id="date-range", component_property="end_date"))
def update_visible_date(start_date, end_date):
    triggered_property = None
    for prop in dash.callback_context.args_grouping:
        if not prop.get('triggered'):
            continue
        else:
            triggered_property = prop.get('property')
    if triggered_property == 'start_date':
        return start_date
    elif triggered_property == 'end_date':
        end_date = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)
        return end_date
    else:
        return date(int(data.index.max().year), 1, 1)


@app.callback(Output(component_id='range-alert', component_property='is_open'),
              Output(component_id='button-search', component_property='disabled'),
              Input(component_id="date-range", component_property="start_date"),
              Input(component_id="date-range", component_property="end_date"))
def verify_time_range(start_date, end_date):
    """Checks the time range selected is valid"""
    valid_flag = check_min_timeframe(start_date, end_date)
    if valid_flag:
        return False, False
    else:
        return True, True


@app.callback(Output(component_id="price-chart", component_property="figure"),
              Input(component_id='button-search', component_property='n_clicks'),
              State(component_id="district-filter", component_property="value"),
              State(component_id="date-range", component_property="start_date"),
              State(component_id="date-range", component_property="end_date"))
def update_chart(_, district, start_date, end_date):
    """Updates the graph for the district selected"""
    if district == 'All Districts':
        filtered_data = data.loc[(data.index >= start_date) & (data.index <= end_date)]
    else:
        filtered_data = data[district]
        filtered_data = filtered_data.loc[(filtered_data.index >= start_date) &
                                          (filtered_data.index <= end_date)]
    fig = px.line(
        filtered_data,
    )
    fig.update_layout(
        yaxis_title="USD/m2",
        xaxis_title=None,
        legend_title=''
    )
    return fig


@app.callback(Output(component_id="district-name", component_property='children'),
              Output(component_id="district-info", component_property='children'),
              Output(component_id="district-return", component_property='children'),
              Input(component_id='button-search', component_property='n_clicks'),
              State(component_id="district-filter", component_property="value"),
              State(component_id="date-range", component_property="start_date"),
              State(component_id="date-range", component_property="end_date"))
def update_district_info(_, district, start_date, end_date):
    """Updates basic information aboue the district selected"""
    min_timeframe_flag = check_min_timeframe(start_date, end_date)
    if min_timeframe_flag:
        if district == 'All Districts':
            district = ''
            no_years = 'Please select a district for more information'
            perc_return = ''
        else:
            district = str(district)
            filtered_data = data[district]
            filtered_data.dropna(how='all', inplace=True)
            percent, time_val, time_str = calculate_returns(filtered_data, start_date, end_date)
            no_years = 'Return of investment in {} {} is'.format(time_val, time_str)
            perc_return = '{}%'.format(percent)
        return district, no_years, perc_return


def check_min_timeframe(start_date, end_date, threshold=89):
    """Checks minimum timeframe allowed to calculate District details
    :param start_date: beginning of time frame in str. Format %Y-%m-%d
    :param end_date: end of time frame in str. Format %Y-%m-%d
    :param threshold: number of days
    :return: bool. True if time range is valid
    """
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    start_date = data.loc[(data.index >= start_date)].index.min()
    end_date = data.loc[(data.index <= end_date)].index.max()
    flag = False
    if (end_date - start_date) > timedelta(days=threshold):
        flag = True
    return flag


def calculate_returns(df, start_date, end_date):
    """Calculates the percernt return over period of time"""
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    start_date = df.loc[(df.index >= start_date)].index.min()
    end_date = df.loc[(df.index <= end_date)].index.max()
    start_price = df.loc[start_date]
    end_price = df.loc[end_date]
    perc = round((end_price - start_price) / start_price * 100, 0)
    timeframe_val = len(pd.date_range(start=start_date, end=end_date, freq='Y', inclusive='left'))
    timeframe_str = 'years'
    if timeframe_val < 1:
        timeframe_val = len(pd.date_range(start=start_date, end=end_date, freq='M', inclusive='left'))
        timeframe_str = 'months'
    return perc, timeframe_val, timeframe_str


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=False)
    # app.run_server(debug=True)
