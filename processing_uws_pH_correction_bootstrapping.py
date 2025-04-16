import pandas as pd, numpy as np
import PyCO2SYS as pyco2
from scipy.interpolate import PchipInterpolator
import matplotlib.pyplot as plt

# Import UWS continuous pH data
df = pd.read_csv('./data/processing/raw_uws_data.csv')

# Import subsamples
subsamples = pd.read_csv('./data/processing/processed_vindta_subsamples_with_uncertainty.csv')

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

# Bootstrap analysis for uncertainty estimation
n_iterations = 100
bootstrapped_ph_lists = []

for iteration in range(n_iterations):
    # Sample a fraction of the subsamples DataFrame
    sampled_subsamples = subsamples.sample(frac=0.5, replace=True)

    # Introduce variability within RMSE
    sampled_subsamples['pH_real_TA_tCO2_adjusted'] = sampled_subsamples['pH_real_TA_tCO2'] + np.random.normal(0, sampled_subsamples['RMSE_pH_TA_tCO2'], size=len(sampled_subsamples))
    sampled_subsamples['pH_real_initial_talk_tCO2_adjusted'] = sampled_subsamples['pH_real_initial_talk_tCO2'] + np.random.normal(0, sampled_subsamples['RMSE_pH_pH_initial_talk_tCO2'], size=len(sampled_subsamples))

    # Recalculate offsets and corrections
    sampled_subsamples['offset'] = abs(sampled_subsamples['pH_real_TA_tCO2_adjusted'] - sampled_subsamples['pH_real_initial_talk_tCO2_adjusted'])
    offset = sampled_subsamples['offset'].mean()
    sampled_subsamples['pH_real_initial_talk_tCO2_adjusted_corr'] = sampled_subsamples['pH_real_initial_talk_tCO2_adjusted'] + offset

    sampled_subsamples['diff'] = abs(sampled_subsamples['pH_real_initial_talk_tCO2_adjusted_corr'] - sampled_subsamples['pH_optode'])

    # Remove where above difference is nan (PCHIP requirement)
    sampled_subsamples = sampled_subsamples.dropna(subset=['diff'])

    # Interpolate using PCHIP
    # Drop duplicate timestamps
    sampled_subsamples = sampled_subsamples.drop_duplicates(subset='date_time')
    
    # Sort by date_time
    sampled_subsamples = sampled_subsamples.sort_values(by='date_time')

    interp_obj = PchipInterpolator(sampled_subsamples['date_time'], sampled_subsamples['diff'], extrapolate=False)
    df_iteration = df.copy()
    df_iteration['pchip_pH_difference'] = interp_obj(df_iteration['date_time'])
    df_iteration['pH_optode_corrected'] = df['pH_insitu_ta_est'] - df_iteration['pchip_pH_difference']

    # Append the series to the list
    bootstrapped_ph_lists.append(df_iteration['pH_optode_corrected'].rename(f'iteration_{iteration}'))

# Concatenate all data into the DataFrame at once after the loop
bootstrapped_ph_values = pd.concat(bootstrapped_ph_lists, axis=1)

# Compute mean and standard deviation of corrected pH values
df['pH_optode_corrected_RMSE'] = np.sqrt((bootstrapped_ph_values.subtract(df['pH_optode_corrected'], axis=0) ** 2).mean(axis=1))

# Save the DataFrame with corrected pH values and uncertainty
# df.to_csv('./data/processing/uws_data_with_corrected_pH.csv')
df.to_csv('./data/processing/processed_uws_data_with_uncertainty_bootstrapping.csv')

#%% === Plotting
# Create figure
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

# Plot uncorrected and corrected pH with simple moving average
L = df["pH_optode_corrected"].notnull()
df_filtered = df[L]

# Function to find gaps in datetime series
def find_gaps(data, threshold=60):
    gaps = np.where(np.diff(data) > np.timedelta64(threshold, 'm'))[0] + 1
    return gaps

# Split data into continuous segments
continuous_segments = np.split(df_filtered, find_gaps(df_filtered['date_time'].values))

# Plot each continuous segment separately
for segment in continuous_segments:
    ax.scatter(segment["date_time"], segment["pH_insitu_ta_est"], s=0.1, label="Uncorrected pH", color='xkcd:light pink', alpha=0.6)
    ax.scatter(segment["date_time"], segment["pH_optode_corrected"].rolling(60, min_periods=1).mean(), s=0.1, label="Corrected pH", color='b', alpha=0.6)
    ax.fill_between(segment["date_time"], 
                    segment["pH_optode_corrected"].rolling(60, min_periods=1).mean() - segment["pH_optode_corrected_RMSE"], 
                    segment["pH_optode_corrected"].rolling(60, min_periods=1).mean() + segment["pH_optode_corrected_RMSE"], 
                    color='b', alpha=0.2)

# Scatter plot for subsamples
ax.scatter(subsamples["date_time"], subsamples["pH_initial_talk_corr"], color='k', label='Subsamples $pH_{TA/DIC}$', s=20, alpha=0.6, edgecolor='k', zorder=6)

# Format plot
ax.set_ylabel("$pH_{total}$")
# ax.set_xlabel("Date Time")
ax.set_ylim(8, 8.2)
ax.grid(alpha=0.3)
fig.autofmt_xdate()

# Set y-axis labels every 0.05
yticks = np.arange(8.0, 8.21, 0.05)
ax.set_yticks(yticks)

# Add legend
from matplotlib.lines import Line2D
custom_handles = [
    Line2D([0], [0], marker='o', color='w', label='Uncorrected pH', markersize=6, markerfacecolor='xkcd:light pink'),
    Line2D([0], [0], marker='o', color='w', label='Corrected pH', markersize=6, markerfacecolor='b'),
] + ax.get_legend_handles_labels()[0][2:]  # Append other handles without modification
# legend = ax.legend(handles=custom_handles, loc="upper left")

# Show plot
plt.show()

# Save the DataFrame with corrected pH values and uncertainty for plotting
df.to_csv('./data/processing/PLOTTING_processed_uws_data_with_uncertainty_bootstrapping.csv', index=False)
subsamples.to_csv('./data/processing/PLOTTING_subsamples_with_corrections.csv', index=False)

