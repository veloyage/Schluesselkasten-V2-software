# Example usage with SMBus
from smbus2 import SMBus
import bq25628
import time

# Initialize the I2C bus
bus = SMBus(1)  # Use 1 for Raspberry Pi /dev/i2c-1

# Create BQ25628 object
bq = bq25628.BQ25628(bus)

# Set charge voltage to 4000mV
bq.set_charge_voltage(4000)

# Set charge current to 1000mA
bq.set_charge_current(1000)

# Read status
status = bq.get_charger_status()
print(f"Charger status: {status}")

# Read ADC values
bq.enable_adc(True)

while True:
    adc_values = bq.read_adc_values()
    print(f"ADC values: {adc_values}")
    time.sleep(1)