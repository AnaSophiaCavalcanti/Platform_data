import os
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import pydeck as pdk
import plotly.express as px

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
db = client["fdep_project"]
collection = db['platforms_data']

tab1, tab2 = st.tabs(['Data', 'About'])

with tab1:

    st.title("Platforms Data")
    
    platforms = collection.distinct('metadata.platform')

    final_data = []
    for value in platforms:
        latest_doc = collection.find_one(
            {"metadata.platform": value},  
            sort=[("timestamp", -1)],  # Sort by most recent timestamp
            projection={"latitude": 1, "longitude": 1}
        )
        if latest_doc:
            final_data.append({
                "platform": value,
                "latitude": latest_doc["latitude"],
                "longitude": latest_doc["longitude"]
            })
    
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
        fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='depth', yaxis=dict(range=[0, 432]))
        st.plotly_chart(fig, use_container_width=True)
    elif selected_graph == 'Temperature':
        margin = 3
        y_min = df['exodata.1'].min() - margin
        y_max = df['exodata.1'].max() + margin
        y1 = df['exodata.1']
        y2 = df['metadata.depth']
        st.write("Choose the option below to view the depth chart alongside the temperature chart.")
        show_depth = st.checkbox("See depth.")
        fig = go.Figure()
        if show_depth:
            fig.add_trace(go.Scatter(x=df['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='temperature'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='depth'))
            fig.update_layout(title='Temperature', xaxis_title='Time [h]', yaxis_title='Temperature [°C]', yaxis=dict(range=[y_min, y_max]), yaxis2=dict(overlaying = 'y', side='right', range=[0, 432]))
        else:
            fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.1'], mode='lines'))
            fig.update_layout(title='Temperature', xaxis_title='Time [h]', yaxis_title='Temperature [°C]', yaxis=dict(range=[y_min, y_max]))
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
        # Define ODO thresholds
        low_threshold = 1     # Poor Oxygen (Hypoxia)
        medium_threshold = 3  # Moderate Oxygen
        high_threshold = 10   # Healthy Oxygen
        fig = go.Figure()
        # Add colored background regions for different oxygen levels
        fig.add_shape(type="rect", xref="paper", yref="y",
                      x0=0, x1=1, y0=0, y1=low_threshold,
                      fillcolor="#FF9999", opacity=0.3, layer="below", line_width=0) #C6DBEF
        fig.add_shape(type="rect", xref="paper", yref="y",
                      x0=0, x1=1, y0=low_threshold, y1=medium_threshold,
                      fillcolor="#FFD966", opacity=0.3, layer="below", line_width=0) #4292C6
        fig.add_shape(type="rect", xref="paper", yref="y",
                      x0=0, x1=1, y0=medium_threshold, y1=high_threshold,
                      fillcolor="#4CAF50", opacity=0.3, layer="below", line_width=0) #08306B
        fig.add_annotation(x=0.5, y=0.5, text="Poor Oxygen (0-1 mg/L)", showarrow=False, xref="paper", yref="y",
                           font=dict(color="black", size=12))
        fig.add_annotation(x=0.5, y=2, text="Moderate Oxygen (1-3 mg/L)", showarrow=False, xref="paper", yref="y",
                           font=dict(color="black", size=12))
        fig.add_annotation(x=0.5, y=6.5, text="Healthy Oxygen (3-10 mg/L)", showarrow=False, xref="paper", yref="y",
                           font=dict(color="black", size=12))
        st.write("Choose the option below to view the depth chart alongside the ODO chart.")
        show_depth = st.checkbox("See depth.")
        if show_depth:
            y1 = df['exodata.212']
            y2 = df['metadata.depth']
            fig.add_trace(go.Scatter(x=df['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='ODO'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='depth'))
            fig.update_layout(title='Optical Dissolved Oxygen', xaxis_title='Time [h]', yaxis_title='ODO [mg/L]', yaxis=dict(range=[0, 10], showgrid=True, dtick=1), yaxis2=dict(overlaying = 'y', side='right', range=[0, 432]))
        else:
            fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.212'], mode='lines'))
            fig.update_layout(title='Optical Dissolved Oxygen', xaxis_title='Time [h]', yaxis_title='ODO [mg/L]', yaxis=dict(range=[0, 10], showgrid=True, dtick=1))    
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
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.topmag'], mode='lines'))
        fig.update_layout(title='Top Mag', xaxis_title='Time [h]', yaxis_title='State')
        st.plotly_chart(fig, use_container_width=True)
    elif selected_graph == 'Top Float':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.topfloat'], mode='lines'))
        fig.update_layout(title='Top Float', xaxis_title='Time [h]', yaxis_title='State')
        st.plotly_chart(fig, use_container_width=True)
    elif selected_graph == 'Bottom Float':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.bottomfloat'], mode='lines'))
        fig.update_layout(title='Bottom Float', xaxis_title='Time [h]', yaxis_title='State')
        st.plotly_chart(fig, use_container_width=True)
    elif selected_graph == 'Bottom Mag':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.bottommag'], mode='lines'))
        fig.update_layout(title='Bottom Mag', xaxis_title='Time [h]', yaxis_title='State')
        st.plotly_chart(fig, use_container_width=True)
    elif selected_graph == 'Sled State':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.sledstate'], mode='lines'))
        fig.update_layout(title='Sled State', xaxis_title='Time [h]', yaxis_title='State')
        st.plotly_chart(fig, use_container_width=True)
    elif selected_graph == 'Power Mode':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.powermode'], mode='lines'))
        fig.update_layout(title='Power Mode', xaxis_title='Time [h]', yaxis_title='State')
        st.plotly_chart(fig, use_container_width=True)
    
    st.write('Location: ')
    
    df_map = pd.DataFrame(final_data)
    
    platform = df['metadata.platform'].iloc[-1]
    latitude, longitude = df_map.query('platform == @platform')[["latitude", "longitude"]].iloc[0]
    
    df_map["color"] = df_map["platform"].apply(lambda x: [255, 0, 0, 200] if x == selected_collection else [0, 0, 255, 200])
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        df_map,
        get_position=["longitude", "latitude"],
        get_color="color", 
        get_radius=100,  # Size of marker
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
        map_style="mapbox://styles/mapbox/streets-v11",
    ))
    
    st.write(f"Marked Location: **Lat:** {latitude}, **Lon:** {longitude}")

with tab2:
    st.title("Under Construction...")

    