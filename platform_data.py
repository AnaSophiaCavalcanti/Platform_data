import os
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import pydeck as pdk
from datetime import datetime, timedelta
import hashlib
import certifi
import pytz


# Function to verify the password
def check_password(password):
    return hashlib.sha256(password.encode()).hexdigest() == 'c467fa26032df945496ca1bef460161bf21c42c8e2899a90d29e0829390cb776'

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)#,  tlsCAFile=certifi.where()) #tlsAllowInvalidCertificates=True,
db = client["fdep_project"]

#@st.cache_resource
def update_collection_dates():
    
    # Load existing document from MongoDB
    doc = db["collection_dates"].find_one({"_id": "unique_dates"})
    collection_dates = {k: v for k, v in doc.items() if k != "_id"} if doc else {}

    updated = False

    # Helper function to convert timestamp or datetime to "YYYY-MM-DD"
    def extract_date(dt):
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                try:
                    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return None
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d")
        return None

    # Loop through all 8 collections
    for i in range(8):
        col_name = f"L{i}_parameters"
        collection = db[col_name]

        # Get the most recent timestamp
        last_doc = collection.find_one({}, sort=[("timestamp", -1)])
        last_dt = last_doc.get("datetime") if last_doc else None
        last_date = extract_date(last_dt)

        if not last_date:
            continue

        # Update if the date is new
        current_dates = set(collection_dates.get(col_name, []))
        if last_date not in current_dates:
            current_dates.add(last_date)
            collection_dates[col_name] = sorted(current_dates)
            updated = True

    # Save only if updates were made
    if updated:
        collection_dates["_id"] = "unique_dates"
        db["collection_dates"].replace_one({"_id": "unique_dates"}, collection_dates, upsert=True)

update_collection_dates()

collections_ = db.list_collection_names()

collections = []

for key in collections_:
    if 'L' in key:
        collections.append(key)

#collection = db['platforms_data']

platform_location = {
    'L0_parameters': 'BBC',
    'L1_parameters': 'Biscayne Canal',
    'L2_parameters': 'Biscayne Bay',
    'L3_parameters': 'Little River (Up)',
    'L4_parameters': 'Little River (Down)',
    'L5_parameters': 'North Bay Village (North)',
    'L6_parameters': 'North Bay Village (South)',
    'L7_parameters': 'Miami River',   
    'L8_parameters': 'Miami River (Down)',
}

water_columns = {
    'BBC': 0,
    'Biscayne Canal': 2,
    'Biscayne Bay': 96,
    'Little River (Up)': 3,
    'Little River (Down)': 20,
    'North Bay Village (North)': 55,
    'North Bay Village (South)': 0,
    'Miami River': 78,
    'Miami River (Down)': 0
}

final_data = []
for value in collections:
    collection = db[value]
    latest_doc = collection.find_one(
        {},  
        sort=[("timestamp", -1)],  # Sort by most recent timestamp
        #projection={"latitude": 1, "longitude": 1}
    )
    if latest_doc:
        final_data.append({
            "platform": latest_doc["metadata"]["platform"],
            "latitude": latest_doc["latitude"],
            "longitude": latest_doc["longitude"]
        })

cycl2cm = 0.3175

tab1, tab2 = st.tabs(['Data', 'About'])

with tab1:

    st.markdown("### Platforms Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Retrieve all unique platforms
        available_locations = [platform_location[key] for key in collections if key in platform_location]

        available_locations = sorted(available_locations)
        
        selected_platform = st.selectbox("Select a platform:", available_locations)

        collection_key = next((key for key, value in platform_location.items() if value == selected_platform), None)
        
        collection = db[collection_key]

        column = water_columns[selected_platform]*2.54
        
        #platforms = collection.distinct("metadata.platform")
        
        # User selects either "Daily" or "Weekly"
        option = st.radio("Select the period:", ["Daily", "Weekly"])
    
    with col2:
        
       # Read the document containing all unique dates by collection
        doc = db["collection_dates"].find_one({"_id": "unique_dates"})
        
        # Retrieve the list of dates for the given collection key, in reverse chronological order
        dates = list(reversed(doc.get(collection_key, []))) if doc else []
        
        if option == "Weekly":
            week_ranges = []
            for d in dates:
                date = pd.to_datetime(d)
                start_date = date - pd.Timedelta(days=date.weekday())
                end_date = start_date + pd.Timedelta(days=6)
                week_ranges.append(f"{start_date.date()} - {end_date.date()}")
            week_options = list(set(week_ranges))
            week_options.sort(reverse=True)
    
        selected_period = st.selectbox("Select the date:", dates if option == "Daily" else week_options)
    
        if option == "Weekly":
            # Split the selected period string into start and end date parts
            start_str, end_str = selected_period.split(" - ")
            
            # Define the local timezone
            local_tz = pytz.timezone("America/New_York")
            
            # Parse the start and end dates as naive datetime objects
            start_naive = datetime.strptime(start_str, "%Y-%m-%d")
            end_naive = datetime.strptime(end_str, "%Y-%m-%d")
            
            # Localize to the selected timezone
            start_local = local_tz.localize(start_naive)
            end_local = local_tz.localize(end_naive)
            
            # Convert localized datetimes to UTC
            start_utc = start_local.astimezone(pytz.utc)
            end_utc = end_local.astimezone(pytz.utc)
            
            # Convert to Unix timestamps (for querying indexed numeric timestamp fields)
            start_ts = start_utc.timestamp()
            end_ts = end_utc.timestamp()
            
            # Build MongoDB query to filter documents in the selected range
            query = {'timestamp': {'$gte': start_ts, '$lt': end_ts}}
        else:           
            # Define the local timezone (e.g., Miami = America/New_York)
            local_tz = pytz.timezone("America/New_York")
            
            # Parse the selected day 
            start_naive = datetime.strptime(selected_period, "%Y-%m-%d")  # naive datetime (no timezone)
            start_local = local_tz.localize(start_naive)                  # attach local timezone
            end_local = start_local + timedelta(days=1)                   # end of the day in local time
            
            # Convert both to UTC for comparison with MongoDB timestamps
            start_ts = start_local.astimezone(pytz.utc).timestamp()
            end_ts = end_local.astimezone(pytz.utc).timestamp()
            
            # Build the MongoDB query using numeric timestamps
            query = {"timestamp": {"$gte": start_ts, "$lt": end_ts}}
        
        data = list(collection.find(query))    
        df = pd.json_normalize(data)
        
        if '_id' in df.columns:
            df = df.drop('_id', axis=1)
        
        df['datetime'] = pd.to_datetime(df['datetime'])

        password = st.text_input("Authorized users only:", type="password")
        
        if password and check_password(password):
            options = ['Water Column Height', 'Depth', 'Temperature', 'Specific Conductance', 'Salinity', 'ODO, mg/L', 'Turbidity', 'Wiper Position', 'Pressure', 'Depth, m', 'Voltage', 'Current', 'Top Mag', 'Top Float', 'Bottom Float', 'Bottom Mag', 'Sled State', 'Power Mode']
            st.success("Extra graphs unlocked!")
        else:
            options = ['Water Column Height', 'Depth', 'Temperature', 'Salinity', 'ODO, mg/L', 'Turbidity']
    
    with col3:
        selected_graph = st.selectbox('Select a graph:', options)
        
    client.close()

    df_filter_calibration = df[df['metadata.sledstate']!=2]
    df_filter = df[df['metadata.sledstate'] == 0]
    df_profile = df[df['metadata.sledstate'] == 1]

    df = df.sort_values('datetime').copy()
    df_filter = df_filter.sort_values('datetime').copy()
    depth_map = dict(zip(df_filter['datetime'], df_filter['metadata.depth']))    
    last_value = df_filter['metadata.depth'].iloc[0]
    water_levels = []    
    for dt in df['datetime']:
        if dt in depth_map:
            last_value = depth_map[dt]
        water_levels.append(last_value)
    df_water_level = pd.DataFrame({
        'datetime': df['datetime'],
        'water_level': water_levels
    })

# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _     
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    
    if selected_graph == 'Water Column Height':
        y1 = df['metadata.depth']*cycl2cm + column
        y2 = df_filter['metadata.depth']*cycl2cm + 27 + (23*cycl2cm) + column
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='sensor position'))
        fig.add_trace(go.Scatter(x=df_filter['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(255,0,0,0.5)'), name='water level'))
        fig.update_layout(title='Water Column Height', xaxis_title='Time [h]', yaxis_title='Sensor Position [cm]', yaxis=dict(range=[0, 160 + column]), yaxis2=dict(title='Water Level [cm]', overlaying = 'y', side='right', range=[0, 160 + column]))
        st.plotly_chart(fig, use_container_width=True)
        st.write('The vertical reference (zero height) is defined at the bottom of the water body beneath the platform. All height measurements represent the vertical distance from this reference point to the EXO sensors or the water surface.')
        # fig = go.Figure()
        # fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.depth']*0.3175, mode='lines'))
        # fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='depth [cm]', yaxis=dict(range=[0, 140]))
        # st.plotly_chart(fig, use_container_width=True)
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    
    elif selected_graph == 'Depth':
        y2 = df_water_level['water_level']*cycl2cm + 27 + (23*cycl2cm)
        y1 = y2 - df['metadata.depth']*cycl2cm
        y2 = y2 - y2
        depth_max = y1.max()
        y_range = [depth_max - 160, depth_max]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='sensor position'))
        fig.add_trace(go.Scatter(x=df_water_level['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(255,0,0,0.5)'), name='water level'))
        fig.update_layout(title='Water Column Height', xaxis_title='Time [h]', yaxis_title='Sensor Position [cm]', yaxis=dict(autorange='reversed', range=y_range), yaxis2=dict(title='Water Level [cm]', overlaying = 'y', side='right', autorange='reversed', range=y_range, matches='y'))
        st.plotly_chart(fig, use_container_width=True)
        st.write('The depth is defined as the vertical distance between the water surface and the EXO sensors. In this configuration, the water level is used as the zero reference, and depth values increase as the sensors move downward below the surface.')
        # fig = go.Figure()
        # fig.add_trace(go.Scatter(x=df['datetime'], y=df['metadata.depth']*0.3175, mode='lines'))
        # fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='depth [cm]', yaxis=dict(range=[0, 140]))
        # st.plotly_chart(fig, use_container_width=True)
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    elif selected_graph == 'Temperature':
        margin = 3
        y_min = df['exodata.1'].min() - margin
        y_max = df['exodata.1'].max() + margin
        y1 = df_filter_calibration['exodata.1']
        y2 = df['metadata.depth']*cycl2cm
        st.write("Choose the option below to view the sensor position graph alongside the temperature graph.")
        show_depth = st.checkbox("See sensor position.")
        fig = go.Figure()
        if show_depth:
            fig.add_trace(go.Scatter(x=df_filter_calibration['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='temperature'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='sensor position'))
            fig.update_layout(title='Temperature', xaxis_title='Time [h]', yaxis_title='Temperature [°C]', yaxis=dict(range=[y_min, y_max]), yaxis2=dict(title='Sensor Position [cm]', overlaying = 'y', side='right', range=[0, 140]))
        else:
            fig.add_trace(go.Scatter(x=df_filter_calibration['datetime'], y=df_filter_calibration['exodata.1'], mode='lines'))
            fig.update_layout(title='Temperature', xaxis_title='Time [h]', yaxis_title='Temperature [°C]', yaxis=dict(range=[y_min, y_max]))
        st.plotly_chart(fig, use_container_width=True)
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    elif selected_graph == 'Specific Conductance':
        y1 = df['exodata.7']
        y2 = df['metadata.depth']*cycl2cm
        st.write("Choose the option below to view the sensor position graph alongside the conductance graph.")
        show_depth = st.checkbox("See sensor position.")
        fig = go.Figure()
        if show_depth:
            fig.add_trace(go.Scatter(x=df['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='conductance'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='sensor position'))
            fig.update_layout(title='Specific Conductance', xaxis_title='Time [h]', yaxis_title='Specific Conductance [μS/cm]', yaxis2=dict(title='Sensor Position [cm]', overlaying = 'y', side='right', range=[0, 140]))
        else:
            fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.7'], mode='lines'))
            fig.update_layout(title='Specific Conductance', xaxis_title='Time [h]', yaxis_title='Specific Conductance [μS/cm]')
        st.plotly_chart(fig, use_container_width=True)
        st.write('Specific conductance (or conductivity) measures water’s ability to conduct electricity, which increases with higher ion concentration. It’s expressed in µS/cm (microsiemens per centimeter). Freshwater typically has low conductance, while brackish and seawater have higher values. Changes in conductivity can indicate pollution, runoff, or seasonal variations, as factors like temperature, salinity, and dissolved solids affect ion concentrations.')
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    elif selected_graph == 'Salinity':
        y1 = df_filter_calibration['exodata.12']
        y2 = df['metadata.depth']*cycl2cm
        st.write("Choose the option below to view the sensor position graph alongside the salinity graph.")
        show_depth = st.checkbox("See sensor position.")
        fig = go.Figure()
        if show_depth:
            fig.add_trace(go.Scatter(x=df_filter_calibration['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='salinity'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='sensor position'))
            fig.update_layout(title='Salinity', xaxis_title='Time [h]', yaxis_title='Salinity [PPT]', yaxis=dict(range=[0, 40]), yaxis2=dict(title='Sensor Position [cm]', overlaying = 'y', side='right', range=[0, 140]))
        else:
            fig.add_trace(go.Scatter(x=df_filter_calibration['datetime'], y=df_filter_calibration['exodata.12'], mode='lines'))
            fig.update_layout(title='Salinity', xaxis_title='Time [h]', yaxis_title='Salinity [PPT]', yaxis=dict(range=[0, 40]))
        st.plotly_chart(fig, use_container_width=True)
        st.write('Salinity, measured in ppt (parts per thousand), indicates water type and changes. Freshwater: 0–0.5 ppt, brackish: 0.5–30 ppt, seawater: ~35 ppt, hypersaline: >40 ppt. Tides increase salinity, while rainfall lowers it. Evaporation raises salinity, and sudden shifts may indicate pollution or river discharge.')
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
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
        st.write("Choose the option below to view the sensor position graph alongside the ODO graph.")
        show_depth = st.checkbox("See sensor position.")
        if show_depth:
            y1 = df_filter_calibration['exodata.212']
            y2 = df['metadata.depth']*cycl2cm
            #y1 = df_filter['exodata.212']
            #y2 = df_filter['metadata.depth']*cycl2cm + 25
            fig.add_trace(go.Scatter(x=df_filter_calibration['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='ODO'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='sensor position'))
            fig.update_layout(title='Optical Dissolved Oxygen', xaxis_title='Time [h]', yaxis_title='ODO [mg/L]', yaxis=dict(range=[0, 10], showgrid=True, dtick=1), yaxis2=dict(title='Sensor Position [cm]', overlaying = 'y', side='right', range=[0, 140]))
        else:
            fig.add_trace(go.Scatter(x=df_filter_calibration['datetime'], y=df_filter_calibration['exodata.212'], mode='lines'))
            fig.update_layout(title='Optical Dissolved Oxygen', xaxis_title='Time [h]', yaxis_title='ODO [mg/L]', yaxis=dict(range=[0, 10], showgrid=True, dtick=1))    
        st.plotly_chart(fig, use_container_width=True)
        st.write('Optical Dissolved Oxygen (ODO) in mg/L measures the concentration of dissolved oxygen in water using optical sensors. It is crucial for assessing water quality, as oxygen is vital for the survival of aquatic organisms. Low ODO levels can indicate pollution or poor water quality, which may harm ecosystems and reduce biodiversity.')
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    elif selected_graph == 'Turbidity':
        y1 = df_filter_calibration['exodata.223']
        y2 = df['metadata.depth']*cycl2cm
        st.write("Choose the option below to view the sensor position graph alongside the turbidity graph.")
        show_depth = st.checkbox("See sensor position.")
        fig = go.Figure()
        if show_depth:
            fig.add_trace(go.Scatter(x=df_filter_calibration['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='turbidity'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='sensor position'))
            fig.update_layout(title='Turbidity', xaxis_title='Time [h]', yaxis_title='Turbidity [FNU]', yaxis2=dict(title='Sensor Position [cm]', overlaying = 'y', side='right', range=[0, 140]))
        else:
            fig.add_trace(go.Scatter(x=df_filter_calibration['datetime'], y=df_filter_calibration['exodata.223'], mode='lines'))
            fig.update_layout(title='Turbidity', xaxis_title='Time [h]', yaxis_title='Turbidity [FNU]')
        st.plotly_chart(fig, use_container_width=True)
        st.write('Turbidity measures water clarity, indicating the presence of suspended particles. It’s expressed in FNU (Formazin Nephelometric Units). Clear water has low turbidity, while higher values suggest pollutants like sediment, algae, or organic matter. Changes in turbidity can result from rainfall, runoff, or disturbances, and it can impact aquatic life by reducing light penetration and oxygen levels.')
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    elif selected_graph == 'Wiper Position':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.229'], mode='lines'))
        fig.update_layout(title='Wiper Position', xaxis_title='Time [h]', yaxis_title='Wiper Position [V]')
        st.plotly_chart(fig, use_container_width=True)
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    elif selected_graph == 'Pressure':
        fig = go.Figure()
        y1 = df['exodata.20']
        y2 = df['metadata.depth']*cycl2cm
        st.write("Choose the option below to view the sensor position graph alongside the pressure graph.")
        show_depth = st.checkbox("See sensor position.")
        fig = go.Figure()
        if show_depth:
            fig.add_trace(go.Scatter(x=df['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='pressure'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='sensor position'))
            fig.update_layout(title='Pressure', xaxis_title='Time [h]', yaxis_title='Pressure [psia]', yaxis2=dict(title='Sensor Position [cm]', overlaying = 'y', side='right', range=[0, 140]))
        else:
            fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.20'], mode='lines'))
            fig.update_layout(title='Pressure', xaxis_title='Time [h]', yaxis_title='Pressure [psia]')
        #fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.20'], mode='lines'))
        #fig.update_layout(title='Pressure', xaxis_title='Time [h]', yaxis_title='Pressure [psia]')
        st.plotly_chart(fig, use_container_width=True)
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
    elif selected_graph == 'Depth, m':
        fig = go.Figure()
        y1 = df['exodata.22']
        y2 = df['metadata.depth']*cycl2cm
        st.write("Choose the option below to view the depth graph alongside the EXO's depth graph.")
        show_depth = st.checkbox("See sensor position.")
        fig = go.Figure()
        if show_depth:
            fig.add_trace(go.Scatter(x=df['datetime'], y=y1, mode='lines', yaxis='y1', line=dict(color='rgba(0,0,255,1)'), name='EXO\'s depth'))
            fig.add_trace(go.Scatter(x=df['datetime'], y=y2, mode='lines', yaxis='y2', line=dict(color='rgba(74,144,226,0.5)'), name='depth'))
            fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='Depth [m]', yaxis2=dict(title='depth [cm]', overlaying = 'y', side='right', range=[0, 140]))
        else:
            fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.22'], mode='lines'))
            fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='Depth [m]')
        #fig.add_trace(go.Scatter(x=df['datetime'], y=df['exodata.22'], mode='lines'))
        #fig.update_layout(title='Depth', xaxis_title='Time [h]', yaxis_title='Depth [m]', yaxis=dict(autorange='reversed'))
        st.plotly_chart(fig, use_container_width=True)
# _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
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
    
    st.write('Location: (marked in red)')
    
    df_map = pd.DataFrame(final_data)
    
    platform = df['metadata.platform'].iloc[-1]
    latitude, longitude = df_map.query('platform == @platform')[["latitude", "longitude"]].iloc[0]
    
    df_map["color"] = df_map["platform"].apply(lambda x: [255, 0, 0, 200] if x == platform else [0, 0, 255, 200])
    
    col1, col2 = st.columns(2)

    with col1:
    
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
        #st.write(f"Marked Location: **Lat:** {latitude}, **Lon:** {longitude}")

    with col2:
        st.write(' ')
        if platform == 'P1':            
            st.image('images/p1.png', caption='Real Platform')
        elif platform == 'P2':
            st.image('images/p2.png', caption='Real Platform')
        elif platform == 'P3':
            st.image('images/p3.png', caption='Real Platform')
        elif platform == 'P4':
            st.image('images/p4.png', caption='Real Platform')
        elif platform == 'P5':
            st.image('images/p5.png', caption='Real Platform')
        elif platform == 'P6':
            st.image('images/p6.png', caption='Real Platform')
        elif platform == 'P7':
            st.image('images/p7.png', caption='Real Platform')
        elif platform == 'P8':
            st.image('images/p8.png', caption='Real Platform')

with tab2:
    #st.markdown("### Under Construction...")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.video('videos/platform.mov')
    with col2:
        pass
    with col3:
        pass
    with col4:
        pass

