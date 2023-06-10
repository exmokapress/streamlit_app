import streamlit as st
import numpy as np
import pydeck as pdk
import pandas as pd
import datetime
from datetime import time
import geopy.distance
from google.oauth2 import service_account
from google.cloud import bigquery


# Create API client
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)



# Create a reference to the dataset
dataset_ref = client.dataset("iot_dataset", project="serene-foundry-379413")  # CHANGE WITH YOUR OWN DATASET (NOT TABLE) NAME AND PROJECT ID

# API request to fetch the dataset
dataset = client.get_dataset(dataset_ref)

# List the tables in the dataset
tables = list(client.list_tables(dataset))
#for table in tables:  
    #print(table.table_id)

# Create a reference to the "rides" table and fetch the table
table_ref = dataset_ref.table("rides") 
rides_table = client.get_table(table_ref)
# Create a dataframe from the table
df_rides = client.list_rows(rides_table).to_dataframe()

# Same for the "gps_rides" table
table_ref = dataset_ref.table("gps_rides") # Make sure it matches the table name printed above (case sensitive)
gps_rides_table = client.get_table(table_ref)
df_gps_rides = client.list_rows(gps_rides_table).to_dataframe()



# Set up the web page of streamlit app
st.set_page_config(layout="wide", page_title="Seeclub Luzern Logbuch", page_icon=":rowboat:")
# Title of the app
st.header("Seeclub Luzern Logbuch") 



# Uses st.cache_data to only rerun when the query changes or after 10 min
# Run a query and return the result in rows
@st.cache_data(ttl=600)
def run_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert the result to list of dicts
    rows = [dict(row) for row in rows_raw]
    return rows


# Run a query and return the result in a dataframe
@st.cache_data(ttl=600)
def run_query_df(query):
    query_job = client.query(query)
    # Convert the result to a dataframe
    df_query = query_job.result().to_dataframe()
    return df_query


# Calculate the midpoint of a set of latitude and longitude coordinates
@st.cache_data
def mpoint(lat, lon):
    # Return a tuple containing the latitude and longitude of the midpoint
    return (np.average(lat), np.average(lon))


# Display the map using the given set of data
def map(data, lat, lon, zoom):
    """
    This function creates a PyDeck map with a pathline layer, based on the input data and the specified
    latitude, longitude, and zoom level. It returns the resulting PyDeck map as a Streamlit component
    ----
    :param data: a pandas dataframe containing the column path which contains all geo coordinates
    :param lat: the latitude coordinate of the map center
    :param lon: the longitude coordinate of the map center
    :param zoom: the initial zoom level of the map
    ----
    :return: a PyDeck map as a Streamlit component
    """
    #print(data.head())
    st.write(
        pdk.Deck(
            map_style = "mapbox://styles/mapbox/light-v9",
            initial_view_state = {
                "latitude": lat,
                "longitude": lon,
                "zoom": zoom,
                "pitch": 50,
            },
            # Tooltip display the name of the boat
            tooltip = {"text": "{boat}"},
            layers = [
                pdk.Layer(
                    type = "PathLayer",
                    pickable = True,
                    data = data,
                    get_color = "colour",
                    width_scale = 5,
                    width_min_pixels = 3,
                    # All geo coordinates in the coloumn path of the dataframe
                    get_path = "path",
                    get_width = 5,
                ),
            ],
        )
    )



# Return the dataframe of the previous ride of a specific member
def get_ride_member(member):
    df_tmp = df_rides.loc[df_rides['member_name_']==member, ['ride_date']].sort_values(by='ride_date', ascending=False)
    return df_gps_rides[df_gps_rides.date_value==df_tmp.iloc[0,0]].sort_values(by='time_value')


# Return the dataframe of all ride dates of a specific member
def get_ride_dates_member(member):
    df_ride_dates = df_rides.loc[df_rides['member_name_']==member, ['ride_date']].sort_values(by='ride_date', ascending=False)
    return df_ride_dates


# Return the dataframe of the previous ride of a specific boat
def get_ride_boat(boat):
    df_tmp = df_rides.loc[df_rides['boat_name_']==boat, ['ride_date']].sort_values(by='ride_date', ascending=False)
    return df_gps_rides[df_gps_rides.date_value==df_tmp.iloc[0,0]].sort_values(by='time_value')


# Return the dataframe of all ride dates of a specific boat
def get_ride_dates_boat(boat):
    df_tmp_dates = df_rides.loc[df_rides['boat_name_']==boat, ['ride_date']]['ride_date'].unique()
    df_ride_dates = pd.DataFrame(df_tmp_dates, columns = ['ride_date']).sort_values(by='ride_date', ascending=False)
    return df_ride_dates


# Return the dataframe of the ride of a specific date
def get_ride_date(date):
    return df_gps_rides[df_gps_rides.date_value==date].sort_values(by='time_value')
    

# Return the list of geo coordinates 
def helper_map(df): 
    #print(df.head())
    df_list = []
    for index, row in df.iterrows():
        df_list.append([row["lon"], row["lat"]])
        
    return df_list


# Return the dataframe of geo coordinates which can be used by the pathline layer to display the map later
def get_map_ride(df_list):
    #df_map = pd.DataFrame(columns=['path'])
    #df_map.at['0', 'path'] = df_list  
    #print(df_map.head())
    df_map = pd.DataFrame(columns=['path', 'colour', 'boat'])
    df_map.at['0', 'path'] = df_list
    # Define the colour of the path on the map
    df_map.at['0', 'colour'] = [255, 0, 0]
    df_map.at['0', 'boat'] = ''
    
    return df_map


# Calculate the total distance of the ride
def cal_distance(df_list):    
    coor_length = len(df_list)
    coor_list = df_list

    coor_distance = 0.0
    i = 0
    j = 1
    # Sum up the distance between each 2 geo coordinates of the ride
    while j < coor_length:
        # Convert the distance to km
        coor_distance += geopy.distance.geodesic(coor_list[i], coor_list[j]).km
        #print(coor_list[i])
        #print(coor_list[j])
        #print(coor_distance)
        i += 1
        j += 1

    #coor_distance = round(coor_distance, 2)
    #print(coor_distance)
    return coor_distance



# Structure the app in tabs
tab1, tab2, tab3 = st.tabs(["Member view", "Boat view", "Live view"])


# Look up a specific member to see the previous ride and the statistic
with tab1:

   # Lay out the screen to a ratio of 3:1 
   row1_1, row1_2 = st.columns((3, 1)) 
    
   with row1_1:
        member = st.text_input('Enter the name of the member :hugging_face:')
   
   # 3/4 for the map while 1/4 for the statistic
   row2_1, row2_2 = st.columns((3, 1)) 


   if member:
        # Get all data of a member
        df_ride_member = get_ride_member(member)
        df_list_map = helper_map(df_ride_member)
        df_dates = get_ride_dates_member(member)
        nr_rides = len(df_dates)
      
        i = 0
        total_coor_distance = 0
        
        # Calculate the total distance of a member
        while (i<nr_rides):
            print(df_dates.iloc[i,0])
            df_ride_date = get_ride_date(df_dates.iloc[i,0])
          
            print(df_ride_date.head())
            df_list_ride_date = helper_map(df_ride_date)
            
            total_coor_distance += cal_distance(df_list_ride_date)
            print(total_coor_distance)
            i += 1
        
        total_coor_distance = round(total_coor_distance, 2)
        
       
        with row2_1:
                #print(df_ride_member.head())
                # Calculate the midpoint of the previous ride of a member
                midpoint = mpoint(df_ride_member["lat"], df_ride_member["lon"])
                df_map = get_map_ride(df_list_map)
                #print(df_new.head())
                # Set the zoom level
                map_zoom = 12.4
                # Display the map
                map(df_map, midpoint[0], midpoint[1], map_zoom)
                              
       
        with row2_2:
                # Lay out the space to a ratio of 1:4
                # 1/4 empty to create a separation, 3/4 for the statistic
                col1, col2 = st.columns([1, 4])
                coor_distance = cal_distance(df_list_map)
                coor_distance = round(coor_distance, 2)
                # Display the statistic of the previous ride
                col2.metric(label="Previous rowing distance ", value=str(coor_distance)+" km")
                col2.metric(label="Previous rowing date ", value=str(df_dates.iloc[0,0]))
                col2.divider()
                # Display overall statistic
                col2.metric(label="Total rowing distance ", value=str(total_coor_distance)+" km")
                col2.metric(label="Number of rowings ", value=nr_rides)
                col2.metric(label="Average rowing distance ", value=str(round(total_coor_distance/nr_rides, 2))+" km")



# Look up a specific boat to see the previous ride and the statistic
# It follows the same logic as member view
with tab2:

   row1_1, row1_2 = st.columns((3, 1))  
    
   with row1_1:
        boat = st.text_input('Enter the name of the boat :hugging_face:')
   
   
   row2_1, row2_2 = st.columns((3, 1))

   
   if boat:
        df_ride_boat = get_ride_boat(boat)
        df_list_map = helper_map(df_ride_boat)
        df_dates = get_ride_dates_boat(boat)
        nr_rides = len(df_dates)
      
        i = 0
        total_coor_distance = 0
        
        while (i<nr_rides):
            print(df_dates.iloc[i,0])
            df_ride_date = get_ride_date(df_dates.iloc[i,0])
          
            print(df_ride_date.head())
            df_list_ride_date = helper_map(df_ride_date)
            
            total_coor_distance += cal_distance(df_list_ride_date)
            print(total_coor_distance)
            i += 1
        
        total_coor_distance = round(total_coor_distance, 2)
        
       
        with row2_1:
                #print(df_ride_member.head())
                midpoint = mpoint(df_ride_boat["lat"], df_ride_boat["lon"])
                df_map = get_map_ride(df_list_map)
                #print(df_new.head())
                map_zoom = 12.4
                map(df_map, midpoint[0], midpoint[1], map_zoom)
                              
       
        with row2_2:
                col1, col2 = st.columns([1, 4])
                coor_distance = cal_distance(df_list_map)
                coor_distance = round(coor_distance, 2)
                col2.metric(label="Previous rowing distance ", value=str(coor_distance)+" km")
                col2.metric(label="Previous rowing date ", value=str(df_dates.iloc[0,0]))
                col2.divider()
                col2.metric(label="Total rowing distance ", value=str(total_coor_distance)+" km")
                col2.metric(label="Number of rowings ", value=nr_rides)
                col2.metric(label="Average rowing distance ", value=str(round(total_coor_distance/nr_rides, 2))+" km")



# Mock the live view look & feel when multiple boats are out on the water
with tab3:
    
    # Get all rides
    df_ride_1 = get_ride_date(datetime.date(2023, 5, 28))
    df_ride_2 = get_ride_date(datetime.date(2023, 5, 7))
    df_ride_3 = get_ride_date(datetime.date(2023, 5, 2))
    
    # Prepare the data for the map display later
    list_map_1 = helper_map(df_ride_1.iloc[0:200])
    list_map_2 = helper_map(df_ride_2.iloc[0:120])
    list_map_3 = helper_map(df_ride_3.iloc[0:570])
    
    df_map = pd.DataFrame(columns=['path', 'colour', 'boat'])
   
    # Set up the first ride
    df_map.at['0', 'path'] = list_map_1
    df_map.at['0', 'colour'] = [255, 0, 0]
    df_map.at['0', 'boat'] = 'Wernli'
    
    # Set up the second ride
    df_map.at['1', 'path'] = list_map_2
    df_map.at['1', 'colour'] = [0, 255, 0]
    df_map.at['1', 'boat'] = 'Happy end'
    
    # Set up the third ride
    df_map.at['2', 'path'] = list_map_3
    df_map.at['2', 'colour'] = [0, 0, 255]
    df_map.at['2', 'boat'] = 'Take five'    

    midpoint = mpoint(df_gps_rides["lat"], df_gps_rides["lon"])
    
    map_zoom = 13
    # Display the map
    map(df_map, midpoint[0], midpoint[1], map_zoom)
   
   



