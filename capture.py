#!/usr/bin/env python3
"""
capture.py -- Poll a Veeder-Root TLS-350 ATG over serial and write tank
inventory to a CSV. Per-store settings live in config.py.
"""

import serial
import re
import struct
import csv
import datetime
import time

import config

# Fixed serial framing for the TLS-350
BYTESIZE = serial.SEVENBITS
PARITY   = serial.PARITY_ODD
STOPBITS = serial.STOPBITS_ONE


# ------------------- Serial Fetching -------------------
def fetch_atg_data():
    """Send CTRL+A + COMMAND + TANK to the TLS-350 and read all data after a short pause."""
    try:
        ser = serial.Serial(
            config.SERIAL_PORT,
            baudrate=config.BAUDRATE,
            bytesize=BYTESIZE,
            parity=PARITY,
            stopbits=STOPBITS,
            timeout=config.TIMEOUT
        )
    except Exception as e:
        print(f"Failed to open {config.SERIAL_PORT}: {e}")
        return None

    # Build payload: start-of-header (CTRL+A) + command + tank number
    payload = bytes(config.COMMAND + config.TANK, 'utf-8')

    # Write CTRL+A + payload
    ser.write(b'\x01' + payload)

    # Attempt to read back the echoed command (not all devices echo fully)
    echoed = ser.read_until(payload, config.TIMEOUT)
    print("Echoed response:", repr(echoed.decode('utf-8', errors='ignore')))

    # Wait a bit to let the device send all data
    time.sleep(2)

    # Read whatever is in the buffer now
    data = ser.read_all()
    ser.close()

    # Decode the raw bytes to a string
    response = data.decode('utf-8', errors='ignore').strip()
    return response


# ------------------- Data Parsing -------------------
def ieee_to_float(hex_str):
    """Convert an 8-character hex string to a float (IEEE 754 format)."""
    try:
        return struct.unpack('>f', bytes.fromhex(hex_str))[0]
    except Exception:
        return 0.0


def ieee_to_rounded_float(hex_str, decimals=1):
    """Convert hex to float and round to the specified decimals."""
    f = ieee_to_float(hex_str)
    return round(f, decimals)


def ullage_90(volume, ullage_full):
    """
    Ullage required to reach 90% full:
        0.90 * (volume + ullage_full) - volume
    Clamped to >= 0.
    """
    val = 0.90 * (volume + ullage_full) - volume
    return max(0.0, val)


def parse_tank_data(response):
    """Extract tank data using a regex pattern that expects a 56-hex string after '07'."""
    if not response:
        return []

    # Print the full raw response for debugging
    print("Raw response:", repr(response))

    # If the response is short, it's probably not the expected data
    if len(response) < 60:
        print("Response is too short to contain valid tank data.")
        return []

    # Pattern: (2 digits)(1 char)(4 digits)07(56 hex)... (& or && optional)
    data = response
    pattern = re.compile(r'(\d{2})(.)(\d{4})07([0-9A-Fa-f]{56})&{0,2}')
    tanks = []
    for match in pattern.finditer(data):
        tank_id, product, _, hex_fields = match.groups()
        hex_data = hex_fields[:56]
        fields = [hex_data[i:i+8] for i in range(0, 56, 8)]

        # original fields
        volume      = ieee_to_float(fields[0])
        tc_volume   = ieee_to_float(fields[1])
        ullage_full = ieee_to_float(fields[2])          # space to 100%
        height      = ieee_to_rounded_float(fields[3])
        water       = ieee_to_rounded_float(fields[4])
        temp        = ieee_to_float(fields[5])

        # Ullage reported = 90% ullage
        ull90 = int(round(ullage_90(volume, ullage_full)))

        tank = {
            'Tank': tank_id,
            'Product': config.PRODUCT_MAP.get(product, 'UNKNOWN'),
            'Volume': int(round(volume)),
            'TC Volume': int(round(tc_volume)),
            'Ullage': ull90,                     # 90% ullage only
            'Height': height,
            'Water': water,
            'Temp': int(round(temp))
        }
        tanks.append(tank)
    return tanks


# ------------------- CSV Export -------------------
def write_csv(tanks, filename):
    if not tanks:
        print("No data to export.")
        return

    headers = ['Tank', 'Product', 'Volume', 'TC Volume', 'Ullage', 'Height', 'Water', 'Temp', 'Time']
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for tank in tanks:
            # Format Height and Water to one decimal place
            tank['Height'] = f"{tank['Height']:.1f}"
            tank['Water'] = f"{tank['Water']:.1f}"
            writer.writerow(tank)
    print(f"CSV saved to {filename}")


# ------------------- Main -------------------
if __name__ == "__main__":
    response = fetch_atg_data()
    if not response:
        print("No response received from device.")
        exit()

    # Parse the data
    tanks = parse_tank_data(response)

    # If parsing succeeded, add a timestamp and write to CSV
    if tanks:
        capture_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for tank in tanks:
            tank['Time'] = capture_time
        write_csv(tanks, config.CSV_PATH)
