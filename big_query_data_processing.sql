-- 1. Pub/sub from IoT device to GCP using NTP time
/*
Data format IoT table

data
lat 0, log 0, time_ntp 2023-05-02 Tues 18:17:14 
*/

-- Query to split the data to 3 colomns and save it as table 02_05 for the next processing

with 
tmp_table as(
SELECT
 SPLIT(data, ',')[offset(0)] as a,
  SPLIT(data, ',')[offset(1)] as b,
   SPLIT(data, ',')[offset(2)] as c,
from `iot_dataset.iot_table`
where data like "%,%,%")
SELECT * FROM tmp_table
WHERE a like "lat%" and c like "%Tues%"

-- Query to extract coordinates and time, and exclude all 0 coordinates 

with 
tmp_table as(
  SELECT
    cast(SUBSTR(a, (STRPOS(a, ' ') + 1), (LENGTH(a) - STRPOS(a, ' '))) as FLOAT64) AS lat,
    cast(SUBSTR(b, (STRPOS(b, 'log') + 3), (LENGTH(b) - STRPOS(b, 'log'))) as FLOAT64) AS lon,
    cast(SUBSTR(c, (-8), 8) as time) AS time_value,
    cast(SUBSTR(c, (11), 10) as date) AS date_value
  FROM 
  `iot_dataset.02_05`)
select * from tmp_table
where lat != 0 
order by time_value 



-- 2. Pub/sub IoT device to GCP using NTP timestamp every 10 seconds 

/*
Data format on the IoT table 

data
47.04501,8.321595,738585311
*/

-- Query to split the data to 3 colomns where coordinates are recorded beyond a certain time, and save it as table 28_05 for the next processing

with 
tmp_table as(
SELECT
 SPLIT(data, ',')[offset(0)] as a,
  SPLIT(data, ',')[offset(1)] as b,
   SPLIT(data, ',')[offset(2)] as c,
from `iot_dataset.iot_table`
where data like "%,%,%")
SELECT * FROM tmp_table
WHERE SAFE_CAST(c AS INT64) IS NOT NULL and SAFE_CAST(c AS INT64) > 738576041

-- Query to convert coordinates to float and extract time from timestamp including postprocessing

with 
tmp_table as(
select cast(a as FLOAT64) as lat, cast(b as FLOAT64) as lon, cast(c as INT64) as timestamp_value, extract(time from TIMESTAMP_SECONDS(cast(c as INT64))) as time_value, extract(date from TIMESTAMP_SECONDS(cast(c as INT64))) as date_value_tmp 
from `iot_dataset.28_05`
)
select lat, lon, time_value, cast(DATETIME_ADD(date_value_tmp, INTERVAL 30 YEAR) as date) AS date_value from tmp_table
where lat != 0 and timestamp_value > 738576041
order by time_value 



-- 3. Write coordinates, hour, minute to a SD card every 10 seconds

/*
Data format as below

string_field_0
47.04521;8.38304;9;3
*/

-- Query to split and convert the data

with 
tmp_table as(
SELECT
 SPLIT(string_field_0, ';')[offset(0)] as a,
  SPLIT(string_field_0, ';')[offset(1)] as b,
   SPLIT(string_field_0, ';')[offset(2)] as c,
      SPLIT(string_field_0, ';')[offset(3)] as d,
from `sd_dataset.23_04`)
SELECT cast(a as FLOAT64), cast(b as FLOAT64), cast(c as INT64), cast(d as INT64) FROM tmp_table

