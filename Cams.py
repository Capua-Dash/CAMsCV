import json
import ssl
import time
from datetime import datetime

import dash_auth
import pymssql
import cv2
import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd
from dash import Dash, dcc, html, Input, Output
from flask import Flask, Response
from plotly import graph_objects as go

from orm.mapping_orindiuva import Dados_da_Usina

import pyautogui

"""
====================================================================================================
                                    COMEÇO DO DASHBOARD DO MAPA
====================================================================================================
"""

login = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Row([
        dbc.Col([
            html.H3("Login")
        ], width={"offset": 4, "size": 4})
    ], style={"margin-top": "50px"}),
    dbc.Row([
        dbc.Col([
            html.H6("Cápua")

        ], width={"offset": 4, "size": 4}),
        dbc.Col([
            html.Span(id='username-validation')
        ], width={"offset": 4, "size": 4})
    ], style={"margin-top": "20px"}),
    dbc.Row([
        dbc.Col([
            dbc.Input(id='password-input', type="password", placeholder="Senha")
        ], width={"offset": 4, "size": 4}),
        dbc.Col([
            html.Span(id='password-validation')
        ], width={"offset": 4, "size": 4})
    ], style={"margin-top": "20px"}),
    dbc.Row([
        dbc.Col([
            dbc.Button("Entrar", id='login-button', n_clicks=0, color="primary")
        ], width={"offset": 4, "size": 4})
    ], style={"margin-top": "20px"})
], className="container")

query2 = "SELECT ((SUM(MGE_ENER)/1200)*(1000/SUM(PI_ENER))*100) FROM Estatisticos WHERE CONVERT(CHAR(7)," \
         "(E3TimeStamp),121) = CONVERT(CHAR(7),(GETDATE()),121) "

query_o = f"SELECT TOP 1 ((MGE_ENER / 1200) * (1000 / PI_ENER)) * 100 FROM PFM2022 ORDER BY E3TimeStamp DESC"

query_pp = f"SELECT ((SUM(MGE_ENER)/2400)*(1000/SUM(PI_ENER))*100) FROM Estatisticos WHERE CONVERT(CHAR(7)," \
           f"(E3TimeStamp),121) = CONVERT(CHAR(7),(GETDATE()),121) "

URL_EF = "mysql+mysqlconnector://root:capua123@localhost:3306/elias_fausto"
URL_PP = 'mysql+mysqlconnector://root:capua123@localhost:3306/paraguacu_paulista'
URL_MA = 'mysql+mysqlconnector://root:capua123@localhost:3306/monte_alto'
URL_Su = 'mysql+mysqlconnector://root:capua123@localhost:3306/suzano'
URL_Ta = 'mysql+mysqlconnector://root:capua123@localhost:3306/taubate'

paraguacu = """{'points': [{'curveNumber': 4, 'pointNumber': 0, 'pointIndex': 0, 'location': 3535507, 'z': 1,
                         'bbox': {'x0': 269.50668501846417, 'x1': 269.50668501846417, 'y0': 587.5410001558035,
                                  'y1': 587.5410001558035}}]}"""
elias = """{'points': [{'curveNumber': 2, 'pointNumber': 0, 'pointIndex': 0, 'location': 3514908, 'z': 1,
                     'bbox': {'x0': 594.0686076598562, 'x1': 594.0686076598562, 'y0': 651.8308037482001,
                              'y1': 651.8308037482001}}]}"""
monte = """{'points': [{'curveNumber': 3, 'pointNumber': 0, 'pointIndex': 0, 'location': 3531308, 'z': 0.5,
                     'bbox': {'x0': 477.79886186512147, 'x1': 477.79886186512147, 'y0': 452.9674770500308,
                              'y1': 452.9674770500308}}]}"""
orindiuva = """{'points': [{'curveNumber': 1, 'pointNumber': 0, 'pointIndex': 0, 'location': 3534203, 'z': 0,
                         'bbox': {'x0': 396.85084183798597, 'x1': 396.85084183798597, 'y0': 349.16671038687684,
                                  'y1': 349.16671038687684}}]}"""
suzano = """{'points': [{'curveNumber': 5, 'pointNumber': 0, 'pointIndex': 0, 'location': 3552502, 'z': 1, 
'bbox': {'x0': 701.5752825679477, 'x1': 701.5752825679477, 'y0': 711.2488053614167, 'y1': 711.2488053614167}}]} """
# pp_json = json.dumps(paraguacu)
# ef_json = json.dumps(elias)
# ma_json = json.dumps(monte)
# or_json = json.dumps(orindiuva)
pp_json = eval(paraguacu)
ef_json = eval(elias)
ma_json = eval(monte)
or_json = eval(orindiuva)
su_json = eval(suzano)


def statusinv(usina, inv):
    modbus = Dados_da_Usina(None, None, None, None)
    return modbus.get_regs(usina, inv) if not modbus.get_regs(usina, inv) == 0 else "Conexão instável"

#191.242.49.24

def up_camera(usina):
    if usina == "elias_fausto":
        return dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Img(src="/video_feedef", className='video_camera')
                ))
            , sm=12)
    if usina == "orindiuva":
        return dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Img(src="/video_feedor", className='video_camera')
                ))

            , sm=12)
    if usina == "monte_alto":
        return dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        html.Img(src="/video_feedma2", className='video_camera')
                    )),

                sm=12),
        ])

    if usina == "paraguacu_paulista":
        return dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        html.Img(src="/video_feedpp2", className='video_camera_pp')
                    ))

                , sm=12),
        ])
    if usina == "suzano":
        return dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        html.Img(src="/video_feedsu", className='video_camera_pp')
                    ))

                , sm=12),
        ])


def muda_usina_cm(usina, reg):
    modbus = Dados_da_Usina(None, None, None, None)
    return round(modbus.get_regs(usina, reg[0]), 1), round(modbus.get_regs(usina, reg[1]), 1), round(
        modbus.get_regs(usina, reg[2]), 1), round(modbus.get_regs(usina, reg[3]), 1)


def muda_usina(usina, branco=False):
    dia3 = datetime.now()
    dia3 = dia3.strftime("%Y-%m-%d")
    if usina == 'elias_fausto':
        engine = create_engine(URL_EF)
        query = f"""SELECT ISI, PU, timestamp 
                    FROM central_meteorologica 
                    WHERE timestamp >= '{dia3} 06:00:00.000' 
                      AND timestamp <= '{dia3} 19:00:00.000'
                    """

        df = pd.read_sql(query, engine)
        IrrPot = go.Figure()
        IrrPot.add_trace(
            go.Scatter(x=df['timestamp'].values, y=df['PU'].values,
                       mode='lines', name='PU'))
        IrrPot.add_trace(
            go.Scatter(x=df['timestamp'].values, y=df['ISI'].values,
                       mode='lines', name='ISI'))
        IrrPot.update_layout(margin=dict(t=0, r=0, b=0, l=0),
                             font_color='#ffffff' if branco else None,
                             plot_bgcolor='RGBA(0,0,0,0)',
                             paper_bgcolor='RGBA(0,0,0,0)', showlegend=False,
                             xaxis=dict(showline=True, showgrid=False, showticklabels=True))

        IrrPot.update_yaxes(range=[0, 1500])
        IrrPot.update_xaxes(range=[f"{dia3} 06:00:00.000000",
                                   f"{dia3} 19:00:00.000000"])
        return IrrPot

    if usina == 'orindiuva':
        engine = create_engine(URL_Or)
        query = f"""SELECT ISI, PU, timestamp 
                    FROM central_meteorologica 
                    WHERE timestamp >= '{dia3} 06:00:00.000' 
                      AND timestamp <= '{dia3} 19:00:00.000'
                    """

        df = pd.read_sql(query, engine)
        IrrPot = go.Figure()
        IrrPot.add_trace(
            go.Scatter(x=df['timestamp'].values, y=df['PU'].values,
                       mode='lines', name='PU'))
        IrrPot.add_trace(
            go.Scatter(x=df['timestamp'].values, y=df['ISI'].values,
                       mode='lines', name='ISI'))
        IrrPot.update_layout(margin=dict(t=0, r=0, b=0, l=0),
                             font_color='#ffffff' if branco else None,
                             plot_bgcolor='RGBA(0,0,0,0)',
                             paper_bgcolor='RGBA(0,0,0,0)', showlegend=False,
                             xaxis=dict(showline=True, showgrid=False, showticklabels=True))

        IrrPot.update_yaxes(range=[0, 1500])
        IrrPot.update_xaxes(range=[f"{dia3} 06:00:00.000000",
                                   f"{dia3} 19:00:00.000000"])
        return IrrPot
    if usina == 'paraguacu_paulista':
        engine = create_engine(URL_PP)
        query = f"""SELECT ISI, PU, timestamp 
                    FROM central_meteorologica 
                    WHERE timestamp >= '{dia3} 06:00:00.000' 
                    AND timestamp <= '{dia3} 19:00:00.000'
                """

        df = pd.read_sql(query, engine)

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['PU'],
                       mode='lines', name='PU', yaxis='y')
        )

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['ISI'],
                       mode='lines', name='ISI', yaxis='y2')
        )

        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            font_color='#ffffff' if branco else None,
            plot_bgcolor='RGBA(0,0,0,0)',
            paper_bgcolor='RGBA(0,0,0,0)',
            showlegend=False,
            xaxis=dict(showline=True, showgrid=False, showticklabels=True),
            yaxis2=dict(range=[0, 1500]),
            yaxis=dict(range=[0, 3000], side='right', overlaying='y', showgrid=False)
        )

        fig.update_xaxes(range=[f"{dia3} 06:00:00.000000", f"{dia3} 19:00:00.000000"])

        return fig

    if usina == 'monte_alto':
        engine = create_engine(URL_MA)
        query = f"""SELECT ISI, PU, timestamp 
                    FROM central_meteorologica 
                    WHERE timestamp >= '{dia3} 06:00:00.000' 
                      AND timestamp <= '{dia3} 19:00:00.000'
                    """

        df = pd.read_sql(query, engine)
        IrrPot = go.Figure()
        IrrPot.add_trace(
            go.Scatter(x=df['timestamp'].values, y=df['PU'].values,
                       mode='lines', name='PU'))
        IrrPot.add_trace(
            go.Scatter(x=df['timestamp'].values, y=df['ISI'].values,
                       mode='lines', name='ISI'))
        IrrPot.update_layout(margin=dict(t=0, r=0, b=0, l=0),
                             font_color='#ffffff' if branco else None,
                             plot_bgcolor='RGBA(0,0,0,0)',
                             paper_bgcolor='RGBA(0,0,0,0)', showlegend=False,
                             xaxis=dict(showline=True, showgrid=False, showticklabels=True))

        IrrPot.update_yaxes(range=[0, 1500])
        IrrPot.update_xaxes(range=[f"{dia3} 06:00:00.000000",
                                   f"{dia3} 19:00:00.000000"])
        return IrrPot
    if usina == 'suzano':
        engine = create_engine(URL_Su)
        query = f"""SELECT ISI, PU, timestamp 
                    FROM central_meteorologica 
                    WHERE timestamp >= '{dia3} 06:00:00.000' 
                    AND timestamp <= '{dia3} 19:00:00.000'
                """

        df = pd.read_sql(query, engine)

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['PU'],
                       mode='lines', name='PU', yaxis='y')
        )

        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['ISI'],
                       mode='lines', name='ISI', yaxis='y2')
        )

        fig.update_layout(
            margin=dict(t=0, r=0, b=0, l=0),
            font_color='#ffffff' if branco else None,
            plot_bgcolor='RGBA(0,0,0,0)',
            paper_bgcolor='RGBA(0,0,0,0)',
            showlegend=False,
            xaxis=dict(showline=True, showgrid=False, showticklabels=True),
            yaxis2=dict(range=[0, 1500]),
            yaxis=dict(range=[0, 3000], side='right', overlaying='y', showgrid=False)
        )

        fig.update_xaxes(range=[f"{dia3} 06:00:00.000000", f"{dia3} 19:00:00.000000"])

        return fig


def mostra_estado(usina, reg):
    modbus = Dados_da_Usina(None, None, None, None)
    if usina == "elias_fausto":
        return modbus.get_invs('elias_fausto', reg[0]) if not modbus.get_invs('elias_fausto',
                                                                              reg[0]) == 0 else "Conexão instável", \
               modbus.get_invs('elias_fausto', reg[1]) if not modbus.get_invs('elias_fausto',
                                                                              reg[1]) == 0 else "Conexão instável", \
               modbus.get_invs('elias_fausto', reg[2]) if not modbus.get_invs('elias_fausto',
                                                                              reg[2]) == 0 else "Conexão instável", \
               modbus.get_invs('elias_fausto', reg[3]) if not modbus.get_invs('elias_fausto',
                                                                              reg[3]) == 0 else "Conexão instável"
    if usina == "orindiuva":
        return modbus.get_invs('orindiuva', reg[0]) if not modbus.get_invs('orindiuva',
                                                                           reg[0]) == 0 else "Conexão instável", \
               modbus.get_invs('orindiuva', reg[1]) if not modbus.get_invs('orindiuva',
                                                                           reg[1]) == 0 else "Conexão instável", \
               modbus.get_invs('orindiuva', reg[2]) if not modbus.get_invs('orindiuva',
                                                                           reg[2]) == 0 else "Conexão instável", \
               modbus.get_invs('orindiuva', reg[3]) if not modbus.get_invs('orindiuva',
                                                                           reg[3]) == 0 else "Conexão instável"

    if usina == "monte_alto":
        return modbus.get_regs('monte_alto', reg[0]) if not modbus.get_regs('monte_alto',
                                                                            reg[0]) == 0 else "Conexão instável", \
               modbus.get_regs('monte_alto', reg[1]) if not modbus.get_regs('monte_alto',
                                                                            reg[1]) == 0 else "Conexão instável", \
               modbus.get_regs('monte_alto', reg[2]) if not modbus.get_regs('monte_alto',
                                                                            reg[2]) == 0 else "Conexão instável", \
               modbus.get_regs('monte_alto', reg[3]) if not modbus.get_regs('monte_alto',
                                                                            reg[3]) == 0 else "Conexão instável"

    if usina == "paraguacu_paulista":
        return modbus.get_regs('paraguacu_paulista', reg[0]) if not modbus.get_regs('paraguacu_paulista',
                                                                                    reg[
                                                                                        0]) == 0 else "Conexão instável", \
               modbus.get_regs('paraguacu_paulista', reg[1]) if not modbus.get_regs('paraguacu_paulista',
                                                                                    reg[
                                                                                        1]) == 0 else "Conexão instável", \
               modbus.get_regs('paraguacu_paulista', reg[2]) if not modbus.get_regs('paraguacu_paulista',
                                                                                    reg[
                                                                                        2]) == 0 else "Conexão instável", \
               modbus.get_regs('paraguacu_paulista', reg[3]) if not modbus.get_regs('paraguacu_paulista',
                                                                                    reg[
                                                                                        3]) == 0 else "Conexão instável"
    if usina == "suzano":
        return modbus.get_invs('suzano', reg[0]) if not modbus.get_invs('suzano',
                                                                        reg[0]) == 0 else "Conexão instável", \
               modbus.get_invs('suzano', reg[1]) if not modbus.get_invs('suzano',
                                                                        reg[1]) == 0 else "Conexão instável", \
               modbus.get_invs('suzano', reg[2]) if not modbus.get_invs('suzano',
                                                                        reg[2]) == 0 else "Conexão instável", \
               modbus.get_invs('suzano', reg[3]) if not modbus.get_invs('suzano',
                                                                        reg[3]) == 0 else "Conexão instável"


navbar2 = dbc.NavbarSimple(
    children=[
        dbc.Row(
            [
                dbc.Col(html.Img(src='assets/sabesp.png', className='sabesp'), width="auto"),
                dbc.Col(html.Img(src='assets/CAPUA-ENGENHARIA.webp', className='logo'), width="auto"),
                dbc.Col(html.H4('MAPA', className='options'), width="auto"),
                dbc.Col(id='carregando2', width="auto"),
                dbc.Col(dbc.NavLink("Gráficos", href="http://187.95.20.103:8052/graficos", className="options2"),
                        width="auto"),
                dbc.Col(dbc.NavLink("Cartões", href='http://187.95.20.103:8052/cartoes', className='options3'),
                        width="auto"),
                dbc.Col(
                    dbc.NavItem([
                        dbc.Row(
                            daq.BooleanSwitch(
                                id='automatico',
                                on=True,
                                color="#008080"
                            ), className="toggle"),
                        dbc.Row(html.H6("AUTO", className="auto")),
                    ]),
                    width="auto"
                ),
                dbc.Col(
                    dcc.Interval(id='time', interval=1000, n_intervals=0),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Span(datetime.now().strftime("%H:%M:%S"), className="hora", id="DATA")
                        ], className='lidata')
                    ], className="card_hora"),
                    width="auto"
                ),
            ],
            align="center",
            className='g-0',
            style={"flex-wrap": "nowrap"}
        )
    ],
    color="light",
    dark=False,
    fluid=True,
    className='nav'
)

# navbar2 = dbc.NavbarSimple(
#     children=[
#         html.Img(src='assets/sabesp.png', className='sabesp'),
#         html.Img(src='assets/CAPUA-ENGENHARIA.webp', className='logo'),
#         html.H4('MAPA', className='options'),
#         html.Div(id='carregando2'),
#         dbc.NavLink("Gráficos", href="http://187.95.20.103:8052/graficos", className="options2"),
#         dbc.NavLink("Cartões", href='http://187.95.20.103:8052/cartoes', className='options3'),
#         dbc.NavItem([
#             dbc.Row(
#                 daq.BooleanSwitch(
#                     id='automatico',
#                     on=True,
#                     color="#008080"
#                 ), className="toggle"),
#             dbc.Row(html.H6("AUTO", className="auto")),
#
#         ]),
#         dcc.Interval(id='time', interval=1000, n_intervals=0),
#         dbc.Row([
#             dbc.Col(dbc.Card([
#                 dbc.CardBody([
#                     html.Span(datetime.now().strftime("%H:%M:%S"), className="hora", id="DATA")
#                 ], className='lidata')
#             ], className="card_hora"))
#         ])
#     ],
#     color="light",
#     dark=False,
#     fluid=True,
#     className='nav'
# )

URL_Or = "mysql+mysqlconnector://root:capua123@localhost:3306/orindiuva"

server_bd = '40.114.35.162'
databaseor = 'UFV_Orindiuva'
databaseef = 'UFV_EliasFausto'
databasema = 'UFV_MonteAlto'
databasepp = 'UFV_ParaguaçuPaulista'
databasesu = 'UFV_Suzano'
username = 'administrador'
password = '20ca11ad20!!'

csv_ef = r'C:\Users\G4S\joshua_teste\files\ef.csv'
csv_ma = r'C:\Users\G4S\joshua_teste\files\ma.csv'
csv_or = r'C:\Users\G4S\joshua_teste\files\or.csv'
csv_pp = r'C:\Users\G4S\joshua_teste\files\pp.csv'
csv_su = r'C:\Users\G4S\joshua_teste\files\su.csv'

dia10 = datetime.now()
dia10 = dia10.strftime("%Y-%m-%d")


def tem_falha(db, n):
    dia10 = datetime.now()
    dia10 = dia10.strftime("%Y-%m-%d")
    modbus = Dados_da_Usina(None, None, None, None)
    if db == 'orindiuva' and not db == 'elias_fausto':
        invs = [modbus.get_invs(db, n[0]), modbus.get_invs(db, n[1]), modbus.get_invs(db, n[2]),
                modbus.get_invs(db, n[3])]
        print(invs)

        i = 0

        estados = ["Chave de parada", "Parada de emergência", "Iniciando espera", "Em espera", "Partindo",
                   "Falha de comunicação",
                   "Falha", "Parado", "Desclassificação", "Expedição", "Alarme ativo"]

        for inv in invs:
            if inv in estados:
                i += 1
        if i:
            return True
        else:
            return False
    else:
        if db == "monte_alto":
            invs = [modbus.get_regs(db, 157), modbus.get_regs(db, 257), modbus.get_regs(db, 357),
                    modbus.get_regs(db, 457)]
            print(invs)

            i = 0

            estados = ['Em espera', 'Falha', 'Falha permanente', 'Não encontrado']

            for inv in invs:
                if inv in estados:
                    i += 1
            if i:
                return True
            else:
                return False

        if db == 'paraguacu_paulista' or db == "suzano":
            invs = [modbus.get_regs(db, 157), modbus.get_regs(db, 257), modbus.get_regs(db, 357),
                    modbus.get_regs(db, 457),
                    modbus.get_regs(db, 557), modbus.get_regs(db, 657), modbus.get_regs(db, 757),
                    modbus.get_regs(db, 857)]
            print(invs)

            i = 0

            estados = ['Em espera', 'Falha', 'Falha permanente', 'Não encontrado']

            for inv in invs:
                if inv in estados:
                    i += 1
            if i:
                return True
            else:
                return False


def tem_falha2(db, n):
    dia10 = datetime.now()
    dia10 = dia10.strftime("%Y-%m-%d")
    modbus = Dados_da_Usina(None, None, None, None)
    if db == 'orindiuva' and not db == 'elias_fausto':
        invs = [modbus.get_invs(db, n[0]), modbus.get_invs(db, n[1]), modbus.get_invs(db, n[2]),
                modbus.get_invs(db, n[3])]
        print(invs)

        if all(inv == "Conexão Instável" for inv in invs):
            return False

        return True

    else:
        if db == "monte_alto":
            invs = [modbus.get_regs(db, 157), modbus.get_regs(db, 257), modbus.get_regs(db, 357),
                    modbus.get_regs(db, 457)]
            print(invs)

            if all(inv == "Conexão Instável" for inv in invs):
                return False

            return True

        if db == 'paraguacu_paulista' or db == "suzano":
            invs = [modbus.get_regs(db, 157), modbus.get_regs(db, 257), modbus.get_regs(db, 357),
                    modbus.get_regs(db, 457),
                    modbus.get_regs(db, 557), modbus.get_regs(db, 657), modbus.get_regs(db, 757),
                    modbus.get_regs(db, 857)]
            print(invs)

            if all(inv == "Conexão Instável" for inv in invs):
                return False

            return True


tem = [tem_falha2('orindiuva', [4, 1, 3, 2]) and tem_falha('orindiuva', [4, 1, 3, 2]),
       tem_falha2('elias_fausto', [1, 2, 3, 4]) and tem_falha('elias_fausto', [1, 2, 3, 4]),
       tem_falha2('monte_alto', None) and tem_falha('monte_alto', None),
       tem_falha2('paraguacu_paulista', None) and tem_falha('paraguacu_paulista', None),
       tem_falha2('suzano', None) and tem_falha('suzano', None)]


class VideoPP(object):
    def __init__(self):
        self.video_pp2 = cv2.VideoCapture('rtsp://admin:Capua123@186.251.7.22:1200/cam/realmonitor?channel=3&subtype=1')

    def __del__(self):
        self.video_pp2.release()

    def get_frame(self):
        try:
            successpp2, imagepp2 = self.video_pp2.read()
            retpp2, jpegpp2 = cv2.imencode(r'.jpg', imagepp2)

            return jpegpp2.tobytes()
        except Exception:
            return


class VideoOR(object):
    def __init__(self):
        self.video_or = cv2.VideoCapture('rtsp://admin:capua123@45.176.175.27:1500/cam/realmonitor?channel=1&subtype=1')

    def __del__(self):
        self.video_or.release()

    def get_frame(self):
        try:
            successor, imageor = self.video_or.read()
            retor, jpegor = cv2.imencode(r'.jpeg', imageor)

            return jpegor.tobytes()
        except Exception:
            print(Exception)


class VideoEF(object):
    def __init__(self):
        self.video = cv2.VideoCapture(
            'rtsp://admin:Capua123@177.101.74.222:1400/cam/realmonitor?channel=1&subtype=1')

    def __del__(self):
        self.video.release()

    def get_frame(self):
        try:
            success, image = self.video.read()
            ret, jpeg = cv2.imencode(r'.jpeg', image)

            return jpeg.tobytes()
        except Exception:
            print(Exception)


class VideoMA(object):
    def __init__(self):
        self.video = cv2.VideoCapture(
            'rtsp://admin:ancora206141@45.170.209.104:1200/cam/realmonitor?channel=3&subtype=1')

    def __del__(self):
        self.video.release()

    def get_frame(self):
        try:
            success, image = self.video.read()
            ret, jpeg = cv2.imencode(r'.jpeg', image)

            return jpeg.tobytes()
        except Exception:
            print(Exception)


class VideoSu(object):
    def __init__(self):
        self.video = cv2.VideoCapture(
            'rtsp://admin:Capua123@45.182.195.252:1200/cam/realmonitor?channel=5&subtype=1')

    def __del__(self):
        self.video.release()

    def get_frame(self):
        try:
            success, image = self.video.read()
            ret, jpeg = cv2.imencode(r'.jpeg', image)

            return jpeg.tobytes()
        except Exception:
            print(Exception)


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


cam = Flask(__name__)


@cam.route('/video_feedor')
def video_feedor():
    return Response(gen(VideoOR()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@cam.route('/video_feedef')
def video_feedef():
    return Response(gen(VideoEF()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@cam.route('/video_feedma2')
def video_feedma2():
    return Response(gen(VideoMA()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@cam.route('/video_feedpp2')
def video_feedpp2():
    return Response(gen(VideoPP()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@cam.route('/video_feedsu')
def video_feedsu():
    return Response(gen(VideoSu()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def IDGT_func(db, query):
    df = executar_query(query, db, None)

    IDGT = go.Figure()

    if df.values[0] < 77.5:
        IDGT.add_trace(go.Bar(x=['IDGT'], y=[df.values[0][0]], text=round(df.values[0][0], 2),
                              textfont=dict(
                                  color="white",
                                  size=16),
                              width=0.52,
                              orientation='v'))
        IDGT.update_yaxes(range=[0, 100])
        IDGT.update_layout(margin=dict(t=0, r=0, b=0, l=0),
                           # font_color='white',
                           plot_bgcolor='RGBA(0,0,0,0)',
                           paper_bgcolor='RGBA(0,0,0,0)', yaxis=dict(showgrid=False))
        IDGT.update_traces(marker_color='#e96a54',
                           marker_line_color='#ffffff',
                           marker_line_width=1.5
                           )

        return IDGT
    else:
        IDGT.add_trace(go.Bar(x=['IDGT'], y=[df.values[0][0]], text=round(df.values[0][0], 2),
                              textfont=dict(
                                  color="white",
                                  size=16), width=0.52,
                              orientation='v'))
        IDGT.update_yaxes(range=[0, 100])
        IDGT.update_layout(margin=dict(t=0, r=0, b=0, l=0),
                           # font_color='white',
                           plot_bgcolor='RGBA(0,0,0,0)',
                           paper_bgcolor='RGBA(0,0,0,0)', yaxis=dict(showgrid=False))
        # IDGT.update_traces(marker_color='rgb(160,200,255)', marker_line_color='rgb(8,48,107)',
        #                    marker_line_width=1.5)
        return IDGT


query = "SELECT TOP 1 INV1, INV2, INV3, INV4, E3TimeStamp FROM Inversores WHERE convert(char(16), E3TimeStamp, " \
        "121) <= convert(char(16), GETDATE() , 121) ORDER BY E3TimeStamp DESC"


def executar_query(query, db, i, tudo=False):
    if i is None:
        conn = create_engine(f"mssql+pymssql://{username}:{password}@{server_bd}/{db}")
        return pd.read_sql(query, conn)
    else:
        conn = pymssql.connect(server_bd, username, password, db)
        cursor = conn.cursor()
        cursor.execute(query)
        if tudo:
            return cursor.fetchall()
        else:
            resultado = cursor.fetchone()
            return resultado[i]


dia = datetime.now()
dia = str(dia)

row = executar_query("SELECT TOP 1 ((MGE_ENER / 1200) * (1000 / PI_ENER)) * 100 FROM PFM2022 ORDER BY E3TimeStamp DESC",
                     databaseor, 0)
IDGT = go.Figure()
IDGT.add_trace(go.Bar(x=['IDGT'], y=[row], width=0.52, orientation='v', text=round(row, 2),
                      textfont=dict(color="white", size=16)))
IDGT.update_yaxes(range=[0, 100])
IDGT.update_layout(margin=dict(t=0, r=0, b=0, l=0), font_color='white', plot_bgcolor='RGBA(0,0,0,0)',
                   paper_bgcolor='RGBA(0,0,0,0)', yaxis=dict(showgrid=False))
IDGT.update_traces(marker_color='rgb(160,200,255)', marker_line_color='rgb(8,48,107)',
                   marker_line_width=1.5)

token = open(r"C:\Users\G4S\joshua_teste\mapa\.mapbox_token").read()  # you will need your own token

colorscale = ['#ff0000', '#ffff00', '#85b0bd', '#00ff00', '#0000ff']

excel = r'C:\Users\G4S\joshua_teste\files\cores2.xlsx'

df = pd.read_excel(excel)  # replace with your own data source
df_csv_ef = pd.read_csv(csv_ef)
df_csv_ma = pd.read_csv(csv_ma)
df_csv_or = pd.read_csv(csv_or)
df_csv_pp = pd.read_csv(csv_pp)
df_csv_su = pd.read_csv(csv_su)
geojson = json.load(open(r"C:\Users\G4S\joshua_teste\files\sp_geo.json", "r", encoding='utf-8'))

fig = go.Figure()

fig.add_trace(go.Choroplethmapbox(z=df['value'],
                                  locations=df['id'],
                                  colorscale=colorscale,
                                  featureidkey="properties.id",
                                  below=True,
                                  geojson=geojson,
                                  hoverinfo='none',
                                  marker_line_width=0.1, marker_opacity=1,
                                  showscale=False))

fig.add_trace(go.Choroplethmapbox(z=df_csv_or['value'],
                                  locations=df_csv_or['id'],
                                  colorscale=['red' if tem[0] else 'blue', 'blue' if not tem[0] else 'red'],
                                  featureidkey="properties.id",
                                  below=True,
                                  geojson=geojson,
                                  hoverinfo='none',
                                  marker_line_width=0.1, marker_opacity=1,
                                  showscale=False))

fig.add_trace(go.Choroplethmapbox(z=df_csv_ef['value'],
                                  locations=df_csv_ef['id'],
                                  colorscale=['red' if tem[1] else 'blue', 'blue' if not tem[1] else 'red'],
                                  featureidkey="properties.id",
                                  below=True,
                                  geojson=geojson,
                                  hoverinfo='none',
                                  marker_line_width=0.1, marker_opacity=1,
                                  showscale=False))

fig.add_trace(go.Choroplethmapbox(z=df_csv_ma['value'],
                                  locations=df_csv_ma['id'],
                                  colorscale=['red' if tem[2] else 'blue', 'blue' if not tem[2] else 'red'],
                                  featureidkey="properties.id",
                                  below=True,
                                  geojson=geojson,
                                  hoverinfo='none',
                                  marker_line_width=0.1, marker_opacity=1,
                                  showscale=False))

fig.add_trace(go.Choroplethmapbox(z=df_csv_pp['value'],
                                  locations=df_csv_pp['id'],
                                  colorscale=['red' if tem[3] else 'blue', 'blue' if not tem[3] else 'red'],
                                  featureidkey="properties.id",
                                  below=True,
                                  geojson=geojson,
                                  hoverinfo='none',
                                  marker_line_width=0.1, marker_opacity=1,
                                  showscale=False))
fig.add_trace(go.Choroplethmapbox(z=df_csv_su['value'],
                                  locations=df_csv_su['id'],
                                  colorscale=['red' if tem[4] else 'blue', 'blue' if not tem[4] else 'red'],
                                  featureidkey="properties.id",
                                  below=True,
                                  geojson=geojson,
                                  hoverinfo='none',
                                  marker_line_width=0.1, marker_opacity=1,
                                  showscale=False))
# fig.update_traces(below="aeroway-polygon", selector=dict(type='scattermapbox'))
fig.add_trace(go.Scattermapbox(
    lat=[-20.1795, -23.0435, -21.2616, -22.4193, -23.5420],
    lon=[-49.3487, -47.3743, -48.4966, -50.5922, -46.3110],
    marker={'color': 'black', 'opacity': 1, 'size': 1},
    mode='text+markers',
    showlegend=False,
    textposition='top center',
    hoverinfo='skip',
    text=[f"Orindiúva", 'Elias Fausto', 'Monte Alto', 'Paraguaçu Paulista', 'Suzano'],
    textfont=dict(color='black', size=17),
))
fig.update_layout(height=990,
                  mapbox=dict(
                      center={"lat": -22.5, "lon": -48.58228565534156},
                      accesstoken=token,
                      zoom=6.13,
                      style="light",
                  ),
                  margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  )

app5 = Dash(__name__, external_stylesheets=[dbc.themes.MORPH], server=cam, url_base_pathname="/")

container2 = dbc.Container([
    html.Meta(name='viewport', content="width=device-width, initial-scale=1.0"),
    html.Link(rel="stylesheet", type="text/css", href="/pages/assets/style.css"),
    dbc.Row(dbc.Col(navbar2, sm=12)),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='MAP', figure=fig, className='mapa'),
            dcc.Interval(id='intervalmap', interval=5 * 60000, n_intervals=0),
        ], sm=6, style={"border-right": "3px solid white"}),
        dbc.Col([
            dcc.Loading([
                dbc.Row([
                    dbc.Col([
                        html.H4(id='nameusina', className='title')
                    ], sm=4, className='paddingcardbody'),
                    dbc.Col([
                        dbc.Card(
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Img(src='assets/horizontal.png',
                                                 title='Irradiação Solar Horizontal', className='img'),
                                    ], sm=6),
                                    dbc.Col([html.P(id='p-ish', className='centerlin'),
                                             dcc.Interval(id='it-ish', interval=5 * 60000)
                                             ], sm=6)
                                ], className='row'),
                            ], className='cardbody'),
                            className='cartao')
                    ], sm=2, className='paddingcardbody'),
                    dbc.Col([
                        dbc.Card(
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([html.Img(src='assets/inclinada.png',
                                                      title='Irradiação Solar Inclinada', className='img'),
                                             ], sm=6),
                                    dbc.Col([html.P(id='p-isi', className='centerlin'),
                                             dcc.Interval(id='it-isi', interval=5 * 60000)
                                             ], sm=6),
                                ], className='row'),
                            ], className='cardbody'),
                            className='cartao')
                    ], sm=2, className='paddingcardbody'),
                    dbc.Col([
                        dbc.Card(
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col(html.Img(src='assets/temp-ambiente.png',
                                                     title='Temperatura Ambiente', className='img'),
                                            sm=6),
                                    dbc.Col([html.P(id='p-ta', className='centerlin'),
                                             dcc.Interval(id='it-ta', interval=5 * 60000)
                                             ], sm=6)
                                ], className='row')
                            ], className='cardbody'),
                            className='cartao')
                    ], sm=2, className='paddingcardbody'),
                    dbc.Col([
                        dbc.Card(
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col(html.Img(src='assets/temp_placas.png',
                                                     title='Temperatura das Placas', className='img'),
                                            sm=6),
                                    dbc.Col([html.P(id='p-tp', className='centerlin'),
                                             dcc.Interval(id='it-tp', interval=5 * 60000)
                                             ], sm=6)
                                ]),
                            ], className='cardbody'),
                            className='ultimo_cartao')
                    ], sm=2, className='paddingcardbody'),
                ], className='cm'),
            ], type='default'),
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            dcc.Loading(
                                [
                                    dcc.Graph(id='PUxISI', className="irrpot"),
                                    dcc.Interval(id='i-p-g', interval=5 * 60000, n_intervals=0)
                                ]
                                , type='graph'),

                        ], sm=10),
                        dbc.Col([
                            dcc.Loading([
                                dbc.Col(dcc.Graph(id='IDGT', figure=IDGT, className='idgt')),
                            ], type='dot'),
                            dcc.Interval(id='it-idgt', interval=5 * 60000, n_intervals=0)

                        ], sm=2)
                    ], style={'border-top': '1px solid white'}),
                ], sm=12),
            ]),
            dcc.Loading([
                dbc.Row([
                    dbc.Col([
                        dbc.Card(
                            dbc.CardBody([
                                html.P(children=[html.Span('INV1: '),
                                                 html.Span(" - ", className='colorinv', id='inv1')],
                                       className='rowinv'), dcc.Interval(id='it-inv1', interval=5 * 60000)
                            ]), className='cardbodyinv', id="inv1-cor")

                    ], sm=3),
                    dbc.Col([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[html.Span('INV2: '),
                                             html.Span(" - ", className='colorinv', id='inv2'
                                                       )],
                                   className='rowinv'), dcc.Interval(id='it-inv2', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv2-cor")

                    ], sm=3),
                    dbc.Col([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[html.Span('INV3: '),
                                             html.Span(" - ", className='colorinv', id='inv3',
                                                       )],
                                   className='rowinv'), dcc.Interval(id='it-inv3', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv3-cor")
                    ], sm=3),
                    dbc.Col([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[html.Span('INV4: '),
                                             html.Span(" - ", className='colorinv', id='inv4'
                                                       )],
                                   className='rowinv'), dcc.Interval(id='it-inv4', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv4-cor")

                    ], sm=3),
                ]),
                html.Div(id='div-invs'),
                html.Div(id='div-invs-su')
            ], type='default'),
            dcc.Loading(html.Div([
            ], id='cams')
                , type='cube'),

        ], sm=6),
    ]),
    html.Meta(httpEquiv="refresh", content=f"{str(26 * 60)};url=http://187.95.20.103:8052/"),
    dcc.Interval(id='change_auto', interval=50000, n_intervals=0)], fluid=True, className='container-fluid')

# app.layout = html.Div(container)
app5.layout = html.Div(container2)

cert = r'C:\Users\G4S\joshua_teste\pages\cert.pem'
key = r'C:\Users\G4S\joshua_teste\pages\key.pem'

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(certfile=cert, keyfile=key)

# @cam.route("/")
# def home():
#     return app.index()


"""
=====================================================================================================
                                        FIM DO DASHBOARD DO MAPA
====================================================================================================
"""

"""
=====================================================================================================
                                    COMEÇO DO DASHBOARD DOS CARTÕES
=====================================================================================================
"""
from dash import Dash, html, dcc, Input, Output
from datetime import datetime
import dash_bootstrap_components as dbc
from modbus.mapping import Dados_da_Usina

dia = datetime.now()
dia = dia.strftime("%Y-%m-%d")
dia = str(dia)

server_bd = '40.114.35.162'
databaseor = 'UFV_Orindiuva'
databaseef = 'UFV_EliasFausto'
databasema = 'UFV_MonteAlto'
databasepp = 'UFV_ParaguaçuPaulista'
username = 'administrador'
password = '20ca11ad20!!'

query = "SELECT ((SUM(MGE_ENER)/1200)*(1000/SUM(PI_ENER))*100) FROM Estatisticos WHERE CONVERT(CHAR(7)," \
        "(E3TimeStamp),121) = CONVERT(CHAR(7),(GETDATE()),121) "

query_o = f"SELECT TOP 1 ((MGE_ENER / 1200) * (1000 / PI_ENER)) * 100 FROM PFM2022 ORDER BY E3TimeStamp DESC"

query_pp = f"SELECT ((SUM(MGE_ENER)/2400)*(1000/SUM(PI_ENER))*100) FROM Estatisticos WHERE CONVERT(CHAR(7)," \
           f"(E3TimeStamp),121) = CONVERT(CHAR(7),(GETDATE()),121) "
query_su = f"SELECT ((SUM(MGE_ENER)/2400)*(1000/SUM(PI_ENER))*100) FROM Estatisticos WHERE CONVERT(CHAR(7)," \
           f"(E3TimeStamp),121) = CONVERT(CHAR(7),(GETDATE()),121) "


def IDGT_func2(db, querie):
    df = executar_query(querie, db, None)

    if df.values[0][0] < 77.5:
        return round(df.values[0][0], 2), dict(color="#ff0000"), dict(color="#ff0000")
    else:
        return round(df.values[0][0], 2), dict(color="#ffffff"), dict(color="#ffffff")


def cm(var):
    dia3 = datetime.now()
    dia3 = dia3.strftime("%Y-%m-%d")
    dia3 = str(dia3)

    modbus = Dados_da_Usina(None, None, None, None)

    if var == 'taOR':
        # df = executar_query("SELECT TOP 1 ISI, TA, TP, E3TimeStamp FROM CentralMet WHERE convert(char(16),
        # " "E3TimeStamp, 121) >= convert(char(16), GETDATE() , 121) ORDER BY E3TimeStamp DESC", databaseor, None)
        return f'{round(modbus.get_regs("orindiuva", 233), 2)} °C'

    if var == 'taEF':
        return f'{round(modbus.get_regs("elias_fausto", 235), 2)} °C'

    if var == 'taMA':
        return f'{round(modbus.get_regs("monte_alto", 9), 2)} °C'

    if var == 'taPP':
        return f'{round(modbus.get_regs("paraguacu_paulista", 9), 2)} °C'

    if var == 'taSu':
        return f'{round(modbus.get_regs("suzano", 9), 2)} °C'

    if var == 'isi1':
        return f'{round(modbus.get_regs("orindiuva", 223), 2)} W/m²'
    if var == 'isi2':
        return f'{round(modbus.get_regs("elias_fausto", 225), 2)} W/m²'
    if var == 'isi3':
        return f'{round(modbus.get_regs("monte_alto", 3), 2)} W/m²'
    if var == 'isi4':
        return f'{round(modbus.get_regs("paraguacu_paulista", 3), 2)} W/m²'
    if var == 'isi5':
        return f'{round(modbus.get_regs("suzano", 3), 2)} W/m²'

    if var == 'PotOR':
        return f'{round(modbus.get_regs("orindiuva", 405), 2)} kW'
    if var == "PotEF":
        return f'{round(modbus.get_regs("elias_fausto", 425), 2)} kW'

    if var == "PotMA":
        return f'{round(modbus.get_regs("monte_alto", 55), 2)} kW'

    if var == "PotPP":
        return f'{round(modbus.get_regs("paraguacu_paulista", 55), 2)} kW'

    if var == "PotSu":
        return f'{round(modbus.get_regs("suzano", 55), 2)} kW'


def inv(engine, n, i):
    modbus = Dados_da_Usina(None, None, None, None)

    counter = 0
    if n == 4:
        if engine == 'monte_alto':
            armazenamento = [modbus.get_regs(engine, i[0]), modbus.get_regs(engine, i[1]),
                             modbus.get_regs(engine, i[2]), modbus.get_regs(engine, i[3])]
            for i in range(0, len(armazenamento)):
                if 'Funcionando' == armazenamento[i] or 'Gerando' == armazenamento[i] or 'Alarme ativo' == \
                        armazenamento[i] or not armazenamento[i]:
                    counter += 1
        else:
            armazenamento = [modbus.get_invs(engine, i[0]), modbus.get_invs(engine, i[1]),
                             modbus.get_invs(engine, i[2]), modbus.get_invs(engine, i[3])]
            for i in range(0, len(armazenamento)):
                if 'Funcionando' == armazenamento[i] or 'Gerando' == armazenamento[i] or 'Alarme ativo' == \
                        armazenamento[i] or not armazenamento[i]:
                    counter += 1
        return f'{counter} de 4'
    if n == 8:
        if engine == "suzano":
            armazenamento = [modbus.get_regs('suzano', 157), modbus.get_regs('suzano', 257),
                             modbus.get_regs('suzano', 357), modbus.get_regs('suzano', 457),
                             modbus.get_regs('suzano', 557), modbus.get_regs('suzano', 657),
                             modbus.get_regs('suzano', 757), modbus.get_regs('suzano', 857)]
            for i in range(0, len(armazenamento)):
                if armazenamento[i] == 'Gerando' or not armazenamento[i]:
                    counter += 1
        if engine == "paraguacu_paulista":
            armazenamento = [modbus.get_regs('paraguacu_paulista', 157), modbus.get_regs('paraguacu_paulista', 257),
                             modbus.get_regs('paraguacu_paulista', 357), modbus.get_regs('paraguacu_paulista', 457),
                             modbus.get_regs('paraguacu_paulista', 557), modbus.get_regs('paraguacu_paulista', 657),
                             modbus.get_regs('paraguacu_paulista', 757), modbus.get_regs('paraguacu_paulista', 857)]
            for i in range(0, len(armazenamento)):
                if armazenamento[i] == 'Gerando' or not armazenamento[i]:
                    counter += 1
        return f'{counter} de 8'


# navbar = dbc.NavbarSimple(
#     children=[
#         dbc.NavItem([html.Img(src='assets/sabesp.png', className='sabesp')]),
#         dbc.NavItem(
#             [html.Img(src='assets/CAPUA-ENGENHARIA.webp', className='logo'
#                       )]),
#         dbc.NavItem(html.H4('OVERVIEW', className='options')),
#         dbc.NavItem(dbc.NavLink("Gráficos", href="http://187.95.20.103:8052/graficos"), className='options2'),
#         dbc.NavItem(dbc.NavLink("Mapa", href="http://187.95.20.103:8052/"), className='options3'),
#         dbc.NavItem([
#             dbc.Row([
#                 dbc.Col([
#                     dbc.Card(
#                         dbc.CardBody([
#                             html.Span(datetime.now().strftime("%H:%M:%S"), className="hora", id="DATA"),
#                             dcc.Interval(id='data-itvl', interval=1000, n_intervals=0)
#                         ])
#                         , className="card_hora"),
#                 ]),
#             ])
#         ]),
#     ],
#     color="dark",
#     dark=True,
#     fluid=True,
# )

navbar = dbc.NavbarSimple(
    children=[
        dbc.Row(
            [
                dbc.Col(html.Img(src='assets/sabesp.png', className='sabesp'), width="auto"),
                dbc.Col(html.Img(src='assets/CAPUA-ENGENHARIA.webp', className='logo'), width="auto"),
                dbc.Col(html.H4('MAPA', className='options'), width="auto"),
                dbc.Col(id='carregando2', width="auto"),
                dbc.Col(dbc.NavLink("Gráficos", href="http://187.95.20.103:8052/graficos", className="options2"),
                        width="auto"),
                dbc.Col(dbc.NavLink("Mapa", href='http://187.95.20.103:8052/', className='options3'),
                        width="auto"),
                dbc.Col(
                    dbc.NavItem([
                        dbc.Row(
                            daq.BooleanSwitch(
                                id='automatico',
                                on=True,
                                color="#008080"
                            ), className="toggle"),
                        dbc.Row(html.H6("AUTO", className="auto")),
                    ]),
                    width="auto"
                ),
                dbc.Col(
                    dcc.Interval(id='time', interval=1000, n_intervals=0),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Span(datetime.now().strftime("%H:%M:%S"), className="hora", id="DATA")
                        ], className='lidata')
                    ], className="card_hora"),
                    width="auto"
                ),
            ],
            align="center",
            className='g-0',
            style={"flex-wrap": "nowrap"}
        )
    ],
    color="light",
    dark=False,
    fluid=True,
    className='nav'
)

cartoes = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col(navbar, sm=12)),

            dbc.Row([
                html.H4('Orindiúva')
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Inversores funcionando')]),
                            dbc.Row([html.H4('None', id='invs0')]),
                            dcc.Interval(id='up-inv-0', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Temperatura ambiente')]),
                            dbc.Row(html.H4('None', id='ta0')),
                            dcc.Interval(id='up-ta-0', interval=10000, n_intervals=0),
                        ]),
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Irradiação')]),
                            dbc.Row([html.H4('None', id='isi0')]),
                            dcc.Interval(id='up-isi-0', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('Geração')),
                            dbc.Row(html.H4('None', id='mge0')),
                            dcc.Interval(id='up-mge-0', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('IDGT', id='red0')),
                            dbc.Row(html.H4('None', id='idgt0')),
                            dcc.Interval(id='up-idgt-0', interval=10000, n_intervals=0),
                        ])
                    )
                ])
            ]),
            dbc.Row([
                html.H4('Elias Fausto')
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Inversores funcionando')]),
                            dbc.Row([html.H4('None', id='invs1')]),
                            dcc.Interval(id='up-inv-1', interval=10000, n_intervals=0),
                        ])
                    )

                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Temperatura ambiente')]),
                            dbc.Row(html.H4('None', id='ta1')),
                            dcc.Interval(id='up-ta-1', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Irradiação')]),
                            dbc.Row([html.H4('None', id='isi1')]),
                            dcc.Interval(id='up-isi-1', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('Geração')),
                            dbc.Row(html.H4('None', id='mge1')),
                            dcc.Interval(id='up-mge-1', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('IDGT', id='red1')),
                            dbc.Row(html.H4('None', id='idgt1')),
                            dcc.Interval(id='up-idgt-1', interval=10000, n_intervals=0),
                        ])
                    )
                ])
            ]),
            dbc.Row([
                html.H4('Monte Alto')
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Inversores funcionando')]),
                            dbc.Row([html.H4('None', id='invs2')]),
                            dcc.Interval(id='up-inv-2', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Temperatura ambiente')]),
                            dbc.Row(html.H4('None', id='ta2')),
                            dcc.Interval(id='up-ta-2', interval=10000, n_intervals=0),

                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Irradiação')]),
                            dbc.Row([html.H4('None', id='isi2')]),
                            dcc.Interval(id='up-isi-2', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('Geração')),
                            dbc.Row(html.H4('None', id='mge2')),
                            dcc.Interval(id='up-mge-2', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('IDGT', id='red2')),
                            dbc.Row(html.H4('None', id='idgt2')),
                            dcc.Interval(id='up-idgt-2', interval=10000, n_intervals=0),
                        ])
                    )
                ])
            ]),
            dbc.Row([
                html.H4('Paraguaçu Paulista')
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Inversores funcionando')]),
                            dbc.Row([html.H4('None', id='invs3')]),
                            dcc.Interval(id='up-inv-3', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Temperatura ambiente')]),
                            dbc.Row(html.H4('None', id='ta3')),
                            dcc.Interval(id='up-ta-3', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Irradiação')]),
                            dbc.Row([html.H4('None', id='isi3')]),
                            dcc.Interval(id='up-isi-3', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('Geração')),
                            dbc.Row(html.H4('None', id='mge3')),
                            dcc.Interval(id='up-mge-3', interval=10000, n_intervals=0),
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('IDGT', id='red3')),
                            dbc.Row(html.H4('None', id='idgt3')),
                            dcc.Interval(id='up-idgt-3', interval=10000, n_intervals=0),
                        ])
                    )
                ])
            ]),
            dbc.Row([
                html.H4('Suzano')
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Inversores funcionando')]),
                            dbc.Row([html.H4('-')])
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Temperatura ambiente')]),
                            dbc.Row(html.H4('-'))
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Irradiação')]),
                            dbc.Row([html.H4('-')])
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('Geração')),
                            dbc.Row(html.H4('-'))
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('IDGT')),
                            dbc.Row(html.H4('-')),
                        ])
                    )
                ])
            ]),
            dbc.Row([
                html.H4('Taubaté')
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Inversores funcionando')]),
                            dbc.Row([html.H4('-')])
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Temperatura ambiente')]),
                            dbc.Row(html.H4('-'))
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row([html.H5('Irradiação')]),
                            dbc.Row([html.H4('-')])
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('Geração')),
                            dbc.Row(html.H4('-'))
                        ])
                    )
                ]),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            dbc.Row(html.H5('IDGT')),
                            dbc.Row(html.H4('-')),
                        ])
                    )
                ])
            ]),
            dcc.Interval(id='up', interval=10000, n_intervals=0),
        ], sm=12)
    ])
], fluid=True)
app2 = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], server=cam, url_base_pathname="/cartoes/")
app2.layout = html.Div(cartoes)


@app2.callback(
    Output('invs0', 'children'),
    [
        Input('up-inv-0', 'n_intervals')
    ]
)
def up_inv0(i):
    return inv('orindiuva', 4, [4, 1, 3, 2])


@app2.callback(
    Output('invs1', 'children'),
    [
        Input('up-inv-1', 'n_intervals')
    ]
)
def up_inv1(i):
    return inv('elias_fausto', 4, [1, 2, 3, 4])


@app2.callback(
    Output('invs2', 'children'),
    [
        Input('up-inv-2', 'n_intervals')
    ]
)
def up_inv2(i):
    return inv('monte_alto', 4, [157, 257, 357, 457])


@app2.callback(
    Output('invs3', 'children'),
    [
        Input('up-inv-3', 'n_intervals')
    ]
)
def up_inv3(i):
    return inv('paraguacu_paulista', 8, None)


@app2.callback(
    Output('ta0', 'children'),
    [
        Input('up-ta-0', 'n_intervals')
    ]
)
def up_ta0(i):
    return cm('taOR')


@app2.callback(
    Output('ta1', 'children'),
    [
        Input('up-ta-1', 'n_intervals')
    ]
)
def up_ta1(i):
    return cm('taEF')


@app2.callback(
    Output('ta2', 'children'),
    [
        Input('up-ta-2', 'n_intervals')
    ]
)
def up_ta2(i):
    return cm('taMA')


@app2.callback(
    Output('ta3', 'children'),
    [
        Input('up-ta-3', 'n_intervals')
    ]
)
def up_ta3(i):
    return cm('taPP')


@app2.callback(
    Output('isi0', 'children'),
    [
        Input('up-isi-0', 'n_intervals')
    ]
)
def up_isi0(i):
    return cm('isi1')


@app2.callback(
    Output('isi1', 'children'),
    [
        Input('up-isi-1', 'n_intervals')
    ]
)
def up_isi1(i):
    return cm('isi2')


@app2.callback(
    Output('isi2', 'children'),
    [
        Input('up-isi-2', 'n_intervals')
    ]
)
def up_isi2(i):
    return cm('isi3')


@app2.callback(
    Output('isi3', 'children'),
    [
        Input('up-isi-3', 'n_intervals')
    ]
)
def up_isi3(i):
    return cm('isi4')


@app2.callback(
    Output('mge0', 'children'),
    [
        Input('up-mge-0', 'n_intervals')
    ]
)
def up_mge0(i):
    return cm('PotOR')


@app2.callback(
    Output('mge1', 'children'),
    [
        Input('up-mge-1', 'n_intervals')
    ]
)
def up_mge1(i):
    return cm('PotEF')


@app2.callback(
    Output('mge2', 'children'),
    [
        Input('up-mge-2', 'n_intervals')
    ]
)
def up_mge2(i):
    return cm('PotMA')


@app2.callback(
    Output('mge3', 'children'),
    [
        Input('up-mge-3', 'n_intervals')
    ]
)
def up_mge3(i):
    return cm('PotPP')


@app2.callback(
    Output('idgt0', 'children'),
    Output('idgt0', 'style'),
    Output('red0', 'style'),

    [
        Input('up-idgt-0', 'n_intervals')
    ]
)
def up_idgt0(i):
    return IDGT_func2(databaseor, query_o)


@app2.callback(
    Output('idgt1', 'children'),
    Output('idgt1', 'style'),
    Output('red1', 'style'),
    [
        Input('up-idgt-1', 'n_intervals')
    ]
)
def up_idgt1(i):
    return IDGT_func2(databaseef, query)


@app2.callback(
    Output('idgt2', 'children'),
    Output('idgt2', 'style'),
    Output('red2', 'style'),
    [
        Input('up-idgt-2', 'n_intervals')
    ]
)
def up_idgt2(i):
    return IDGT_func2(databasema, query)


@app2.callback(
    Output('idgt3', 'children'),
    Output('idgt3', 'style'),
    Output('red3', 'style'),
    [
        Input('up-idgt-3', 'n_intervals')
    ]
)
def up_idgt3(i):
    return IDGT_func2(databasepp, query_pp)


@app2.callback(
    Output('DATA', 'children'),
    Input('data-itvl', 'n_intervals')
)
def up_data(itvl):
    return datetime.now().strftime("%H:%M:%S")


# SELECT TOP 1 ((MGE_ENER / 1200) * (1000 / PI_ENER)) * 100 FROM PFM2022 ORDER BY E3TimeStamp DESC
# SELECT TOP 1 ((MGE_ENER / 1200) * (1000 / PI_ENER)) * 100 FROM Estatisticos ORDER BY E3TimeStamp DESC

"""
=====================================================================================================
                                    FIM DO DASHBOARD DOS CARTÕES
====================================================================================================
"""

"""
=====================================================================================================
                                COMEÇO DO DASHBOARD DOS GRÁFICOS
=====================================================================================================
"""
from dash import Dash, html, dcc, Input, Output
from datetime import datetime
from sqlalchemy import create_engine
import pymssql
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

# navbar = dbc.NavbarSimple(
#     children=[
#         dbc.NavItem([html.Img(src='assets/sabesp.png', className='sabesp')]),
#         dbc.NavItem(
#             [html.Img(src='assets/CAPUA-ENGENHARIA.webp', className='logo'
#                       )]),
#         dbc.NavItem(html.H4('OVERVIEW', className='options')),
#         dbc.NavItem(dbc.NavLink("Mapa", href="http://187.95.20.103:8052/"), className='options2'),
#         dbc.NavItem(dbc.NavLink("Cartões", href="http://187.95.20.103:8052/cartoes"), className='options3'),
#
#         dbc.NavItem([
#             dbc.Row([
#                 dbc.Col([
#                     dbc.Card(
#                         dbc.CardBody([
#                             html.Span(datetime.now().strftime("%H:%M:%S"), className="hora", id="DATA"),
#                             dcc.Interval(id='data-itvl', interval=1000, n_intervals=0)
#                         ])
#                         , className="card_hora"),
#                 ]),
#             ])
#         ])
#
#     ],
#     color="dark",
#     dark=True,
#     fluid=True,
# )

navbar = dbc.NavbarSimple(
    children=[
        dbc.Row(
            [
                dbc.Col(html.Img(src='assets/sabesp.png', className='sabesp'), width="auto"),
                dbc.Col(html.Img(src='assets/CAPUA-ENGENHARIA.webp', className='logo'), width="auto"),
                dbc.Col(html.H4('MAPA', className='options'), width="auto"),
                dbc.Col(id='carregando2', width="auto"),
                dbc.Col(dbc.NavLink("Mapa", href="http://187.95.20.103:8052/", className="options2"),
                        width="auto"),
                dbc.Col(dbc.NavLink("Cartões", href='http://187.95.20.103:8052/cartoes', className='options3'),
                        width="auto"),
                dbc.Col(
                    dbc.NavItem([
                        dbc.Row(
                            daq.BooleanSwitch(
                                id='automatico',
                                on=True,
                                color="#008080"
                            ), className="toggle"),
                        dbc.Row(html.H6("AUTO", className="auto")),
                    ]),
                    width="auto"
                ),
                dbc.Col(
                    dcc.Interval(id='time', interval=1000, n_intervals=0),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Span(datetime.now().strftime("%H:%M:%S"), className="hora", id="DATA")
                        ], className='lidata')
                    ], className="card_hora"),
                    width="auto"
                ),
            ],
            align="center",
            className='g-0',
            style={"flex-wrap": "nowrap"}
        )
    ],
    color="light",
    dark=False,
    fluid=True,
    className='nav'
)

graficos = dbc.Row(dbc.Col(dbc.Container([
    dbc.Row(dbc.Col(navbar, sm=12)),

    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        html.H3('Orindiúva')
                    ]),
                    dbc.Row([
                        dcc.Graph(figure=muda_usina("orindiuva"), id='IrPt-O', style=dict(height='35vh')),
                        dcc.Interval(interval=10000, id='i-IP-O', n_intervals=0)
                    ]),
                ])
                , style={'margin-top': '20px'})

        ], sm=6),
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        html.H3('Elias Fausto')
                    ]),
                    dbc.Row([
                        dcc.Graph(figure=muda_usina("elias_fausto"), id='IrPt-EF', style=dict(height='35vh')),
                        dcc.Interval(interval=10000, id='i-IP-EF', n_intervals=0)
                    ]),
                ])
                , style={'margin-top': '20px'})
        ], sm=6),
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        html.H3('Paraguaçu Paulista')
                    ]),
                    dbc.Row([
                        dcc.Graph(figure=muda_usina("paraguacu_paulista"), id='IrPt-PP', style=dict(height='35vh')),
                        dcc.Interval(interval=10000, id='i-IP-PP', n_intervals=0)
                    ]),
                ])
                , style={'margin-top': '20px'})
        ], sm=6),
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        html.H3('Monte Alto')
                    ]),
                    dbc.Row([
                        dcc.Graph(figure=muda_usina("monte_alto"), id='IrPt-MA', style=dict(height='35vh')),
                        dcc.Interval(interval=10000, id='i-IP-MA', n_intervals=0)
                    ]),
                ])
                , style={'margin-top': '20px'})
        ], sm=6),
    ]),
], fluid=True)
    , sm=12))

app3 = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], server=cam, url_base_pathname="/graficos/")
app3.layout = html.Div(graficos)


@app3.callback(
    Output('IrPt-MA', 'figure'),
    [
        Input('i-IP-MA', 'n_intervals')
    ]
)
def update_MA(i):
    return muda_usina("monte_alto", True)


@app3.callback(
    Output('IrPt-PP', 'figure'),
    [
        Input('i-IP-PP', 'n_intervals')
    ]
)
def update_PP(i):
    return muda_usina("paraguacu_paulista", True)


@app3.callback(
    Output('IrPt-O', 'figure'),
    [
        Input('i-IP-O', 'n_intervals')
    ]
)
def update_Or(i):
    return muda_usina("orindiuva", True)


@app3.callback(
    Output('IrPt-EF', 'figure'),
    [
        Input('i-IP-EF', 'n_intervals')
    ]
)
def update_EF(i):
    return muda_usina("elias_fausto", True)


@app3.callback(
    Output('DATA', 'children'),
    Input('data-itvl', 'n_intervals')
)
def up_data(itvl):
    return datetime.now().strftime("%H:%M:%S")


"""
=====================================================================================================
                                    FIM DO DASHBOARD DOS GRÁFICOS
====================================================================================================
"""

"""
=====================================================================================================
                                    COMEÇO DA TELA DE LOGIN
=====================================================================================================
"""
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc

# Inicializando a aplicação Dash e aplicando o tema SPACELAB
from dash import Output, Input, State
from dash.exceptions import PreventUpdate
import ssl

cert = r'C:\Users\G4S\joshua_teste\pages\cert.pem'
key = r'C:\Users\G4S\joshua_teste\pages\key.pem'

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(certfile=cert, keyfile=key)

"""
==================================================================================================
                                        Iframe
==================================================================================================
"""

VALID_USERNAME_PASSWORD_PAIRS = {
    "Capua": "Capua@123"
}

auth2 = dash_auth.BasicAuth(
    app2,
    VALID_USERNAME_PASSWORD_PAIRS
)

auth3 = dash_auth.BasicAuth(
    app3,
    VALID_USERNAME_PASSWORD_PAIRS
)

auth4 = dash_auth.BasicAuth(
    app5,
    VALID_USERNAME_PASSWORD_PAIRS
)


@app5.callback(
    Output('p-ish', 'children'),
    Output('p-isi', 'children'),
    Output('p-ta', 'children'),
    Output('p-tp', 'children'),
    [
        Input('it-ish', 'n_intervals'),
        Input('MAP', 'clickData'),
        Input("automatico", "value")
    ]
)
def up_modbus(i, click, val):
    #
    df = pd.read_csv('../files/usinas.csv')
    ids = [usina for usina in df['id']]
    usinas = [usina for usina in df['nome']]
    #

    try:
        if click['points'][0]['location'] == ids[0]:
            return muda_usina_cm(usinas[0], [223, 225, 227, 235])
        elif click['points'][0]['location'] == ids[1]:
            return muda_usina_cm(usinas[1], [1, 3, 5, 9])
        elif click['points'][0]['location'] == ids[2]:
            return muda_usina_cm(usinas[2], [237, 223, 225, 233])
        elif click['points'][0]['location'] == ids[3]:
            return muda_usina_cm(usinas[3], [1, 3, 5, 9])
        elif click['points'][0]['location'] == ids[4]:
            return muda_usina_cm(usinas[4], [1, 3, 5, 9])
        # elif click['points'][0]['location'] == ids[5]:
        #     return muda_usina(usinas[5])
        else:
            raise PreventUpdate
    except TypeError:
        return muda_usina_cm(usinas[2], [237, 223, 225, 233])


@app5.callback(
    Output('inv1', 'children'),
    Output('inv2', 'children'),
    Output('inv3', 'children'),
    Output('inv4', 'children'),
    [
        Input('it-inv4', 'n_intervals'),
        Input('MAP', 'clickData'),
        Input("automatico", "value")
    ]
)
def atualiza_inv(intervalo, click, val):
    df = pd.read_csv('../files/usinas.csv')
    ids = [usina for usina in df['id']]
    usinas = [usina for usina in df['nome']]
    print(f"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   {click}")
    try:
        if click['points'][0]['location'] == ids[0]:
            return mostra_estado(usinas[0], [1, 2, 3, 4])
        elif click['points'][0]['location'] == ids[1]:
            return mostra_estado(usinas[1], [157, 257, 357, 457])
        elif click['points'][0]['location'] == ids[2]:
            return mostra_estado(usinas[2], [4, 1, 3, 2])
        elif click['points'][0]['location'] == ids[3]:
            return mostra_estado(usinas[3], [157, 257, 357, 457])
        elif click['points'][0]['location'] == ids[3]:
            return mostra_estado(usinas[4], [157, 257, 357, 457])
        else:
            raise PreventUpdate
    except TypeError:
        return mostra_estado(usinas[2], [4, 1, 3, 2])


@app5.callback(
    Output('nameusina', 'children'),
    [
        Input('MAP', 'clickData'),
        Input("automatico", "value")
    ]
)
def nameusina(click, val):
    # csv_mapa = pd.read_csv('data_geo_ft_teste2.csv', sep=',')
    csv_usina = pd.read_csv('../files/usinas.csv')
    try:
        usinas = [usina for usina in csv_usina['id']]
        print(click['points'][0])
        print(usinas[3])
        if click['points'][0]['location'] == usinas[3]:
            return 'Paraguaçu Paulista'
        elif click['points'][0]['location'] == usinas[2]:
            return 'Orindiúva'
        elif click['points'][0]['location'] == usinas[0]:
            return 'Elias Fausto'
        elif click['points'][0]['location'] == usinas[1]:
            return 'Monte Alto'
        elif click['points'][0]['location'] == usinas[4]:
            return 'Suzano'
        else:
            raise PreventUpdate
    except TypeError:
        return 'Orindiúva'


@app5.callback(
    Output('PUxISI', 'figure'),
    [
        Input('i-p-g', 'n_intervals'),
        Input('MAP', 'clickData'),
        Input("automatico", "value")
    ]
)
def up_graph(i, click, val):
    dia3 = datetime.now()
    dia3 = dia3.strftime("%Y-%m-%d")
    dia3 = str(dia3)

    df = pd.read_csv('../files/usinas.csv')
    ids = [usina for usina in df['id']]
    usinas = [usina for usina in df['nome']]

    try:
        if click['points'][0]['location'] == ids[0]:
            return muda_usina(usinas[0])
        elif click['points'][0]['location'] == ids[1]:
            return muda_usina(usinas[1])
        elif click['points'][0]['location'] == ids[2]:
            return muda_usina(usinas[2])
        elif click['points'][0]['location'] == ids[3]:
            return muda_usina(usinas[3])
        elif click['points'][0]['location'] == ids[4]:
            return muda_usina(usinas[4])
        elif click['points'][0]['location'] == ids[5]:
            return muda_usina(usinas[5])
        else:
            raise PreventUpdate
    except TypeError:
        return muda_usina(usinas[2])


@app5.callback(
    Output('IDGT', 'figure'),
    [
        Input('it-idgt', 'n_intervals'),
        Input('MAP', 'clickData'),
        Input("automatico", "value")
    ]
)
def up_idgt(i, cli, val):
    df = pd.read_csv('../files/usinas.csv')
    ids = [usina for usina in df['id']]

    try:
        if cli['points'][0]['location'] == ids[0]:
            return IDGT_func(databaseef, query2)
        elif cli['points'][0]['location'] == ids[2]:
            return IDGT_func(databaseor, query_o)
        elif cli['points'][0]['location'] == ids[1]:
            return IDGT_func(databasema, query2)
        elif cli['points'][0]['location'] == ids[3]:
            return IDGT_func(databasepp, query_pp)
        elif cli['points'][0]['location'] == ids[4]:
            return IDGT_func(databasesu, query_su)
        else:
            raise PreventUpdate
    except TypeError:
        return IDGT_func(databaseor, query_o)


@app5.callback(
    Output('DATA', 'children'),
    [Input('time', "n_intervals")],
)
def DATA(DATA):
    return f"{datetime.now().strftime('%H:%M:%S')}"


@app5.callback(
    Output('cams', 'children'),
    [
        Input('MAP', 'clickData'),
        Input("automatico", "value")
    ]
)
def render_cam(clickdata, val):
    try:
        df = pd.read_csv('../files/usinas.csv')
        ids = [id for id in df['id'].values]
        usinas = [usina for usina in df['nome'].values]

        if clickdata['points'][0]['location'] == ids[0]:
            return up_camera('elias_fausto')
        if clickdata['points'][0]['location'] == ids[1]:
            return up_camera('monte_alto')
        if clickdata['points'][0]['location'] == ids[2]:
            return up_camera('orindiuva')
        if clickdata['points'][0]['location'] == ids[3]:
            return up_camera('paraguacu_paulista')
        if clickdata['points'][0]['location'] == ids[4]:
            return up_camera('suzano')
        else:
            raise PreventUpdate
    except TypeError:
        return up_camera('orindiuva')


PP = 'paraguacu-paulista'


@app5.callback(
    Output('div-invs', 'children'),
    [
        Input('MAP', 'clickData'),
        Input("automatico", "value")

    ]
)
def show_plus_invs(mapa, val):
    dia9 = datetime.now()
    dia9 = dia9.strftime("%Y-%m-%d")
    dia9 = str(dia9)
    df = pd.read_csv('../files/usinas.csv')
    ids = [id for id in df['id'].values]
    usinas = [usina for usina in df['nome'].values]

    try:
        if mapa['points'][0]['location'] == ids[3]:
            return dbc.Row([
                dbc.Col([
                    dcc.Loading([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[
                                html.Span('INV5: '),
                                html.Span(children=[statusinv(PP,557)],
                                          className='colorinv',
                                          id='inv5',
                                          style=dict(color='#9c9105' if not statusinv(PP,
                                              557) == "Gerando" else '#636efa'))],
                                className='rowinv'),
                            dcc.Interval(id='it-inv5', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv5-cor"),
                    ], type='default')
                ], sm=3),
                dbc.Col([
                    dcc.Loading([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[
                                html.Span('INV6: '),
                                html.Span(children=[statusinv(PP,657)],
                                          className='colorinv',
                                          id='inv6', style=dict(color='#9c9105' if not statusinv(
                                        PP,657) == "Gerando" else '#636efa'))],
                                className='rowinv'),
                            dcc.Interval(id='it-inv6', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv6-cor")
                    ], type='default')

                ], sm=3),
                dbc.Col([
                    dcc.Loading([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[html.Span('INV7: '),
                                             html.Span(children=[statusinv(PP,757)], className='colorinv',
                                                       id='inv7', style=dict(
                                                     color='#9c9105' if not statusinv(PP,
                                                         757) == "Gerando" else '#636efa'))],
                                   className='rowinv'), dcc.Interval(id='it-inv7', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv7-cor")
                    ], type='default')

                ], sm=3),
                dbc.Col([
                    dcc.Loading([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[html.Span('INV8: '),
                                             html.Span(children=[statusinv(PP,857)], className='colorinv',
                                                       id='inv8', style=dict(
                                                     color='#9c9105' if not statusinv(PP,
                                                         857) == "Gerando" else 'r#636efa'))],
                                   className='rowinv'), dcc.Interval(id='it-inv8', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv8-cor")
                    ], type='default')

                ], sm=3),

            ]),
        if mapa['points'][0]['location'] == ids[4]:
            return dbc.Row([
                dbc.Col([
                    dcc.Loading([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[
                                html.Span('INV5: '),
                                html.Span(children=[statusinv('suzano', 557)],
                                          className='colorinv',
                                          id='inv5su',
                                          style=dict(color='#9c9105' if not statusinv('suzano',
                                                                                      557) == "Gerando" else '#636efa'))],
                                className='rowinv'),
                            dcc.Interval(id='it-inv5su', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv5-corsu"),
                    ], type='default')
                ], sm=3),
                dbc.Col([
                    dcc.Loading([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[
                                html.Span('INV6: '),
                                html.Span(children=[statusinv('suzano', 657)],
                                          className='colorinv',
                                          id='inv6su', style=dict(color='#9c9105' if not statusinv('suzano',
                                                                                                   657) == "Gerando" else '#636efa'))],
                                className='rowinv'),
                            dcc.Interval(id='it-inv6su', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv6-corsu")
                    ], type='default')

                ], sm=3),
                dbc.Col([
                    dcc.Loading([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[html.Span('INV7: '),
                                             html.Span(children=[statusinv('suzano', 757)], className='colorinv',
                                                       id='inv7su', style=dict(
                                                     color='#9c9105' if not statusinv('suzano',
                                                                                      757) == "Gerando" else '#636efa'))],
                                   className='rowinv'), dcc.Interval(id='it-inv7su', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv7-corsu")
                    ], type='default')

                ], sm=3),
                dbc.Col([
                    dcc.Loading([
                        dbc.Card(dbc.CardBody([
                            html.P(children=[html.Span('INV8: '),
                                             html.Span(children=[statusinv('suazno', 857)], className='colorinv',
                                                       id='inv8su', style=dict(
                                                     color='#9c9105' if not statusinv('suzano',
                                                                                      857) == "Gerando" else 'r#636efa'))],
                                   className='rowinv'), dcc.Interval(id='it-inv8su', interval=5 * 60000)
                        ]), className='cardbodyinv', id="inv8-corsu")
                    ], type='default')

                ], sm=3),

            ]),
    except TypeError:
        return None


@app5.callback(
    Output('MAP', 'figure'),
    [
        Input('intervalmap', 'n_intervals')
    ]
)
def change_color_region_map(i):
    tem = [tem_falha('orindiuva', [4, 1, 3, 2]), tem_falha('elias_fausto', [1, 2, 3, 4]), tem_falha('monte_alto', None),
           tem_falha('paraguacu_paulista', None), tem_falha('suzano', None)]

    df = pd.read_excel(excel)  # replace with your own data source
    df_csv_ef = pd.read_csv(csv_ef)
    df_csv_ma = pd.read_csv(csv_ma)
    df_csv_or = pd.read_csv(csv_or)
    df_csv_pp = pd.read_csv(csv_pp)
    df_csv_su = pd.read_csv(csv_su)
    geojson = json.load(open(r"C:\Users\G4S\joshua_teste\files\sp_geo.json", "r", encoding='utf-8'))

    fig = go.Figure()

    fig.add_trace(go.Choroplethmapbox(z=df['value'],
                                      locations=df['id'],
                                      colorscale=colorscale,
                                      featureidkey="properties.id",
                                      below=True,
                                      geojson=geojson,
                                      hoverinfo='none',
                                      marker_line_width=0.1, marker_opacity=1,
                                      showscale=False))

    fig.add_trace(go.Choroplethmapbox(z=df_csv_or['value'],
                                      locations=df_csv_or['id'],
                                      colorscale=['red' if tem[0] else 'blue', 'blue' if not tem[0] else 'red'],
                                      featureidkey="properties.id",
                                      below=True,
                                      geojson=geojson,
                                      hoverinfo='none',
                                      marker_line_width=0.1, marker_opacity=1,
                                      showscale=False))

    fig.add_trace(go.Choroplethmapbox(z=df_csv_ef['value'],
                                      locations=df_csv_ef['id'],
                                      colorscale=['red' if tem[1] else 'blue', 'blue' if not tem[1] else 'red'],
                                      featureidkey="properties.id",
                                      below=True,
                                      geojson=geojson,
                                      hoverinfo='none',
                                      marker_line_width=0.1, marker_opacity=1,
                                      showscale=False))

    fig.add_trace(go.Choroplethmapbox(z=df_csv_ma['value'],
                                      locations=df_csv_ma['id'],
                                      colorscale=['red' if tem[2] else 'blue', 'blue' if not tem[2] else 'red'],
                                      featureidkey="properties.id",
                                      below=True,
                                      geojson=geojson,
                                      hoverinfo='none',
                                      marker_line_width=0.1, marker_opacity=1,
                                      showscale=False))

    fig.add_trace(go.Choroplethmapbox(z=df_csv_pp['value'],
                                      locations=df_csv_pp['id'],
                                      colorscale=['red' if tem[3] else 'blue', 'blue' if not tem[3] else 'red'],
                                      featureidkey="properties.id",
                                      below=True,
                                      geojson=geojson,
                                      hoverinfo='none',
                                      marker_line_width=0.1, marker_opacity=1,
                                      showscale=False))
    fig.add_trace(go.Choroplethmapbox(z=df_csv_su['value'],
                                      locations=df_csv_su['id'],
                                      colorscale=['red' if tem[4] else 'blue', 'blue' if not tem[4] else 'red'],
                                      featureidkey="properties.id",
                                      below=True,
                                      geojson=geojson,
                                      hoverinfo='none',
                                      marker_line_width=0.1, marker_opacity=1,
                                      showscale=False))

    fig.add_trace(go.Scattermapbox(
        lat=[-20.1795, -23.0435, -21.2616, -22.4193, -23.5420],
        lon=[-49.3487, -47.3743, -48.4966, -50.5922, -46.3110],
        marker={'color': 'black', 'opacity': 1, 'size': 1},
        mode='text+markers',
        showlegend=False,
        textposition='top center',
        hoverinfo='skip',
        text=[f"Orindiúva", 'Elias Fausto', 'Monte Alto', 'Paraguaçu Paulista', 'Suzano'],
        textfont=dict(color='black', size=17),
    ))

    fig.update_layout(height=990,
                      mapbox=dict(
                          center={"lat": -22.5, "lon": -48.58228565534156},
                          accesstoken=token,
                          zoom=6.13,
                          style="light",
                      ),
                      margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      )
    return fig


@app5.callback(
    Output('inv1', 'style'),
    Input('inv1', 'children'),
    Input('it-inv1', 'n_intervals'),
)
def cor_invs(c, i):
    if not c == "Funcionando" and not c == "Gerando":
        return dict(color="#9c9105")
    elif c in "Conexão instável":
        return None
    else:
        return dict(color="#636efa")


@app5.callback(
    Output('inv2', 'style'),
    Input('inv2', 'children'),
    Input('it-inv2', 'n_intervals'),
)
def cor_invs(c, i):
    if not c == "Funcionando" and not c == "Gerando":
        return dict(color="#9c9105")
    elif c in "Conexão instável":
        return None
    else:
        return dict(color="#636efa")


@app5.callback(
    Output('inv3', 'style'),
    Input('inv3', 'children'),
    Input('it-inv3', 'n_intervals'),
)
def cor_invs(c, i):
    if not c == "Funcionando" and not c == "Gerando":
        return dict(color="#9c9105")
    elif c in "Conexão instável":
        return None
    else:
        return dict(color="#636efa")


@app5.callback(
    Output('inv4', 'style'),
    Input('inv4', 'children'),
    Input('it-inv4', 'n_intervals'),
)
def cor_invs(c, i):
    if not c == "Funcionando" and not c == "Gerando":
        return dict(color="#9c9105")
    elif c in "Conexão instável":
        return None
    else:
        return dict(color="#636efa")


@app5.callback(Output("MAP", "clickData"),
               Input("MAP", "clickData"),
               Input("automatico", "on"),
               Input("change_auto", "n_intervals"))
def deixa_automatico(click, auto, intv):
    if auto:
        n = pd.read_csv(r"C:\Users\G4S\joshua_teste\files\n.csv")
        if n["n"].values[0] == 1:
            return ef_json
        if n["n"].values[0] == 2:
            return ma_json
        if n["n"].values[0] == 3:
            return or_json
        if n["n"].values[0] == 4:
            # pyautogui.press('f5')
            return pp_json
        if n["n"].values[0] == 5:
            return su_json
    else:
        return click


if __name__ == "__main__":
    cam.run(host="0.0.0.0", debug=True, port=8052)
