from db import Database
from billing import calculate_bill, generate_invoice
from vehicle_map import VEHICLE_TO_SLOT
from datetime import datetime

db = Database()

def handle_entry(plate, vehicle_type=None):
    """
    Reserve slot and insert parking record.
    Returns status dict with 'slot' when success.
    """
    if not plate:
        return {'status': "error", "message": "empty_plate"}


    active = db.get_active_entry(plate)
    if active:

        return {"status": "exists", "message": "already_inside", "slot": active["slot"]}

    vtype = (vehicle_type or "family_sedan").lower()
    preferred_size = VEHICLE_TO_SLOT.get(vtype, "medium")

    slot = db.find_and_reserve_slot(preferred_size, plate)
    if not slot:

        slot = db.reserve_any_slot(plate)

    if not slot:
        return {"status": "full", "message": "no_slot_available"}


    db.insert_entry(plate, vtype, slot)
    return {"status": "ok", "message": "entry_recorded", "slot": slot, "vehicle_type": vtype}


def handle_exit(plate):
    """
    Release slot, compute bill, update record, return invoice path & slot released.
    """
    if not plate:
        return {'status': "error", "message": "empty_plate"}

    active = db.get_active_entry(plate)
    if not active:
        return {"status": "not_found", "message": "no_active_entry"}

    entry_time = active["entry_time"]
    vehicle_type = active["vehicle_type"] or "family_sedan"
    slot = active["slot"]

    minutes, amount = calculate_bill(entry_time)
    db.close_parking(plate, minutes, amount)

    released_slot = None
    if slot:
        released_slot = db.release_slot_by_plate(plate)

    exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    invoice_path = generate_invoice(plate, entry_time, exit_time, minutes, amount, vehicle_type)
    return {"status": "ok", "message": "exit_recorded", "minutes": minutes, "amount": amount,
            "invoice": invoice_path, "slot_released": released_slot, "vehicle_type": vehicle_type}
