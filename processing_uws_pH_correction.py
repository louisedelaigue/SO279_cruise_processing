import pandas as pd, numpy as np
import PyCO2SYS as pyco2
from scipy.interpolate import PchipInterpolator

# Import UWS continuous pH data
df = pd.read_csv('./data/processing/raw_uws_data.csv')

# Import subsamples
subsamples = pd.read_csv('./data/processing/internal_subsamples_data.csv')

# === FAST INCREASES PROCESSING
# Cut continuous pH data to remove fast, unrealistic pH increases at the 
# beginning of each PyroScience file (beyond 20 min stablization, which was cut off during the initial raw processing)
# File #2
L = (df['filename'] == '2020-12-11_163148_NAPTRAM2020') & (df['sec'] < 3000) & (df['pH_insitu_ta_est'] < 8.094)
df = df[~L]

# File #3
L = (df['filename'] == '2020-12-15_214136_NAPTRAM20202') & (df['sec'] < 20000) & (df['pH_insitu_ta_est'] < 8.11) # 8.1125) #& (df['pH_insitu_ta_est'] > 8.0879)
df = df[~L]

# File #4
L = (df['filename'] == '2020-12-17_134828_NAPTRAM20203') & (df['sec'] < 6500)
df = df[~L]

# File 5
L = (df['filename'] == '2020-12-20_182318_NAPTRAM20205') & (df['sec'] < 10000) & (df['pH_insitu_ta_est'] < 8.105)
df = df[~L]

# Convert columns to datetime objects
df['date_time'] = pd.to_datetime(df['date_time'])
subsamples['date_time'] = pd.to_datetime(subsamples['date_time'])

# === SUBSAMPLES AND CONTINUOUS pH MATCH
# Reindex subsamples to match continuous pH data based on datetime
nearest = df.set_index('date_time').reindex(subsamples.set_index('date_time').index, method='nearest').reset_index()

# Add continuous pH data points corresponding to subsamples
# based on date and time
point_location = subsamples['date_time'].tolist()
subsamples['pH_optode'] = np.nan
for location in point_location:
    subsamples.loc[subsamples['date_time']==location, 'pH_optode'] = subsamples['date_time'].map(nearest.set_index('date_time')['pH_insitu_ta_est'])

# === pH CALCULATION AND CONVERSION
# Calculate subsamples pH(TA/DIC) at insitu temperature and pressure
subsamples['pH_total_talk_tco2_insitu_temp'] = pyco2.sys(
    subsamples.talk,
    subsamples.tco2,
    1,
    2,
    salinity=subsamples.salinity,
    temperature_out=subsamples.temperature,
    pressure_out=3,
    total_phosphate=subsamples.total_phosphate,
    total_silicate=subsamples.total_silicate,
)['pH_total_out']

# Recalculate pH(initial_talk) at insitu temperature and pressure
# using TA and DIC 
# and convert from free scale to total scale
subsamples['pH_total_initial_talk_tco2_insitu_temp'] = pyco2.sys(
    subsamples.pH_initial_talk,
    subsamples.tco2,
    3,
    2,
    opt_pH_scale=3,
    salinity=subsamples.salinity,
    temperature_out=subsamples.temperature,
    pressure_out=3,
    total_phosphate=subsamples.total_phosphate,
    total_silicate=subsamples.total_silicate,
)['pH_total_out']

# === pH OFFSET CALCULATION
# Calculate offset between pH(TA/DIC) and pH(initial_talk)
subsamples['offset'] = abs(subsamples['pH_total_talk_tco2_insitu_temp'] - subsamples['pH_total_initial_talk_tco2_insitu_temp'])
offset = subsamples['offset'].mean()
subsamples['pH_initial_talk_corr'] = subsamples['pH_total_initial_talk_tco2_insitu_temp'] + offset

# Subtract pH(initial_talk, corr) from pH(optode)
subsamples['diff'] = abs(subsamples['pH_initial_talk_corr'] - subsamples['pH_optode'])

# Remove where above difference is nan (PCHIP requirement)
L = subsamples['diff'].isnull()
subsamples = subsamples[~L]

# PCHIP difference points over date_time range in df
subsamples.sort_values(by=['diff'], ascending=True)
interp_obj = PchipInterpolator(subsamples['date_time'], subsamples['diff'], extrapolate=False)
df['pchip_pH_difference'] = interp_obj(df['date_time'])

# === CORRECTION OF pH CONTINUOUS DATA
# Correct pH(optode) using PCHIP values
df['pH_optode_corrected'] = df['pH_insitu_ta_est'] - df['pchip_pH_difference']

# Remove datapoints before first subsamples for file #5
L = (df['filename'] == '2020-12-20_182318_NAPTRAM20205') & (df['pH_optode_corrected'] < 8.07278)
df = df[~L]

# === SIMPLE MOVING AVERAGE
# Compute simple moving average (SMA) over period of 30 minutes
file_list = df['filename'].unique().tolist()
for file in file_list:
    df.loc[df['filename']==file, 'SMA'] = df.loc[df['filename']==file, 'pH_optode_corrected'].rolling(60, min_periods=1).mean()

# Save UWS continuous pH dataset
df.to_csv('./data/processing/processed_uws_data.csv', index=False)
subsamples.to_csv('./data/processing/subsamples_pH_correction.csv', index=False)
