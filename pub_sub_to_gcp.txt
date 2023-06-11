from m5stack import *
from m5ui import *
from uiflow import *
from m5mqtt import M5mqtt

from m5stack_ui import *
import ntptime
import time
import unit


project_id = "serene-foundry-379413"
cloud_region = "europe-west1"
registry_id = "test_iot_data"
device_id = "test_device"
jwt = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE2ODMwNDEzNzIsImV4cCI6MTY4MzEwMTM3MiwiYXVkIjoic2VyZW5lLWZvdW5kcnktMzc5NDEzIn0.ttr1HSYW5SKLQ1G7bznUjgeFxJAsP3lfPJNYcwI3qiE0sTiwxwMepr3jxgLZQ_O6Jxl-toWzmOeCnKCIcJ8DyKeBWVD6g5tYg9KDc1vVhcFDSnGDrvXOAaTE0I2KnWaSJcGSDy3wg-6-fFW1qiC2q2yeidBnJPJyvZy53Pc-zHh17XEp3Bzct_QO9cPLBQw5a2uoVZoLHrLH4_Qq7cUKgHVbFkjwA4wr86I0fZUFjGj-K2gJ8cvXd4Vkm1DE9pv77dtvugY_G8V-V_K8XmzYB7Cw3FyK2NOpTrLIbBFJxIrdyjREA6wZQwN2pR9WmJ5viKo_HdCyOuQXPuqnWzor0A"
wifi_ssid="Moka"
wifi_password= "HomeGeranienstrasse10"


client_id = "projects/{}/locations/{}/registries/{}/devices/{}".format(
    project_id, cloud_region, registry_id, device_id
)

mqtt_topic = "/devices/{}/events".format(device_id)

mqtt_bridge_hostname='mqtt.googleapis.com'
mqtt_bridge_port = 8883


setScreenColor(0x222222)
label0 = M5TextBox(51, 101, "label0", lcd.FONT_Default, 0xFFFFFF, rotate=0)
label0.setText('Hello!')

gps_0 = unit.get(unit.GPS, unit.PORTC)
ntp = ntptime.client(host='cn.pool.ntp.org', timezone=2)


try:
  import network 
  sta_if = network.WLAN(network.STA_IF)
  if not sta_if.isconnected():
              label0.setText('Connecting to network...')
              wait(3)
              sta_if.active(True)
              sta_if.connect(
                  wifi_ssid, wifi_pwd)
  while not sta_if.isconnected():
    pass
  label0.setText('Connected')
  wait(3)
except:
  label0.setText('Error in connecting to Wifi')
  wait(3)


try:
  client = M5mqtt(
              client_id,
              mqtt_bridge_hostname,
              port=mqtt_bridge_port,
              user="unused",
              password=jwt,
              keepalive=300,
              ssl=True,
              ssl_params={"cert": "/flash/roots.pem"}
          )
          
  client.start()
  
  
  i = 0
  while True:
    payload = "{}, {},{}".format(gps_0.latitude_decimal, gps_0.longitude_decimal, ntp.getTimestamp())
    client.publish(mqtt_topic, payload, qos=1)
    label0.setText("payload number {} published".format(i))
    i += 1
    wait(10)
  

except:
  label0.setText('Error in connecting to mqtt')
  wait(3)





