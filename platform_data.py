import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.graph_objects as go

#/Users/anasophia/Library/CloudStorage/OneDrive-Pessoal/Trabalho/FIU/"Jupyter Lab"

uri = 'mongodb+srv://fixedplatform01:dbFixedPlatformPwd01@cluster0.wzn4u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(uri, tlsAllowInvalidCertificates=True)  # Substitua pela URI correta, se necessário

# Selecionar o banco de dados
db = client["exo_data"]

# Listar coleções disponíveis
collections = db.list_collection_names()
collections = sorted(collections, reverse=True)

# Interface no Streamlit
st.title("Platforms Data")
    #st.write("Dados carregados do MongoDB:")

selected_collection = st.selectbox("Available collections:", collections)


collection = db[selected_collection]

cursor = collection.distinct('data.0')

datas_unicas = sorted(cursor, reverse=True)

data_escolhida = st.selectbox('Available dates:', datas_unicas)

data = []

consulta = {'data.0': data_escolhida}
for documento in collection.find(consulta):
    if len(documento['data']) >= 27 and len(documento['data']) <= 28:
        data.append(documento)
df = pd.DataFrame(data)

if '_id' in df.columns:
    df = df.drop('_id', axis=1)

client.close()

graphs = ['Depth', 'Voltage', 'Current', 'Top Mag', 'Top Float', 'Bottom Float', 'Bottom Mag', 'Sled State', 'Power Mode']

choose_graph = st.selectbox('Available graphs:', graphs)

# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

df_updated = pd.DataFrame(df['data'].tolist())
df_updated[0] = pd.to_datetime(df_updated[0] + ' ' + df_updated[1])
df_updated.drop(columns=[1], inplace=True)
df_updated[2] = df_updated[2].astype(float).astype(int)
df_updated[3] = df_updated[3].astype(float).astype(int)
df_updated[4] = df_updated[4].astype(float)
df_updated[5] = df_updated[5].astype(float)
df_updated[6] = df_updated[6].astype(float)
df_updated[7] = df_updated[7].astype(float)
df_updated[8] = pd.to_datetime(df_updated[8] + ' ' + df_updated[9], format='%Y-%m-%d %H%M%S', errors='coerce')
df_updated.drop(columns=[9], inplace=True)
df_updated.columns = range(df_updated.shape[1])
df_updated[8] = df_updated[8].astype(float)
df_updated[9] = df_updated[9].astype(float)
df_updated[10] = df_updated[10].astype(float)
df_updated[11] = df_updated[11].astype(float)
df_updated[12] = pd.to_numeric(df_updated[12], errors='coerce')
df_updated[12] = df_updated[12].astype(float)
df_updated[13] = df_updated[13].astype(float)
df_updated[14] = df_updated[14].astype(float)
df_updated[15] = df_updated[15].astype(float)
df_updated[16] = pd.to_numeric(df_updated[16], errors='coerce')
df_updated[16] = df_updated[16].astype(float)
df_updated[17] = pd.to_numeric(df_updated[17], errors='coerce')
df_updated[17] = df_updated[17].astype(float)
df_updated[18] = df_updated[18].astype(float)
df_updated[19] = df_updated[19].astype(float)
df_updated[20] = pd.to_numeric(df_updated[20], errors='coerce').fillna(2).astype(int)
df_updated[21] = pd.to_numeric(df_updated[21], errors='coerce').fillna(2).astype(int)
df_updated[22] = pd.to_numeric(df_updated[22], errors='coerce').fillna(2).astype(int)
df_updated[23] = pd.to_numeric(df_updated[23], errors='coerce').fillna(2).astype(int)
df_updated[24] = pd.to_numeric(df_updated[24], errors='coerce').fillna(2).astype(int)
df_updated[25] = pd.to_numeric(df_updated[25], errors='coerce').fillna(-1).astype(int)

if choose_graph == 'Depth':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_updated[0], y=df_updated[1], mode='lines'))
    fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='depth')
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

