# streamlit_app.py

import streamlit as st
import numpy as np
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


def run_query_df(query):
    query_job = client.query(query)
    df_query = query_job.result().to_dataframe()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    return df_query


# Print results.
st.write("Some wise words from Shakespeare:")


#rows = run_query("select cast(a as FLOAT64) as lat, cast(b as FLOAT64) as lon, extract(time from TIMESTAMP_SECONDS(cast(c as INT64))) as time_value from `iot_dataset.07_05` limit 10")

#for row in rows:
#    st.write(row['time_value'])

df_query = run_query_df("select cast(a as FLOAT64) as lat, cast(b as FLOAT64) as lon, extract(time from TIMESTAMP_SECONDS(cast(c as INT64))) as time_value from `iot_dataset.07_05` limit 10")
for column in df_query:
    st.write(df_query[column])


# CALCULATE MIDPOINT FOR GIVEN SET OF DATA
@st.cache_data
def mpoint(lat, lon):
    """
    This function calculates the midpoint of a set of latitude and longitude coordinates, using the numpy.average()
    function. It uses Streamlit's caching feature to cache the result, so it only needs to be computed once. It returns
    a tuple containing the latitude and longitude of the midpoint.
    """
    return (np.average(lat), np.average(lon))


#zoom_level = 12 # the map will be zoomed in to show the airport in detail
#midpoint = mpoint(data["lat"], data["lon"]) # the map will be centered on the midpoint of all the data points