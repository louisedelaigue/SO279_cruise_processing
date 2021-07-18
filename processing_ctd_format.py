import pandas as pd, numpy as np

# Import CTD data 
df = pd.read_csv('./data/processing/processed_vindta_ctd.csv')

# Import Latitude/Longitude and CTD date from cruise report and add it to dataset
# File 'SO279_GPF_20-3_089_SCR.pdf'
coordinates = pd.read_csv('./data/other/stations_coordinates_decimals.csv')
coordinates['station'] = coordinates['station'].astype(int)
df['date'] = np.nan
df['latitude'] = np.nan
df['longitude'] = np.nan

stations_list = df['station'].unique().tolist()
for station in stations_list:
    df.loc[df['station']==station, 'date'] = coordinates.loc[coordinates['station']==station, 'date'].item()
    df.loc[df['station']==station, 'latitude'] = coordinates.loc[coordinates['station']==station, 'lat'].item()
    df.loc[df['station']==station, 'longitude'] = coordinates.loc[coordinates['station']==station, 'lon'].item()

# Add EXPOCODE column
df['EXPOCODE'] = '06SN20201204'

# Add cruise ID column
df['Cruise_ID'] = 'SO279'

# Add cast number column
df['Cast_number'] = 1

# Convert date column to datetime object
df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M')
# df['date'] = df['date'].dt.strftime('%Y-%d-%m H%:M%:S%')

# Add year, month, day and time columns
df['Year_UTC'] = df['date'].dt.year
df['Month_UTC'] = df['date'].dt.month
df['Day_UTC'] = df['date'].dt.day
df['Time_UTC'] = df['date'].dt.time

# Drop date column
columns = [
    'date',
    'pH_initial_talk'
    ]
df.drop(columns, axis =1, inplace=True)

# Rename columns with names according to best practices
rn = {
    'station':'Station_ID',
    'latitude':'Latitude',
    'longitude':'Longitude',
    'station':'Station_ID',
    'niskin':'Niskin_ID',
    'pressure':'CTDPRES',
    'depth':'Depth',
    'salinity':'CTDSAL_PSS78',
    'temperature':'CTDTEMP_ITS90',
    'total_phosphate':'Phosphate',
    'total_silicate':'Silicate',
    'total_ammonium':'Ammonium',
    'total_nitrate_nitrite':'Nitrate_and_Nitrite',
    'total_nitrite':'Nitrite',
    'total_nitrate':'Nitrate',
    'talk':'TA',
    'flag_talk':'TA_flag',
    # 'duplicate_difference_talk',
    # 'n_duplicates_talk',
    'tco2':'DIC',
    'flag_tco2':'DIC_flag',
    # 'duplicate_difference_tco2',
    # 'n_duplicates_tco2',
      }
df.rename(rn, axis=1, inplace=True)

# Reorder columns
new_index = [
    'EXPOCODE',
    'Cruise_ID',
    'Station_ID',
    'Cast_number',
    'Niskin_ID',
    'Year_UTC',
    'Month_UTC',
    'Day_UTC',
    'Time_UTC',
    'Latitude',
    'Longitude',
    'CTDPRES',
    'Depth',
    'CTDTEMP_ITS90',
    'CTDSAL_PSS78',
    'DIC',
    'DIC_flag',
    'TA',
    'TA_flag',
    'Silicate',
    'Silicate_flag',
    'Phosphate',
    'Phosphate_flag',
    'Nitrate',
    'Nitrate_flag',
    'Nitrite',
    'Nitrite_flag',
    'Nitrate_and_Nitrite',
    'Nitrate_and_Nitrite_flag',
    'Ammonium',
    'Ammonium_flag'
    ]
df = df.reindex(new_index, axis=1)


# Replace nans by conventional '-9999'
df.fillna(-999, inplace=True)

# Save CTD dataset to csv
df.to_csv('./data/SO279_CTD_discrete_samples.csv', index=False)