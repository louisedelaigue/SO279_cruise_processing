import pandas as pd

# Import continuous pH data 
df = pd.read_csv('./data/processing/processed_uws_data.csv')

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

# Add flag column
df['pH_flag'] = 2

# Save as is for internal use
df.to_csv('./data/SO279_internal_UWS_data.csv', index=False)

# Drop useless columns
df.drop(columns=[
    'index',
    'date_time',
    'filename',
    'sec',
    'pH_cell',
    'temp_cell',
    'dphi',
    'signal_intensity',
    'ambient_light',
    'status_temp',
    'ldev',
    'status_ph',
    'WS_airtemp',
    'WS_baro',
    'WS_course',
    'WS_date',
    'WS_heading',
    'WS_humidity',
    'WS_lat',
    'WS_lon',
    'WS_longwave',
    'WS_normto',
    'WS_pyrogeometer',
    'WS_sensorvalue',
    'WS_sentence',
    'WS_shortwave',
    'WS_speed',
    'WS_timestamp',
    'WS_watertemp',
    'WS_winddirection_rel',
    'WS_winddirection_true',
    'WS_windspeed_rel',
    'WS_windspeed_true',
    'WS_windspeed_true_bft',
    'chl',
    'SBE_45_C',
    'date',
    'delay',
    'ew',
    'flow',
    'ns',
    'system',
    'smb_name',
    'sentence',
    'SMB.RSSMB.SMB_SN',
    'SBE45_sv',
    'SBE45_sal',
    'insitu_sv',
    'smb_status',
    'smb_sv_aml',
    'SBE45_water_temp',
    'smb_time',
    'smb_tur',
    'temp_diff',
    'pH',
    'pchip_salinity',
    'ta_est',
    'pH_insitu_ta_est',
    'pchip_pH_difference',
    'SMA'],
    axis=1,
    inplace=True)

# Rename columns
rn = {
      'lat':'Latitude',
      'lon':'Longitude',
      'depth':'Depth',
      'SBE38_water_temp':'Temperature',
      'salinity':'Salinity',
      'flag_salinity':'Salinity_flag',
      'pH_optode_corrected':'pH_TS_measured (optode)'
      }
df.rename(rn, axis=1, inplace=True)

# Drop rows where there is no pH corrected values
df = df[df['pH_TS_measured (optode)'].notna()]

# Replace nans by conventional '-999'
df.fillna(-999, inplace=True)

# Duplicate Temperature column
df['TEMP_pH'] = df['Temperature']

# Reorder columns
new_index = [
    'EXPOCODE',
    'Cruise_ID',
    'Year_UTC',
    'Month_UTC',
    'Day_UTC',
    'Time_UTC',
    'Latitude',
    'Longitude',
    'Depth',
    'Temperature',
    'TEMP_pH',
    'Salinity',
    'Salinity_flag',
    'pH_TS_measured (optode)',
    'pH_flag'
    
    ]
df = df.reindex(new_index, axis=1)

# Save subsamples dataset to csv
df.to_csv('./data/SO279_UWS_data.csv', index=False)
