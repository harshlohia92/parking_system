from datetime import datetime
import os

RATE_PER_MINUTE = 2
MINIMUM_CHARGE_MINUTES = 1

def calculate_bill(entry_time_str):
    entry = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    diff = now - entry
    minutes = max(MINIMUM_CHARGE_MINUTES, int(diff.total_seconds() // 60) + 1)
    amount = minutes * RATE_PER_MINUTE
    return minutes, amount

def generate_invoice(plate, entry_time, exit_time, minutes, amount, vehicle_type="unknown", out_folder="output"):
    os.makedirs(out_folder, exist_ok=True)
    filename = os.path.join(out_folder, f"invoice_{plate}_{exit_time.replace(' ', '_').replace(':','')}.txt")
    with open(filename, "w") as f:
        f.write("===== PARKING INVOICE =====\n")
        f.write(f"Plate: {plate}\n")
        f.write(f"Vehicle Type: {vehicle_type}\n")
        f.write(f"Entry: {entry_time}\n")
        f.write(f"Exit : {exit_time}\n")
        f.write(f"Duration (min): {minutes}\n")
        f.write(f"Amount: ₹{amount}\n")
        f.write("===========================\n")
    return filename
