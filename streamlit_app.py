# streamlit_app.py

import streamlit as st
import numpy as np
import pydeck as pdk
import pandas as pd
import geopy.distance
from google.oauth2 import service_account
from google.cloud import bigquery

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)


st.set_page_config(layout="wide", page_title="SCL rowing log demo", page_icon=":boat:")


# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]
    return rows

@st.cache_data(ttl=600)
def run_query_df(query):
    query_job = client.query(query)
    df_query = query_job.result().to_dataframe()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    return df_query


# CALCULATE MIDPOINT FOR GIVEN SET OF DATA
@st.cache_data
def mpoint(lat, lon):
    """
    This function calculates the midpoint of a set of latitude and longitude coordinates, using the numpy.average()
    function. It uses Streamlit's caching feature to cache the result, so it only needs to be computed once. It returns
    a tuple containing the latitude and longitude of the midpoint.
    """
    return (np.average(lat), np.average(lon))


# FUNCTION FOR AIRPORT MAPS
def map(data, lat, lon, zoom):
    """
    This function creates a PyDeck map with a hexagonal heatmap layer, based on the input data and the specified
    latitude, longitude, and zoom level. It returns the resulting PyDeck map as a Streamlit component.
    ----
    :param data: a pandas dataframe containing the data to be visualized on the map
    :param lat: the latitude coordinate of the map center
    :param lon: the longitude coordinate of the map center
    :param zoom: the initial zoom level of the map
    ----
    :return: a PyDeck map as a Streamlit component
    """
    st.write(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": lat,
                "longitude": lon,
                "zoom": zoom,
                "pitch": 50,
            },
            layers=[
                pdk.Layer(
                    type="PathLayer",
                    pickable=True,
                    data = data,
                    get_color=[255, 0, 0],
                    width_scale=5,
                    width_min_pixels=2,
                    get_path="path",
                    get_width=5,
                ),
            ],
        )
    )

#df = pd.read_csv("bquxjob_346917b4_18823823f98.csv")
#print(df.head())

df = run_query_df("select * from `iot_dataset.gps_rides` where date_value = '2023-05-02' order by time_value")
print(df.head())

df_list = []
for index, row in df.iterrows():
  df_list.append([row["lon"], row["lat"]])
  
coor_length = len(df_list)

df_new = pd.DataFrame(columns=['path'])
df_new.at['0', 'path'] = df_list  
print(df_new.head())



coor_list = df_new.iloc[0]['path']

coor_distance = 0.0
i = 0
j = 1
while j < coor_length:
  coor_distance += geopy.distance.geodesic(coor_list[i], coor_list[j]).km
  #print(coor_list[i])
  #print(coor_list[j])
  #print(coor_distance)
  i += 1
  j += 1

coor_distance = round(coor_distance, 2)
print(coor_distance)


#df_date = run_query_df("select ride_date from `iot_dataset.rides` where member_name_ = 'Shanshan' order by ride_date limit 1")
q1 = """
bq query 
--use_legacy_sql=false 
--parameter=name:STRING:Shanshan 
select ride_date
from %s.iot_dataset.rides
where member_name_ = name 
order by ride_date desc limit 1
"""

df_date = run_query_df(q1)
ride_date = df_date.iloc[0,0]

#rows = run_query("select cast(a as FLOAT64) as lat, cast(b as FLOAT64) as lon, extract(time from TIMESTAMP_SECONDS(cast(c as INT64))) as time_value from `iot_dataset.07_05` limit 10")

#for row in rows:
#    st.write(row['time_value'])


# LAYING OUT THE TOP SECTION OF THE APP WITH 2 COLUMNS
row1_1, row1_2 = st.columns((2, 1)) # Size of columns 2, 3 means 2/5 and 3/5 of the screen

with row1_1:
    st.title("Seeclub Luzern Logbuch") # Title of the app
    #hour_selected = st.slider("Select hour of pickup", 0, 23) # Slider to select hour of pickup
    member = st.text_input('Enter the name of the member 👇')
    #st.write('The current movie title is', member)

with row1_2:
    # Just a text to explain the app
    st.write("something")

# LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS
row2_1, row2_2 = st.columns((2, 1)) # Size of columns 2, 1, 1, 1 


#df_query = run_query_df("select cast(a as FLOAT64) as lat, cast(b as FLOAT64) as lon, extract(time from TIMESTAMP_SECONDS(cast(c as INT64))) as time_value from `iot_dataset.07_05`")
midpoint = mpoint(df["lat"], df["lon"]) # the map will be centered on the midpoint of all the data points
#map(df, midpoint[0], midpoint[1], 11)
#for column in df_query:
#    st.write(df_query[column])

with row2_1:
    if member:
        st.write("Previous rowing of ", member)
        map(df_new, midpoint[0], midpoint[1], 13)
        
with row2_2:
    if member:
        col1, col2, col3 = st.columns(3)
        col1.metric("Your distance", coor_distance)
        col2.metric("Ride date", ride_date)
        col3.metric("Humidity", "86%", "4%")
#zoom_level = 12 # the map will be zoomed in to show the airport in detail
#midpoint = mpoint(data["lat"], data["lon"]) # the map will be centered on the midpoint of all the data points