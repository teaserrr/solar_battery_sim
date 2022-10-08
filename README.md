# solar_battery_sim
Simulates solar battery level based on actual energy usage report from 'My Fluvius'

# Usage

Go to 'My fluvius' and in the 'electricity' area, click 'show usage':
![image](https://user-images.githubusercontent.com/34370173/180648656-1857830a-b2ff-4eca-9eaa-a9c43c779501.png)

Click 'download report':
![image](https://user-images.githubusercontent.com/34370173/180648611-e16d7816-e78b-48b6-a6e9-754357691a0e.png)

Select 'quarter of an hour' as detail level and select the desired time range:
![image](https://user-images.githubusercontent.com/34370173/180648727-c77860c9-0b01-446d-9ff8-b43d9743ecb5.png)

Run the script:

```
usage: main.py [-h] [-o OUTPUT_FILE] [-s] [--price-extraction PRICE_EXTRACTION] [--price-injection PRICE_INJECTION] csv_file capacity max_power

Simulates solar battery usage from actual usage data

positional arguments:
  csv_file    Exported usage data in csv format
  capacity    Maximum battery capacity in kWh
  max_power   Maximum charging/discharging power in kW

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Path to the output file
  -s, --summary         Print a summary
  --price-extraction PRICE_EXTRACTION
                        Price for extracting energy from the grid in €/kWh
  --price-injection PRICE_INJECTION
                        Price for injecting energy into the grid in €/kWh

```

For example:
```commandline
./main.py Verbruikshistoriek_elektriciteit_541448820042152161_20211009_20221009_kwartiertotalen.csv 5 5 --price-extraction 0.5 --price-injection 0.2 -s -o results.csv
```
This will do a simulation for a 5kWh battery with 5kW charging/discharging power. It will also calculate your savings 
based on a cost of 50 cents per kWh for electricity you get from the grid and a price of 20 cents you get back when injecting
into the grid. It will output the detailed calculations to the file `results.csv` and print a summary:

```commandline
Simulated saved extraction: 1081.25kWh (actual extraction: 2302.22kWh, simulated extraction: 1220.97kWh
Simulated saved injection: 1083.72kWh (actual injection: 3713.63kWh, simulated injection: 2629.92kWh
Simulated savings: 323.88€ (actual cost: 408.38€, simulated cost: 84.50€)
```

The output file, if specified, is in csv format and contains the following data:
- timestamp in UTC
- duration (should be 15 min)
- actual extraction from the grid in kWh
- actual injection from the grid in kWh
- simulated battery level in kWh
- simulated extraction from the grid in kWh
- simulated injection from the grid in kWh
