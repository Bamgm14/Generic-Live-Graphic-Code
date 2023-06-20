#My Code
from sr510 import SR510
from tenma import TENMA_72_7210
from Keithley6487 import Keithley6487
from experiment import Experiment
from pymeasure.instruments.keithley import Keithley2450, Keithley2400
#External
import dash
from dash import html, dcc, Output, Input, ctx, State, MATCH
from flask import send_from_directory, Flask
import pyvisa
import plotly.graph_objs as go
import numpy as np
import time
import os
import serial.tools.list_ports as ports
rst = False
#Initialized
modes_sensitivity = {
    1e-8, 2e-8, 5e-8,
    1e-7, 2e-7, 5e-7,
    1e-6, 2e-6, 5e-6, 
    1e-5, 2e-5, 5e-5, 
    1e-4, 2e-4, 5e-4,
    1e-3, 2e-3, 5e-3,
    1e-2, 2e-2, 5e-2,
    1e-1, 2e-1, 5e-1,
}
modes_pre_time = {
    1e-3, 3e-3,
    1e-2, 3e-2,
    1e-1, 3e-1,
    1, 3,
    10, 30,
    100
}
modes_post_time = {
    "None",
    1e-1,
    1
}
server = Flask(__name__)
RM = pyvisa.ResourceManager()
savepath = 'data'
gate = None
source_drain = None
laser_power = None
lockin = None
experiment = None
graphing = {"source-drain": 1,
            "gate-potential":3,
            "time":0,
            "lockin-output":2}
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
if not os.path.exists(savepath):
    os.makedirs(savepath)
@server.route(f'/download/<path:path>')
def download(path):
    print("Downloading...")
    return send_from_directory(savepath, path, as_attachment=True)
app = dash.Dash(server=server, update_title="Running...", external_stylesheets=external_stylesheets)  # remove "Updating..." from title
app.layout = html.Div(
    [
        html.Center(
            html.H1("Measurements"),
        ),
        html.Div(id = 'output-div', children = [
                html.Center(
                    html.H2("Graphs"),
                ),
                html.Div(id = 'graph-div', style = {
                                           'display': 'grid', 
                                           'grid-template-columns': 'repeat(auto-fit, minmax(300px, 1fr))',
                                           'grid-gap': '20px',
                                           'margin': '20px'
                                            }
                ),
                dcc.Interval(id='interval', interval=750, disabled=True),    
            ]
        ),
        html.Div(id = 'input-div', children = [
                    html.Div(style = {'width': '30%', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto', 'text-align': 'center'}, children = [
                        html.Center(
                            html.Label('Port for Lock-In Amplifier (SR510): '),
                        ),
                        dcc.Dropdown(
                            options = [{"label": str(p), "value": p.name} for p in ports.comports()], id='lockin', searchable = False,
                        ),
                        html.Center(
                            html.Label('Port for Power Supply (TENMA): '),
                        ),
                        dcc.Dropdown(
                            options = [{"label": str(p), "value": p.name} for p in ports.comports()], id='laser-source', searchable = False,
                        ),
                        html.Center(
                            html.Label('Port for Keithley6487: '),
                        ),
                        dcc.Dropdown(
                            options = [{"label": str(p), "value": p.name} for p in ports.comports()], id='power-source', searchable = False,
                        ),
                        html.Center(
                            html.Label('Port for Power Supply (Keithley): '),
                        ),
                        dcc.Dropdown(
                            options = [{"label": str(p), "value": p} for p in RM.list_resources()], id='gate-source', searchable = False,
                        ),
                        html.Center(
                            html.Label('Laser Wavelength: '),
                        ),
                        dcc.Dropdown(
                            options = [{"label": "Red (650 nm)", "value": f"{650 * 10 ** (-9)}"},
                                       {"label": "Green (520 nm)", "value": f"{520 * 10 ** (-9)}"}], id='wavelength', searchable = False,
                        ),
                        html.Button('Setup', id='setup-button',value='Setup', disabled=False),
                        html.Div(id='setup-complete', style={'display': 'none'}, children = [
                            html.Center(
                                html.Label('Laser Voltage (V): '),
                            ),
                            dcc.Slider(id='laser-voltage-slider', min=0, max=10, step=0.01, value=0, marks = None, tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Center(
                                html.Label('Gate Voltage (V): '),
                            ),
                            dcc.Slider(id='gate-voltage-slider', min=0, max=10, step=0.0001, value=0, marks = None, tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Center(
                                html.Label('Source-Drain Voltage (V): '),
                            ),
                            dcc.Slider(id='source-voltage-slider', min=-10, max=10, step=0.0001, value=0, marks = None, tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            dcc.Loading(id='loading3', children=[
                                html.Button('AutoPhase', id='autophase-button',value='AutoPhase'),
                                html.Button('FastAutoPhase', id='fast-autophase-button',value='AutoPhase'),
                            ], type = 'default'),
                            html.Center(
                                html.Label('Sensitivity (V): '),
                            ),
                            dcc.Dropdown(id = 'sensitivity',
                                options = [{"label": str(x), "value": x} for x in modes_sensitivity],
                            value = None,),
                            html.P(id='autophase-output', style={'display': 'none'}),
                            dcc.Loading(id='loading1', children=[
                                html.Button('Start', id='start-button',value='Start', disabled=True),
                            ], type = 'default'),
                            html.Br(),
                            html.Button('Make File', id='make-file-button',value='file', disabled=True),
                            dcc.Loading(id='loading2', children=[
                                html.A('', id='download-link', download="rawdata.csv", href="/download/"),
                            ], type='default'),
                            html.Br(),
                        ]),
                            html.Center(
                            html.Label('Create Graph: '),
                        ),
                        html.Div(children = [
                            html.Div(style = {'width': '47.5%', 'text-align': 'center', 'display': 'inline-block'}, children = [
                                html.Center(
                                    html.Label('X-AXIS'),
                                ),
                                dcc.Dropdown(
                                    options = [{"label": "Source Drain", "value": "source-drain"},
                                               {"label": "Gate Potential", "value": f"gate-potential"},
                                               {"label": "Time Counter", "value": f"time"},
                                               {"label": "Lockin Output", "value": "lockin-output"}], id='x-axis', searchable = False,
                                ),
                            ]),
                            html.Label("", style = {'width': '5%', 'text-align': 'center', 'display': 'inline-block'}),
                            html.Div(style = {'width': '47.5%', 'text-align': 'center', 'display': 'inline-block'}, children = [
                                html.Center(
                                    html.Label('Y-AXIS'),
                                ),
                                dcc.Dropdown(
                                    options = [{"label": "Source Drain", "value": "source-drain"},
                                               {"label": "Gate Potential", "value": f"gate-potential"},
                                               {"label": "Time Counter", "value": f"time"},
                                               {"label": "Lockin Output", "value": "lockin-output"}], id='y-axis', searchable = False,
                                ),
                            ]),
                            html.Br(),
                            html.Button('Create Graph',id = 'create-graph'),
                        ]),
                    ]
                ),
            ]
        ),
        html.Button("Reset", id="reset-button", value="Reset", disabled=False),
    ]
)

@app.callback(
    Output('start-button', 'children'), Output('start-button', 'value') ,Output('interval', 'disabled'), Output('make-file-button', 'disabled'),
    Input('start-button', 'n_clicks'), Input('start-button', 'value'),
    prevent_initial_call=True
)
def start_n_stop(n_clicks, value):
    try:
        #print(value)
        if value == 'Start':
            experiment.start()
            return ("Stop", "Stop", False, True)
        if value == 'Stop':
            experiment.stop()
            #experiment.collected_to_df()
            return ("Start", "Start", True, False)
    except Exception as e:
        print(f"Error: {e}")
        return ("Start", "Start", True, False)

@app.callback(
    Output('sensitivity', 'value', allow_duplicate=True),
    Input('sensitivity', 'value'),
    prevent_initial_call=True
)
def sensitivity(value):
    try:
        lockin.sensitivity = value
        return lockin.sensitivity
    except Exception as e:
        print(f"Error: {e}")
        return lockin.sensitivity


@app.callback(Output('start-button', 'disabled'), Output('setup-button', 'disabled'), Output('setup-complete', 'style'), 
              Output('sensitivity', 'value', allow_duplicate=True), Output('gate-voltage-slider', 'value', allow_duplicate=True), 
              Output('source-voltage-slider', 'value', allow_duplicate=True), Output('laser-voltage-slider', 'value', allow_duplicate=True),
              State('lockin', 'value'), State('power-source', 'value'), State('gate-source', 'value'), State('laser-source', 'value'), State('wavelength', 'value'),
              Input('setup-button', 'n_clicks'),
              prevent_initial_call=True)

def validate(value1, value2, value3, value4, wavelength, n_clicks):
    global lockin, laser_power, gate, source_drain, experiment
    try:
        print(value1)
        lockin = SR510(value1)
        print(value2)
        source_drain = Keithley6487(value2)
        source_drain.enable_source()
        print(value3)
        gate = None
        #gate = Keithley2450(value3)
        #gate.enable_source() 
        print(value4)
        laser_power = TENMA_72_7210(value4)
        experiment = Experiment(lockin, laser_power, source_drain, gate, wavelength)
        #print("Setup Complete")
        #print(source_drain.set_voltage)
        #print(laser_power.set_voltage)
        return False, True, {}, lockin.sensitivity, 0, source_drain.set_voltage, laser_power.set_voltage
    except Exception as e:
        print(e)
        del lockin, gate, source_drain, experiment, laser_power
        lockin = None
        gate = None
        source_drain = None
        laser_power = None
        experiment = None
        return True, False, {'display': 'none'}, None, 0, 0, 0

@app.callback(Output({'type': 'graph', 'x': MATCH, 'y': MATCH}, 'extendData'),
              Input('interval', 'n_intervals'), State({'type': 'graph', 'x': MATCH, 'y': MATCH}, 'id'),
              prevent_initial_call=True)

def auto_update(_, id):
    global rst
    try:
        data = experiment.get_data()
        if rst:
            return dict(x=[[]], y=[[]]), [0], None
        if data == []:
            return dict(x=[[]], y=[[]]), [0], None
    except Exception as e:
        print(e)
        return dict(x=[[]], y=[[]]), [0], None
    x = data[-1][graphing[id['x']]]
    y = data[-1][graphing[id['y']]]
    #print(data[-1])
    #count += 1
    return (dict(x=[[x]], y=[[y]]), [0], None)


@app.callback(Output('autophase-output', 'children', allow_duplicate=True), Output('autophase-output', 'style', allow_duplicate=True),
              Input('autophase-button', 'n_clicks'), 
              prevent_initial_call=True)

def autophase(n_clicks):
    try:
        phase = lockin.autophase()
        return f'Autophase successful: {phase}°', {'display': 'block'}
    except Exception as e:
        return f'Autophase failed: {e}', {'display': 'block'}

@app.callback(Output('autophase-output', 'children', allow_duplicate=True), Output('autophase-output', 'style', allow_duplicate=True),
              Input('fast-autophase-button', 'n_clicks'), 
              prevent_initial_call=True)

def fast_autophase(n_clicks):
    try:
        phase = lockin.fast_autophase()
        return f'Fast Autophase successful: {phase}°', {'display': 'block'}
    except Exception as e:
        return f'Fast Autophase failed: {e}', {'display': 'block'}

@app.callback(
    Output('graph-div', 'children'),
    [Input('create-graph', 'n_clicks')],
    [State('graph-div', 'children'), State('x-axis', 'value'), State('y-axis', 'value')]
)
def create_graph(_, children, x, y):
    children = children if children else []
    if not (x and y):
        return children
    children.append(dcc.Graph(
        id = {'type': 'graph', 'x': x, 'y': y},
        figure={
                'data': [
                    go.Scatter(
                        x=[],
                        y=[],
                        mode='lines+markers',
                        name=f'Graph {x} vs {y}'
                    )
                ],
                'layout': go.Layout(
                    title=f'Graph {x} vs {y}',
                    margin={'l': 40, 'b': 40, 't': 50, 'r': 10}
                )
            }
        )
    )
    return children
@app.callback(Output('download-link', 'href'), Output('download-link', 'children'),
              Input('make-file-button', 'n_clicks'),
              prevent_initial_call=True)
def make_file(n_clicks):
    try:
        #print(experiment.filename)
        experiment.write(savepath)
        a = 0
        #print(experiment.filename)
        while os.path.getsize(savepath + '/' + experiment.filename) - a > 0:
            time.sleep(1)
            a = os.path.getsize(savepath + '/' + experiment.filename)
        return f"/download/{experiment.filename}", experiment.filename
    except Exception as e:
        print(f"Error: {e}")
        return "", ""

@app.callback(Output('source-voltage-slider', 'value'),
              Input('source-voltage-slider', 'value'), 
              prevent_initial_call=True)
def source_voltage_slider(value):
    global source_drain
    try:
        #print(value)
        source_drain.set_voltage  = value
        return source_drain.set_voltage
    except Exception as e:
        print(e)
        return 0

@app.callback(Output('gate-voltage-slider', 'value'),
              Input('gate-voltage-slider', 'value'), 
              prevent_initial_call=True)
def gate_voltage_slider(value):
    global gate
    try:
        #print(value)
        gate.source_voltage  = value
        return gate.source_voltage
    except Exception as e:
        print(e)
        return 0

@app.callback(Output('laser-voltage-slider', 'value'),
              Input('laser-voltage-slider', 'value'), 
              prevent_initial_call=True)
def laser_voltage_slider(value):
    global laser_power
    try:
        #print(value)
        laser_power.set_voltage = value
        return laser_power.set_voltage
    except Exception as e:
        print(e)
        return 0

@app.callback(Output('setup-button', 'disabled', allow_duplicate=True), Output('start-button', 'disabled', allow_duplicate=True), Output('graph-div', 'children', allow_duplicate=True),
              Input('reset-button', 'n_clicks'), State('graph-div', 'children'),
              prevent_initial_call=True)
def reset(value, children):
    global lockin, gate, source_drain, experiment, rst, laser_power
    del lockin, gate, source_drain, experiment, laser_power
    for x in range(len(children)):
        #print(children[x])
        children[x]['props']['figure']['data'][0]['x'] = []
        children[x]['props']['figure']['data'][0]['y'] = []
    rst = True
    return False, True, children
if __name__ == "__main__": 
    app.run_server(debug=True)