import pandas as pd

# Import CTD data 
df = pd.read_csv('./data/processing/processed_vindta_subsamples.csv')

# Add EXPOCODE column
df['EXPOCODE'] = '06SN20201204'

# Add cruise ID column
df['Cruise_ID'] = 'SO279'

# Convert date column to datetime object
df['date_time'] = pd.to_datetime(df['date_time'])

# Add year, month, day and time columns
df['Year_UTC'] = df['date_time'].dt.year
df['Month_UTC'] = df['date_time'].dt.month
df['Day_UTC'] = df['date_time'].dt.day
df['Time_UTC'] = df['date_time'].dt.time

# Save as is for internal use
df.to_csv('./data/processing/internal_subsamples_data.csv', index=False)

# Drop useless columns
columns = [
    'date_time',
    'internal_flag_tco2',
    'duplicate_difference_tco2',
    'n_duplicates_tco2',
    'internal_flag_talk',
    'duplicate_difference_talk',
    'n_duplicates_talk',
    'pH_initial_talk'
    ]
df.drop(columns, axis =1, inplace=True)

# Replace nans by conventional '-999'
df.fillna(-999, inplace=True)

# Rename date column
rn = {
    'sample':'Sample_ID',
    'latitude':'Latitude',
    'longitude':'Longitude',
    'depth':'Depth',
    'salinity':'Salinity',
    'salinity_flag':'Salinity_flag',
    'temperature':'Temperature',
    'total_phosphate':'Phosphate',
    'total_silicate':'Silicate',
    'total_ammonium':'Ammonium',
    'total_nitrate_nitrite':'Nitrate_and_Nitrite',
    'total_nitrite':'Nitrite',
    'total_nitrate':'Nitrate',
    'talk':'TA',
    'flag_talk':'TA_flag',
    'tco2':'DIC',
    'flag_tco2':'DIC_flag',
      }

df.rename(rn, axis=1, inplace=True)

# Reorder columns
new_index = [
    'EXPOCODE',
    'Cruise_ID',
    'Sample_ID',
    'Year_UTC',
    'Month_UTC',
    'Day_UTC',
    'Time_UTC',
    'Latitude',
    'Longitude',
    'Depth',
    'Temperature',
    'Salinity',
    'Salinity_flag',
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
    'Ammonium_flag',
    ]
df = df.reindex(new_index, axis=1)

# Sort by sample number
df.sort_values(by=['Sample_ID'], inplace=True)

# Save subsamples dataset to csv
df.to_csv('./data/SO279_UWS_discrete_samples.csv', index=False)
