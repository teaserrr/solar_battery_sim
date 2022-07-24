# solar_battery_sim
Simulates solar battery level based on actual energy usage report from 'My Fluvius'

# Usage

Go to 'My fluvius' and in the 'electricity' area, click 'show usage':
![image](https://user-images.githubusercontent.com/34370173/180648656-1857830a-b2ff-4eca-9eaa-a9c43c779501.png)

Click 'download report':
![image](https://user-images.githubusercontent.com/34370173/180648611-e16d7816-e78b-48b6-a6e9-754357691a0e.png)

Select 'quarter of an hour' as detail level and select the desired time range:
![image](https://user-images.githubusercontent.com/34370173/180648727-c77860c9-0b01-446d-9ff8-b43d9743ecb5.png)

Run the script, use the location of the downloaded csv-file as the first argument, the battery capacity in kWh as the second argument and the maximum (dis)charge power in kW as the third.

```
usage: main.py [-h] csv_file capacity max_power

Simulates solar battery usage from actual usage data

positional arguments:
  csv_file    Exported usage data in csv format
  capacity    Maximum battery capacity in kWh
  max_power   Maximum charging/discharging power in kW

optional arguments:
  -h, --help  show this help message and exit
```

The output is also in csv format and contains the following data:
- timestamp in UTC
- duration (should be 15 min)
- actual extraction from the grid in kWh
- actual injection from the grid in kWh
- simulated battery level in kWh
- simulated extraction from the grid in kWh
- simulated injection from the grid in kWh
