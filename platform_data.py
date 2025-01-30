import os
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import pydeck as pdk

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)

db = client["FDEP_Project"]

collection = db['platforms_data']

st.title("Platforms Data")

platforms = collection.distinct('metadata.platform')

selected_collection = st.selectbox("Available collections:", platforms)

query = {'metadata.platform': selected_collection}

dates = collection.find(query).distinct('datetime')

dates = sorted(set(dt.split(" ")[0] for dt in dates), reverse=True)

selected_date = st.selectbox('Available dates:', dates)

query = {
    'metadata.platform': selected_collection,
    'datetime': {'$regex': selected_date}
}

data = list(collection.find(query))

df = pd.json_normalize(data)

if '_id' in df.columns:
    df = df.drop('_id', axis=1)

df['datetime'] = pd.to_datetime(df['datetime'])

client.close()

graphs = ['Depth', 'Temperature', 'Specific Conductance', 'Salinity', 'ODO, %Sat', 'ODO, mg/L', 'Turbidity', 'TSS', 'Wiper Position', 'Pressure', 'Depth, m', 'Voltage', 'Current', 'Top Mag', 'Top Float', 'Bottom Float', 'Bottom Mag', 'Sled State', 'Power Mode']

selected_graph = st.selectbox('Available graphs:', graphs)

# # _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

if selected_graph == 'Depth':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.depth'], mode='lines'))
    fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='depth')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Temperature':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.1'], mode='lines'))
    fig.update_layout(title='Temperature', xaxis_title='Time [h]', yaxis_title='Temperature [°C]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Specific Conductance':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.7'], mode='lines'))
    fig.update_layout(title='Specific Conductance', xaxis_title='Time [h]', yaxis_title='Specific Conductance [μS/cm]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Salinity':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.12'], mode='lines'))
    fig.update_layout(title='Salinity', xaxis_title='Time [h]', yaxis_title='Salinity [PPT]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'ODO, %Sat':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.211'], mode='lines'))
    fig.update_layout(title='Optical Dissolved Oxygen', xaxis_title='Time [h]', yaxis_title='ODO [%Sat]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'ODO, mg/L':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.212'], mode='lines'))
    fig.update_layout(title='Optical Dissolved Oxygen', xaxis_title='Time [h]', yaxis_title='ODO [mg/L]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Turbidity':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.223'], mode='lines'))
    fig.update_layout(title='Turbidity', xaxis_title='Time [h]', yaxis_title='Turbidity [FNU]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'TSS':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.190'], mode='lines'))
    fig.update_layout(title='Total Suspended Solids', xaxis_title='Time [h]', yaxis_title='TSS [mg/L]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Wiper Position':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.229'], mode='lines'))
    fig.update_layout(title='Wiper Position', xaxis_title='Time [h]', yaxis_title='Wiper Position [V]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Pressure':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.20'], mode='lines'))
    fig.update_layout(title='Pressure', xaxis_title='Time [h]', yaxis_title='Pressure [psia]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Depth, m':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.22'], mode='lines'))
    fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='Depth [m]', yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Voltage':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.voltage'], mode='lines'))
    fig.update_layout(title='Voltage', xaxis_title='Time [h]', yaxis_title='Voltage [V]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Current':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.current'], mode='lines'))
    fig.update_layout(title='Current', xaxis_title='Time [h]', yaxis_title='Current [mA]')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Top Mag':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.top mag'], mode='lines'))
    fig.update_layout(title='Top Mag', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Top Float':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.top float'], mode='lines'))
    fig.update_layout(title='Top Float', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Bottom Float':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.bottom float'], mode='lines'))
    fig.update_layout(title='Bottom Float', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Bottom Mag':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.bottom mag'], mode='lines'))
    fig.update_layout(title='Bottom Mag', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Sled State':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.sled state'], mode='lines'))
    fig.update_layout(title='Sled State', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)
elif selected_graph == 'Power Mode':
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.power mode'], mode='lines'))
    fig.update_layout(title='Power Mode', xaxis_title='Time [h]', yaxis_title='State')
    st.plotly_chart(fig, use_container_width=True)

st.write('Location: ')

latitude = df['latitude'].iloc[0]
longitude = df['longitude'].iloc[0]
data = pd.DataFrame({"lat": [latitude], "lon": [longitude]})

layer = pdk.Layer(
    "ScatterplotLayer",
    data,
    get_position=["lon", "lat"],
    get_color=[255, 0, 0],  # Red color
    get_radius=50,  # Size of marker
)
view_state = pdk.ViewState(
    latitude=latitude,
    longitude=longitude,
    zoom=12,  # Adjust zoom level
    pitch=0,
)
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/streets-v11",  # Other styles available
))
st.write(f"Marked Location: **Lat:** {latitude}, **Lon:** {longitude}")