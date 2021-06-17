import pandas as pd
import re

def converter(lat_or_lon):
    """Convert coordinates from degrees to decimals."""
    deg, minutes, seconds, direction =  re.split('[°\.\'\"]', lat_or_lon)
    ans = (
        (float(deg) + float(minutes)/60) + float(seconds)/(60*60)
    ) * (-1 if direction in ['W', 'S'] else 1)
    return pd.Series({
        'decimals': ans
        })