import os
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)

db = client["exo_data"]

collections = db.list_collection_names()
collections = sorted(collections, reverse=True)

st.title("Platforms Data")

selected_collection = st.selectbox("Available collections:", collections)

collection = db[selected_collection]

cursor = collection.distinct('data.0')

datas_unicas = sorted(cursor, reverse=True)

data_escolhida = st.selectbox('Available dates:', datas_unicas)

data = []

consulta = {'data.0': data_escolhida}
for documento in collection.find(consulta):
    if len(documento['data']) == 28:
        data.append(documento)
df = pd.DataFrame(data)

if '_id' in df.columns:
    df = df.drop('_id', axis=1)

client.close()

graphs = ['Depth', 'Temperature', 'Specific Conductance', 'Salinity', 'ODO, %Sat', 'ODO, mg/L', 'Turbidity', 'TSS', 'Wiper Position', 'Pressure', 'Depth, m', 'Voltage', 'Current', 'Top Mag', 'Top Float', 'Bottom Float', 'Bottom Mag', 'Sled State', 'Power Mode']

choose_graph = st.selectbox('Available graphs:', graphs)

# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

df_updated = pd.DataFrame(df['data'].tolist())
df_updated[0] = pd.to_datetime(df_updated[0] + ' ' + df_updated[1])
df_updated.drop(columns=[1], inplace=True)
df_updated[8] = pd.to_datetime(df_updated[8] + ' ' + df_updated[9], format='%Y-%m-%d %H%M%S', errors='coerce')
df_updated.drop(columns=[9], inplace=True)
df_updated.columns = range(df_updated.shape[1])

df_updated[1] = pd.to_numeric(df_updated[1], errors='coerce').fillna(-1).astype(float).astype(int)
df_updated[2] = pd.to_numeric(df_updated[2], errors='coerce').fillna(-1).astype(float).astype(int)

int_values = [20, 21, 22, 23, 24, 25]
for value in int_values:
    df_updated[value] = pd.to_numeric(df_updated[value], errors='coerce').fillna(-1).astype(int)

float_values = [3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
for value in float_values:
    df_updated[value] = pd.to_numeric(df_updated[value], errors='coerce').fillna(-1).astype(float)

# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

if choose_graph == 'Depth':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[1], mode='lines'))
    fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='depth')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Temperature':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[8], mode='lines'))
    fig.update_layout(title='Temperature', xaxis_title='Time [h]', yaxis_title='Temperature [°C]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Specific Conductance':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[9], mode='lines'))
    fig.update_layout(title='Specific Conductance', xaxis_title='Time [h]', yaxis_title='Specific Conductance [μS/cm]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Salinity':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[10], mode='lines'))
    fig.update_layout(title='Salinity', xaxis_title='Time [h]', yaxis_title='Salinity [PPT]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'ODO, %Sat':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[11], mode='lines'))
    fig.update_layout(title='Optical Dissolved Oxygen', xaxis_title='Time [h]', yaxis_title='ODO [%Sat]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'ODO, mg/L':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[12], mode='lines'))
    fig.update_layout(title='Optical Dissolved Oxygen', xaxis_title='Time [h]', yaxis_title='ODO [mg/L]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Turbidity':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[13], mode='lines'))
    fig.update_layout(title='Turbidity', xaxis_title='Time [h]', yaxis_title='Turbidity [FNU]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'TSS':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[14], mode='lines'))
    fig.update_layout(title='Total Suspended Solids', xaxis_title='Time [h]', yaxis_title='TSS [mg/L]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Wiper Position':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[15], mode='lines'))
    fig.update_layout(title='Wiper Position', xaxis_title='Time [h]', yaxis_title='Wiper Position [V]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Pressure':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[16], mode='lines'))
    fig.update_layout(title='Pressure', xaxis_title='Time [h]', yaxis_title='Pressure [psia]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Depth, m':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[17], mode='lines'))
    fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='Depth [m]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Voltage':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[18], mode='lines'))
    fig.update_layout(title='Voltage', xaxis_title='Time [h]', yaxis_title='Voltage [V]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Current':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[19], mode='lines'))
    fig.update_layout(title='Current', xaxis_title='Time [h]', yaxis_title='Current [mA]')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Top Mag':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[20], mode='lines'))
    fig.update_layout(title='Top Mag', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Top Float':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[21], mode='lines'))
    fig.update_layout(title='Top Float', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Bottom Float':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[22], mode='lines'))
    fig.update_layout(title='Bottom Float', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Bottom Mag':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[23], mode='lines'))
    fig.update_layout(title='Bottom Mag', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Sled State':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[24], mode='lines'))
    fig.update_layout(title='Sled State', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif choose_graph == 'Power Mode':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[25], mode='lines'))
    fig.update_layout(title='Power Mode', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)