from m5stack import *
from m5stack_ui import *
from uiflow import *
import ntptime
import time
import unit


screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xFFFFFF)
gps_0 = unit.get(unit.GPS, unit.PORTC)
ntp = ntptime.client(host='cn.pool.ntp.org', timezone=2)


label0 = M5Label('label0', x=50, y=36, color=0x000, font=FONT_MONT_14, parent=None)
label1 = M5Label('label1', x=50, y=65, color=0x000, font=FONT_MONT_14, parent=None)
label2 = M5Label('label2', x=51, y=154, color=0x000, font=FONT_MONT_14, parent=None)
label3 = M5Label('label3', x=110, y=154, color=0x000, font=FONT_MONT_14, parent=None)
label4 = M5Label('label4', x=174, y=154, color=0x000, font=FONT_MONT_14, parent=None)
label5 = M5Label('label5', x=234, y=153, color=0x000, font=FONT_MONT_14, parent=None)

month = str(ntp.month())
day = str(ntp.day())
label2.set_text(month)
label3.set_text(day)
    
with open('/sd/gps_test_b.csv', 'a') as fs:
  while True:
    lat = str(gps_0.latitude_decimal)
    lon = str(gps_0.longitude_decimal)
    hour = str(ntp.hour())
    minute = str(ntp.minute())
    label0.set_text(str(lat))
    label1.set_text(str(lon))
    label4.set_text(str(hour))
    label5.set_text(str(minute))
    fs.write(lat + ';' + lon + ';' + hour + ';' + minute)
    fs.write('\n')
    fs.flush()
    wait(10)