from datetime import datetime

PEAK_HOURS = {6, 7, 8, 9, 18, 19, 20, 21}
NORMAL_HOURS = set(range(10, 18))
OFF_PEAK_PRICE = 3
NORMAL_PRICE = 7
PEAK_PRICE = 12
FLAT_RATE = 7


def grid_price(hour):
    if hour in PEAK_HOURS:
        return PEAK_PRICE, "Peak"
    if hour in NORMAL_HOURS:
        return NORMAL_PRICE, "Normal"
    return OFF_PEAK_PRICE, "Off-Peak"


def current_grid_tier():
    hour = datetime.now().hour
    price, period = grid_price(hour)
    return {"price": price, "period": period, "hour": hour}
