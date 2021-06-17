import pandas as pd, numpy as np
import re

# Import coordinates data
coordinates = pd.read_excel('./data/other/stations_coordinates_degrees.xlsx')

# Remove spaces within Latitude/Longitude strings
coordinates['lat_deg'] = coordinates['lat_deg'].apply(lambda x: ''.join(filter(None, x.split(' '))))
coordinates['lon_deg'] = coordinates['lon_deg'].apply(lambda x: ''.join(filter(None, x.split(' '))))

# Create function for coordinate conversion
def dms_to_dd(lat_or_lon):
    """Convert coordinates from degrees to decimals."""
    deg, minutes, seconds, direction =  re.split('\°|\.|\'', str(lat_or_lon))
    ans = (
        (float(deg) + float(minutes)/60) + float(seconds)/(60*60)
    ) * (-1 if direction in ['W', 'S'] else 1)
    return pd.Series({
        'decimals': ans
        })

# Convert coordinates from degrees to decimals
coordinates['lat'] = np.nan
coordinates['lon'] = np.nan
coordinates['lat'] = coordinates['lat_deg'].apply(dms_to_dd)
coordinates['lon'] = coordinates['lon_deg'].apply(dms_to_dd)

# Drop degree coordinates
coordinates.drop('lat_deg', axis=1, inplace=True)
coordinates.drop('lon_deg', axis=1, inplace=True)

# Save coordinates to csv
coordinates.to_csv('./data/other/stations_coordinates_decimals.csv', index=False)
