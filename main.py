#!/usr/bin/python

import csv
import argparse
import locale

import pytz

from datetime import datetime, timedelta
from pytz.exceptions import AmbiguousTimeError


csv_fields = [
    'Van Datum',
    'Van Tijdstip',
    'Tot Datum',
    'Tot Tijdstip',
    'EAN',
    'Meter',
    'Metertype',
    'Register',
    'Volume',
    'Eenheid',
    'Validatiestatus'
]

timezone = pytz.timezone('Europe/Brussels')


class UsageData:
    def __init__(self, start_time, duration, extraction, injection):
        self.start_time = start_time
        self.duration = duration
        self.extraction = extraction
        self.injection = injection

    def __str__(self):
        return 'start_time: {} duration: {} extraction: {} injection: {}'.format(
            self.start_time, self.duration, self.extraction, self.injection)


class SimulationData:
    def __init__(self, usage_data: UsageData, battery_level, extraction, injection):
        self.usage_data = usage_data
        self.battery_level = battery_level
        self.extraction = extraction
        self.injection = injection

    def __str__(self):
        return '{} battery_level: {} extraction: {} injection: {}'.format(
            self.usage_data, self.battery_level, self.extraction, self.injection)


def import_usage_history(csv_file):
    records = _import_file(csv_file)
    duration = None
    i = 0
    while i < len(records):
        assert records[i]['from_datetime'] == records[i+1]['from_datetime']
        assert records[i]['injection'] is not records[i+1]['injection']
        start_time = records[i]['from_datetime']

        if not duration:
            duration = records[i+2]['from_datetime'] - start_time if i+2 < len(records) else None

        extraction = records[i]['value'] if not records[i]['injection'] else records[i+1]['value']
        injection = records[i]['value'] if records[i]['injection'] else records[i + 1]['value']
        yield UsageData(start_time, duration, extraction, injection)
        i += 2


def _import_file(csv_file):
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';', skipinitialspace=True)
        return [_parse_record(row[csv_fields[0]], row[csv_fields[1]], row[csv_fields[7]], row[csv_fields[8]]) for row in reader]


def _parse_record(from_date, from_time, type, volume):
    from_datetime = _get_utc_datetime(from_date, from_time)
    injection = type.startswith('Inject')
    try:
        value = float(volume.replace(',', '.'))
    except ValueError:
        value = 0.0
    return {'from_datetime': from_datetime, 'value': value, 'injection': injection}


# HACK
# The Fluvius export is local time so when switching from DST to non-DST, timestamps between 1:00 and 2:00 appear
# twice in the list. On top of that, the order of the records is incorrect so we always have 2 records (extraction and
# injection) in DST time, followed by 2 records with the same timestamp but non-DST. The counter below will count to 2,
# then reset to -2. When the counter is > 0, the timestamp is parsed as DST, otherwise as non-DST
dst_counter = 0


def _get_utc_datetime(date, time):
    naive = datetime.strptime('{} {}'.format(date, time), '%d-%m-%Y %H:%M:%S')
    try:
        local_dt = timezone.localize(naive, is_dst=None)
    except AmbiguousTimeError:
        global dst_counter
        dst_counter += 1
        local_dt = timezone.localize(naive, is_dst=(dst_counter > 0))
        if dst_counter == 2:
            dst_counter -= 4
    return local_dt.astimezone(pytz.utc)


def _calc_max_energy(duration, max_power):
    return max_power * duration / timedelta(hours=1)


def _calc_discharge(energy_delta, duration, battery_level, max_power):
    max_discharge = _calc_max_energy(duration, max_power)
    discharge = min(energy_delta, battery_level, max_discharge)
    return discharge


def _calc_charge(energy_delta, duration, battery_level, battery_capacity, max_power):
    max_charge = _calc_max_energy(duration, max_power)
    charge = min(energy_delta, battery_capacity-battery_level, max_charge)
    return charge


def simulate(usage_data, battery_capacity, max_power, roundtrip_efficiency=0.9):
    efficiency = 1-(1-roundtrip_efficiency)/2
    prev_simulation_data = SimulationData(None, 0, 0, 0)
    for usage_record in usage_data:
        energy_delta = usage_record.extraction - usage_record.injection
        if energy_delta > 0:
            discharge = _calc_discharge(energy_delta, usage_record.duration, prev_simulation_data.battery_level, max_power)
            new_charge = prev_simulation_data.battery_level - discharge
            extraction = energy_delta - discharge * efficiency
            injection = 0
        else:
            charge = _calc_charge(-energy_delta, usage_record.duration, prev_simulation_data.battery_level, battery_capacity, max_power)
            new_charge = prev_simulation_data.battery_level + charge * efficiency
            extraction = 0
            injection = -energy_delta - charge

        prev_simulation_data = SimulationData(usage_record, new_charge, extraction, injection)
        yield prev_simulation_data


def _process_results(results, csv_writer, summary, price_extraction, price_injection):
    actual_injection = 0
    actual_extraction = 0
    actual_total_cost = 0
    simulated_injection = 0
    simulated_extraction = 0
    simulated_total_cost = 0

    simulate_cost = summary and price_extraction is not None and price_injection is not None
    locale.setlocale(locale.LC_ALL, '')
    curr = locale.localeconv().get('currency_symbol')

    if csv_writer:
        csv_writer.writerow(['start_time', 'duration', 'extraction', 'injection', 'battery_level', 'new_extraction', 'new_injection'])

    for r in results:
        u = r.usage_data
        if csv_writer:
            csv_writer.writerow([u.start_time, u.duration, u.extraction, u.injection, r.battery_level, r.extraction, r.injection])

        if summary:
            actual_extraction += u.extraction
            actual_injection += u.injection
            simulated_extraction += r.extraction
            simulated_injection += r.injection

        if simulate_cost:
            actual_total_cost += u.extraction * price_extraction - u.injection * price_injection
            simulated_total_cost += r.extraction * price_extraction - r.injection * price_injection

    if summary:
        print(f"Simulated saved extraction: {actual_extraction-simulated_extraction:.2f}kWh "
              f"(actual extraction: {actual_extraction:.2f}kWh, simulated extraction: {simulated_extraction:.2f}kWh")
        print(f"Simulated saved injection: {actual_injection-simulated_injection:.2f}kWh "
              f"(actual injection: {actual_injection:.2f}kWh, simulated injection: {simulated_injection:.2f}kWh")
    if simulate_cost:
        print(f"Simulated savings: {actual_total_cost-simulated_total_cost:.2f}{curr} "
              f"(actual cost: {actual_total_cost:.2f}{curr}, simulated cost: {simulated_total_cost:.2f}{curr})")


def main():
    parser = argparse.ArgumentParser(description='Simulates solar battery usage from actual usage data')
    parser.add_argument('csv_file', type=str, help='Exported usage data in csv format')
    parser.add_argument('capacity', type=float, help='Maximum battery capacity in kWh')
    parser.add_argument('max_power', type=float, help='Maximum charging/discharging power in kW')
    parser.add_argument('-o', '--output-file', type=str, default=None, help='Path to the output file')
    parser.add_argument('-s', '--summary', action='store_true', default=False, help='Print a summary')
    parser.add_argument('-e', '--efficiency', type=float, default=0.9, help='Roundtrip efficiency, expects a number from 0-1. '
                                                                            'Default 0.9, corresponding with 90% efficiency.')
    parser.add_argument('--price-extraction', type=float, default=None, help='Price for extracting energy from the grid in €/kWh')
    parser.add_argument('--price-injection', type=float, default=None, help='Price for injecting energy into the grid in €/kWh')
    args = parser.parse_args()

    records = import_usage_history(args.csv_file)
    results = simulate(records, args.capacity, args.max_power, args.efficiency)

    price_extraction = args.price_extraction
    price_injection = args.price_injection
    output_file = args.output_file
    summary = args.summary

    if output_file:
        with open(output_file, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            _process_results(results, csv_writer, summary, price_extraction, price_injection)
    else:
        _process_results(results, None, summary, price_extraction, price_injection)


if __name__ == '__main__':
    main()