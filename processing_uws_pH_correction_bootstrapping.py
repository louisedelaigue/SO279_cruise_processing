import pandas as pd
import numpy as np
from scipy.interpolate import PchipInterpolator
import PyCO2SYS as pyco2 
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('./data/processing/raw_uws_data.csv')
subsamples = pd.read_csv('./data/processing/internal_subsamples_data.csv')

# Convert date_time columns to datetime objects for both datasets
df['date_time'] = pd.to_datetime(df['date_time'])
subsamples['date_time'] = pd.to_datetime(subsamples['date_time'])

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

# === Initial pH Correction with All Subsamples ===
# Match continuous pH data to the closest subsample
nearest = df.set_index('date_time').reindex(subsamples.set_index('date_time').index, method='nearest').reset_index()
subsamples['pH_optode'] = nearest['pH_insitu_ta_est'].values

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

# Calculate offset between pH(TA/DIC) and pH(initial_talk), then correct pH
subsamples['offset'] = abs(subsamples['pH_total_talk_tco2_insitu_temp'] - subsamples['pH_total_initial_talk_tco2_insitu_temp'])
overall_mean_offset = subsamples['offset'].mean()
subsamples['pH_initial_talk_corr'] = subsamples['pH_total_initial_talk_tco2_insitu_temp'] + overall_mean_offset

# Calculate the difference (offset) between corrected initial talk pH and pH measured by optode
subsamples['diff'] = abs(subsamples['pH_initial_talk_corr'] - subsamples['pH_optode'])

# Ensure 'diff' contains only finite values before interpolation
subsamples = subsamples[np.isfinite(subsamples['diff'])]

# Use all subsamples to interpolate a correction for the entire dataset
interp = PchipInterpolator(subsamples['date_time'].astype(np.int64), subsamples['diff'], extrapolate=True)
df['pchip_pH_difference'] = interp(df['date_time'].astype(np.int64))

# Apply the interpolated correction
df['pH_optode_corrected'] = df['pH_insitu_ta_est'] - df['pchip_pH_difference']

# === Bootstrapping for Uncertainty Estimation ===
n_iterations = 100
fraction_to_omit = 0.5
bootstrapped_pH_values = []

for iteration in range(n_iterations):
    # Randomly sample a subset of subsamples
    bootstrapped_subsamples = subsamples.sample(frac=1 - fraction_to_omit, replace=True)
    
    # Ensure 'diff' contains only finite values before interpolation
    bootstrapped_subsamples = bootstrapped_subsamples[np.isfinite(bootstrapped_subsamples['diff'])]
    
    # Sort by 'date_time' to ensure strictly increasing sequence
    bootstrapped_subsamples = bootstrapped_subsamples.sort_values(by='date_time')
    
    # Check for strictly increasing 'date_time' by ensuring no duplicates
    # This step is optional if you are certain your 'date_time' values are unique
    bootstrapped_subsamples = bootstrapped_subsamples.drop_duplicates(subset='date_time', keep='first')
    
    # Proceed if there are enough points for interpolation
    if len(bootstrapped_subsamples) > 1:
        # Interpolate the correction using the bootstrapped subsamples
        interp = PchipInterpolator(bootstrapped_subsamples['date_time'].astype(np.int64), bootstrapped_subsamples['diff'], extrapolate=False)
        df['pchip_pH_difference_temp'] = interp(df['date_time'].astype(np.int64))
        
        # Temporarily corrected pH values for this bootstrapped iteration
        df['pH_optode_corrected_temp'] = df['pH_insitu_ta_est'] - df['pchip_pH_difference_temp']
        
        # Store the bootstrapped corrected pH values
        bootstrapped_pH_values.append(df['pH_optode_corrected_temp'].values)

# Calculate uncertainty as the standard deviation across bootstrapped iterations
pH_uncertainty = np.std(bootstrapped_pH_values, axis=0)

# Add uncertainty to the dataframe
df['pH_uncertainty'] = pH_uncertainty

# === SIMPLE MOVING AVERAGE
# Compute simple moving average (SMA) over period of 30 minutes
df["SMA"] = df["pH_optode_corrected"].rolling(60, min_periods=1).mean()
df["SMA_uncertainty"] = df["pH_uncertainty"].rolling(60, min_periods=1).mean()

# Save the results
# df.to_csv('./data/processing/processed_uws_data_with_uncertainty.csv', index=False)
# subsamples.to_csv('./data/processing/subsamples_pH_correction_with_uncertainty.csv', index=False)

print("Processing and uncertainty estimation completed.")

# Create plot
fig, ax = plt.subplots(figsize=(6, 4), dpi=300)

# Plotting the uncorrected and corrected pH values along with uncertainties
L = df["SMA"].notnull()
ax.scatter(df["date_time"][L], df["pH_insitu_ta_est"][L], s=0.1, label="Uncorrected pH", color='xkcd:light pink', alpha=0.6)
ax.scatter(df["date_time"][L], df["SMA"][L], s=0.1, label="Corrected pH", color='b', alpha=0.6)
ax.fill_between(df["date_time"][L], df["SMA"][L] - df["SMA_uncertainty"][L], df["SMA"][L] + df["SMA_uncertainty"][L], color='b', alpha=0.2)
ax.scatter(subsamples["date_time"], subsamples["pH_initial_talk_corr"], color='k', label='Subsamples $pH_{TA/DIC}$', s=20, alpha=0.6, edgecolor='k', zorder=6)

# Improve plot aesthetics
ax.set_ylabel("$pH_{total}$")
ax.set_ylim(8.05, 8.2)
ax.grid(alpha=0.3)
fig.autofmt_xdate()

# Add a legend with custom marker sizes
handles, labels = ax.get_legend_handles_labels()
custom_handles = [
    plt.Line2D([], [], marker='o', color='w', label='Uncorrected pH', markersize=6, markerfacecolor='xkcd:light pink'),
    plt.Line2D([], [], marker='o', color='w', label='Corrected pH', markersize=6, markerfacecolor='b'),
] + handles[2:]  # Append other handles without modification
legend = ax.legend(handles=custom_handles, loc="upper left")

plt.show()

