# streamlit_app.py

import streamlit as st
import numpy as np
import pydeck as pdk
import pandas as pd
import datetime
import geopy.distance
from google.oauth2 import service_account
from google.cloud import bigquery

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)


# Create a reference to the World Cup dataset
dataset_ref = client.dataset("iot_dataset", project="serene-foundry-379413")  # CHANGE WITH YOUR OWN DATASET (NOT TABLE) NAME AND PROJECT ID

# API request - fetch the dataset
dataset = client.get_dataset(dataset_ref)

# List the tables in the dataset
tables = list(client.list_tables(dataset))
for table in tables:  
    print(table.table_id)

# Create a reference to the "Teams" table and fetch the table
table_ref = dataset_ref.table("rides") # Make sure it matches the table name printed above (case sensitive)
rides_table = client.get_table(table_ref)
df_rides = client.list_rows(rides_table).to_dataframe()

# Same for the "Players" table
table_ref = dataset_ref.table("gps_rides") # Make sure it matches the table name printed above (case sensitive)
gps_rides_table = client.get_table(table_ref)
df_gps_rides = client.list_rows(gps_rides_table).to_dataframe()


tmp_2 = df_rides.loc[df_rides['member_name_']=='Shanshan', ['ride_date']]
print(tmp_2.iloc[0,0])
print(type(tmp_2.iloc[0,0]))


st.set_page_config(layout="wide", page_title="Seeclub Luzern Logbuch", page_icon=":boat:")
st.header("Seeclub Luzern Logbuch") # Title of the app

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
    print(data.head())
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



#df = run_query_df("select * from `iot_dataset.gps_rides` where date_value = '2023-05-02' order by time_value")
#print(df.head())

# Return the dataframe of the previous ride of a specific member
def get_ride_member(member):
    df_tmp = df_rides.loc[df_rides['member_name_']==member, ['ride_date']].sort_values(by='ride_date', ascending=False)
    #print(df_tmp.iloc[0,0])
    #print(type(df_tmp.iloc[0,0]))
    #ride_date = datetime.date(df_rides.loc[df_rides.member_name_=='Shanshan', 'ride_date'].sort_values(ascending=False).head(1))
    #print(ride_date)
    return df_gps_rides[df_gps_rides.date_value==df_tmp.iloc[0,0]].sort_values(by='time_value')
    #return df_gps_rides[df_gps_rides.date_value==datetime.date(2023, 5, 28)].sort_values(by='time_value')

# Return the list of geo coordinates 
def helper_map(df): 
    #print(df.head())
    df_list = []
    for index, row in df.iterrows():
        df_list.append([row["lon"], row["lat"]])
        
    return df_list

# Return the dataframe of geo coordinates which can be used by pathline
def get_map_ride(df_list):
    df_new = pd.DataFrame(columns=['path'])
    df_new.at['0', 'path'] = df_list  
    #print(df_new.head())
    return df_new


def cal_distance(df_list):    
    coor_length = len(df_list)
    #coor_list = df_new.iloc[0]['path']
    coor_list = df_list

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
    #print(coor_distance)
    return coor_distance


"""

"""

#df_date = run_query_df("select ride_date from `iot_dataset.rides` where member_name_ = 'Shanshan' order by ride_date limit 1")
#ride_date = df_date.iloc[0,0]

tab1, tab2, tab3 = st.tabs(["Live view", "Member view", "Boat view"])

with tab1:
   #st.header("Member view")
   row1_1, row1_2 = st.columns((3, 1)) # Size of columns 2, 1, 1, 1 
    
   with row1_1:
        member = st.text_input('Enter the name of the member 👇')
   
   
   # LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS
   row2_1, row2_2 = st.columns((3, 1)) # Size of columns 2, 1, 1, 1 


    #df_query = run_query_df("select cast(a as FLOAT64) as lat, cast(b as FLOAT64) as lon, extract(time from TIMESTAMP_SECONDS(cast(c as INT64))) as time_value from `iot_dataset.07_05`")
    #midpoint = mpoint(df["lat"], df["lon"]) # the map will be centered on the midpoint of all the data points
    #map(df, midpoint[0], midpoint[1], 11)
    #for column in df_query:
    #    st.write(df_query[column])
   
   if member:
        df_ride_member = get_ride_member(member)
        df_list_map = helper_map(df_ride_member)
        
        with row2_1:
                #print(df_ride_member.head())
                midpoint = mpoint(df_ride_member["lat"], df_ride_member["lon"])
                df_map = get_map_ride(df_list_map)
                #print(df_new.head())
                map_zoom = 12
                map(df_map, midpoint[0], midpoint[1], map_zoom)


                    
        with row2_2:
                col1, col2 = st.columns([1, 4])
                coor_distance = cal_distance(df_list_map)
                col2.metric(label="Distance", value=coor_distance)
                col2.metric(label="Temperature", value="70 °F")
                col2.metric(label="Temperature", value="70 °F")
                col2.metric(label="Temperature", value="70 °F")


with tab2:
   st.header("A dog")
   st.image("https://static.streamlit.io/examples/dog.jpg", width=200)

with tab3:
   st.header("An owl")
   st.image("https://static.streamlit.io/examples/owl.jpg", width=200)


