
from importlib.resources import path
from dash import Dash, html, dcc, Input, Output, callback, ctx
import dash
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
#import db
import csv
from datetime import timedelta, date
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash_extensions.javascript import arrow_function
import dash_bootstrap_components as dbc
import dash_core_components as dcc

#--------------------------------------------------------------------#
#웹 구성
#page 1 --> 월간 통계 적용
#index_page 구성
# 전체 분포 지도, 
# 사이드바(발생 순위)->top5 plot 그리기, 
# 발생수(today, total)
#page 2
#구 -> 일주월 추이 그래프, 정지선 TOP5, 인도TOP5 
#동 -> 일주월 추이 그래프, CCTV위치(마커표시), 
#cctv->일주일단위의 추이표(현재가 젤 뒤에 있는), CCTV에서의 범법행위 개수
#--------------------------------------------------------------------#


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


app = Dash(__name__,suppress_callback_exceptions=True)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

#1. data 
cities=["광진구","강동구","성동구","강남구","강서구","강북구","관악구","구로구","금천구","노원구","동대문구","도봉구","동작구","마포구","서대문구","성북구","서초구","송파구","영등포구","용산구","양천구","은평구","종로구","중구","중랑구"]

#임시데이터
df = pd.DataFrame({
    "SIG_KOR_NM": ["광진구","강동구","성동구","강남구","강서구","강북구","관악구","구로구","금천구","노원구","동대문구","도봉구","동작구","마포구","서대문구","성북구","서초구","송파구","영등포구","용산구","양천구","은평구","종로구","중구","중랑구"],
    "Amount": [1000,500,100,0,234,764,2436,764,34,87,12,76,235,764,124,7853,14,564,236,764,1348,536,234,546,5271]
})


#서울시 구 데이터 로드
geometry = json.load(open('./assets/TL_SCCO_SIG.json',encoding='utf-8'))

#Choropleth 시각화 -> 추후 SIG_KOR_NM column 을 누구나 알아볼 수 있게 바꿀예정(ex.city)
fig=px.choropleth(df,geojson=geometry,locations='SIG_KOR_NM',color='Amount',
                  color_continuous_scale='Blues',
                  featureidkey='properties.SIG_KOR_NM')
fig.update_geos(fitbounds="locations",visible=False)
fig.update_layout(title_text="example",title_font_size=20, width=1100)

#서울시 동 데이터 로드
dong = json.load(open('./assets/seoul.json',encoding='utf-8'))

#추이 그래프를 위한 임시 데이터
data1=pd.read_csv('assets\data1.csv')

#2. content
header = html.Div(
    children=[
                html.P(children=html.Img(src="assets\motorcycle.ico", ), className="header_img"),
                html.H1(children="Zol-zol-zol", className="header_title"),
                html.P(children="설명~", className="header_description"),
            ],
            className='header_box',
)

dropdown = html.Div(
    children=[
        html.Div(
            children=[
                html.H4(children='기간 설정',className='dropdown_title'),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    min_date_allowed=date(2000, 1, 1),
                    max_date_allowed=date(2022, 10, 16),
                    initial_visible_month=date(2022, 9, 15),
                    className="dropdown",
                ),
            ]
        ),
        html.Div(
            children=[
                html.H4(children='이동수단 설정',className='menu_title'),
                dcc.Dropdown(
                    ['오토바이'], '오토바이', 
                    id='mobility-dropdown',
                    style={
                        'width':"18rem",
                    },
                    className="dropdown",
                ),
                html.Div(id='dd_mobility'),
            ]
        ),],
    className="dropdown_bg",
)

# 추이 그래프 선택 창
controls = html.Div(
    children=[
        dbc.Card(
            [dbc.FormGroup(
                    [
                        #dbc.Label("Options"),
                        dcc.RadioItems(id="display_figure", 
                        options=[{'label': 'None', 'value': 'Nope'},
                                {'label': '일간 통계', 'value': '일간 통계'},
                                {'label': '주간 통계', 'value': '주간 통계'},
                                {'label': '월간 통계', 'value': '월간 통계'}
                            ],
                        value='Nope',
                        labelStyle={'display': 'inline-block', 'width': '10em', 'line-height':'0.5em'}
                        ) 
                    ], 
                ),
                dbc.FormGroup(
                    [dbc.Label(""),]
                ),
            ],
            body=True,
            style = {'font-size': 'large'}),],
            className='controls',
    )
    

container = html.Div(
    children=[
        dbc.Container([
            html.H1("범법행위 발생 추이"),
            html.Hr(),
            dbc.Row([
                dbc.Col([controls],xs = 4),
                dbc.Col([
                    dbc.Row([
                        dbc.Col(dcc.Graph(id="analystics")),
                    ])
                ]),
            ]),
            html.Br(),
            dbc.Row([
    
            ]), 
        ],
        fluid=True,)
    ],
    className='container',
)


#3. *layout(고정)*
app.layout = html.Div([

    header,

    # represents the browser address bar and doesn't render anything
    dcc.Location(id='url', refresh=False),
    
    # content will be rendered in this element
    html.Div(id='page-content'),
    #html.Div(id="hidden_div_for_redirect_callback")

])

#page1 content 
index_page = html.Div([
    dropdown,
    dcc.Graph(id='graph',figure=fig, className='graph'),
    html.Div(id='index'),
    print("index"),

])

fig1 = go.Figure(go.Scattermapbox())




#4. function
#두 번째 페이지 그래프(layout)
def analytics_page(location):
    print(location)
    
    #왼쪽 지도 관련
    features = {"type": "FeatureCollection","features":[i for i in dong['features'] if i['properties']['sggnm']==location]}
    xy=features['features'][0]['geometry']['coordinates'][0][0][5]
    #crime_info = db.select_gu(str(location))
    fig1.add_trace(go.Scattermapbox(
        #lat= crime_info['x'] if not crime_info.empty else [],
        #lon=crime_info['y'] if not crime_info.empty else [],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=14,
            color='rgb(242, 24, 24)'
        ),
        #text=crime_info['location'] if not crime_info.empty else [],
    ))
    fig1.update_layout(
            mapbox = {
                'style': "carto-positron",
                'center': { 'lon': xy[0], 'lat': xy[1]},
                'zoom': 12, 
                'layers': [{ 
                    'source': features,
                    'type': "fill", 
                    'below': "traces", 
                    'color': "royalblue"}]},
            margin = {'l':0, 'r':0, 'b':0, 't':0},
            clickmode='select')        
    #fig1.layout.hovermode = 'closest'        
    
    #오른쪽 그래프 관련 수정수정수정하자~~~~~~~~~~~~~~~~
    #data= go.Bar(x=list(i.to_pydatetime().day for i in crime_info['time']))
    #fig2 = go.Figure(data=data)
    #fig2.add_trace(
    #     go.Scatter(x=list(i.to_pydatetime().day for i in crime_info['time']),line = dict(color='red'))
    # )     
    
    return html.Div(id="analytics_page-content",
        children=[
        dcc.Location(id='url_2', refresh=False),
        html.Div(id="title",
                children=[
                    html.Div(id = "second_page"),
                    html.Div(location),
                    dcc.Dropdown(cities,location,id="city-dropdown",style={'width':"50%","float": "left"}),
                    html.H2("Dashboard",style={"float": "left"})],
                className='analytics_page-content'),
        dcc.Graph(id='dong-graph',figure=fig1,className='dong_graph',
                style={'width':"55%","float": "left", 'margin-top':'25px'}),
        #일주월 추이그래프
        container,
        #html.Div(id="map",children=[
           #   dcc.Graph(id='diverse-graph',figure=fig2)],style={'width':"50%","float": "right"})
    ])


def detail_page(detail_location):
    return html.Div(id="detail_page-content",children=[
        
        html.Div("i clieked"+detail_location)
    ])

@callback(
    Output('url', 'href'),
    Input('city-dropdown', 'value'), prevent_initial_call=True)
def move_page_dropdown(value):
    print("move")
    print(value)
    if value is not None:    
        return "/"+value
        
#첫 번째 그래프 클릭 시 상세 그래프로 페이지 이동    
@callback(
    Output('url', 'pathname'),
    Input('graph', 'clickData'), prevent_initial_call=True)
def move_page(clickData):
    print(clickData)
    if clickData is not None:            
        location = clickData['points'][0]['location']
        return "/"+location
    else : return "/"
    
@callback(Output('page-content', 'children'),
               Input('url', 'pathname'),prevent_initial_call=True)
def display_page(pathname):
    print("display")
    
    print(pathname)
    for city in df['SIG_KOR_NM']:
        if pathname == '/'+city :
            return analytics_page(city)

    return  index_page

@callback(Output('analytics_page-content', 'children'),
               Input('url','href'),prevent_initial_call=True)
def display_page2(href):
    print("display2")
    print(href)
    
    for city in df['SIG_KOR_NM']:
        if href=="/"+city:
            return analytics_page(city),
    

    return  index_page

# def update_point(trace, points, selector):
#     with fig1.batch_update():
#         return

       

@callback(Output("detail_page-content",'chiledren'),
          Input('dong-graph','clickData'))
def A(clickData):
    print("^^"+clickData)
    return
    

#첫 번째 페이지 추이 그래프
@app.callback(
    Output("analystics", "figure"),
    [Input("display_figure", "value"),

    ],
)
def make_graph(display_figure):

    # main trace
    print(display_figure)
    if 'Nope' in display_figure:
        fig = go.Figure()
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          yaxis = dict(showgrid=False, zeroline=False, tickfont = dict(color = 'rgba(0,0,0,0)')),
                          xaxis = dict(showgrid=False, zeroline=False, tickfont = dict(color = 'rgba(0,0,0,0)')))
        return fig

    if '일간 통계' in display_figure:
        fig = go.Figure(go.Scatter(x=data1['date'], y=data1['case1'],
                mode='lines+markers', name='횡단보도 주행 위반'))
        fig.add_traces(go.Scatter(x=data1['date'], y=data1['case2'],
                mode='lines+markers', name='보행자도로 통행 위반'))
        fig.update_layout(template='plotly_dark')

    # prediction trace
    if '주간 통계' in display_figure:
        fig = go.Figure(go.Scatter(x=data1['date'], y=data1['case1'],
                mode='lines+markers', name='횡단보도 주행 위반'))
        fig.add_traces(go.Scatter(x=data1['date'], y=data1['case2'],
                mode='lines+markers', name='보행자도로 통행 위반'))
        fig.update_layout(template='seaborn')

    if '월간 통계' in display_figure:
        fig = go.Figure(go.Scatter(x=data1['date'], y=data1['case1'],
                mode='lines+markers', name='횡단보도 주행 위반'))
        fig.add_traces(go.Scatter(x=data1['date'], y=data1['case2'],
                mode='lines+markers', name='보행자도로 통행 위반'))
        fig.update_layout(template='plotly_white')

    # Aesthetics
    fig.update_layout(margin= {'t':50, 'b':0, 'r': 0, 'l': 0, 'pad': 0})
    #fig.update_layout(hovermode = 'x')
    #fig.update_layout(showlegend=True, legend=dict(x=1,y=0.85))
    fig.update_layout(uirevision='constant')
    fig.update_layout(title='<b>월별 범법행위 발생 추이')

    return(fig)





if __name__ == '__main__':
    app.run_server(debug=True)