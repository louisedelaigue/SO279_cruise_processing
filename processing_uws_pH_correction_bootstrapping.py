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


# Initialize a DataFrame to hold bootstrapped uncertainties
df['pH_uncertainty'] = np.nan

# Perform bootstrapping for the entire dataset
n_iterations = 1000
bootstrapped_pH_values = []

# Get indices of subsamples
subsample_indices = subsamples.index.tolist()

# Check if there are at least two subsamples to perform interpolation
if len(subsamples) > 1:
    for iteration in range(n_iterations):
        # Randomly sample a subset of subsample indices, excluding index 0
        sampled_indices = np.random.choice(subsample_indices[1:], size=int(0.5 * (len(subsample_indices)-1)), replace=False)
        # Add index 0 to the sampled indices
        sampled_indices = np.concatenate(([subsample_indices[0]], sampled_indices))
        
        print("Sampled indices:", sampled_indices)  # Print sampled indices
        
        # Get the corresponding subsamples
        bootstrapped_subsamples = subsamples.loc[sampled_indices].sort_values(by='date_time')
        
        # Ensure that at least two samples are present after sampling
        if len(bootstrapped_subsamples) > 1:
            # Perform interpolation
            interp = PchipInterpolator(bootstrapped_subsamples['date_time'].astype(np.int64), bootstrapped_subsamples['diff'], extrapolate=False)
            df['pchip_pH_difference_temp'] = interp(df['date_time'].astype(np.int64))

            # Calculate and store the corrected pH values
            df['pH_optode_corrected_temp'] = df['pH_insitu_ta_est'] - df['pchip_pH_difference_temp']
            bootstrapped_pH_values.append(df['pH_optode_corrected_temp'].values)

    # Calculate uncertainty as the standard deviation across bootstrapped iterations
    if bootstrapped_pH_values:
        pH_uncertainty = np.std(np.column_stack(bootstrapped_pH_values), axis=1)
        df['pH_uncertainty'] = pH_uncertainty
else:
    print("Not enough subsamples for bootstrapping.")


    
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
ax.fill_between(df["date_time"][L], df["SMA"][L] - (df["SMA_uncertainty"][L] +0), df["SMA"][L] + (df["SMA_uncertainty"][L] + 0), color='b', alpha=0.2)
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

# #%%
# # Use all subsamples to interpolate a correction for the entire dataset
# interp = PchipInterpolator(subsamples['date_time'].astype(np.int64), subsamples['diff'], extrapolate=True)
# df['pchip_pH_difference'] = interp(df['date_time'].astype(np.int64))

# # Apply the interpolated correction
# df['pH_optode_corrected'] = df['pH_insitu_ta_est'] - df['pchip_pH_difference']

# # Ensure 'diff' contains only finite values before interpolation
# subsamples = subsamples[np.isfinite(subsamples['diff'])]

# # Initialize a DataFrame to hold bootstrapped uncertainties
# df['pH_uncertainty'] = np.nan

# # Define the date ranges and their corresponding correction numbers
# date_ranges = {
#     1: ('beginning', '2020-12-10'),
#     2: ('2020-12-11', '2020-12-15'),
#     3: ('2020-12-16', '2020-12-16'),
#     4: ('2020-12-17', '2020-12-18'),
#     5: ('2020-12-19', '2020-12-21'),
#     6: ('2020-12-22', '2020-12-27'),
#     7: ('2020-12-28', 'end')
# }

# # Function to assign correction numbers based on inclusive date ranges
# def assign_correction_number(date, date_ranges):
#     for correction_number, (start_str, end_str) in date_ranges.items():
#         start_date = pd.to_datetime(start_str) if start_str != 'beginning' else pd.NaT
#         end_date = pd.to_datetime(end_str) if end_str != 'end' else pd.NaT

#         # If we have a valid end date, add one day (to include the entire end day) and subtract one second to avoid including midnight of the next day
#         if pd.notnull(end_date):
#             end_date = end_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

#         # Now check if the date falls within the range, inclusive of both start and end dates
#         if (pd.isnull(start_date) or date >= start_date) and (pd.isnull(end_date) or date <= end_date):
#             return correction_number
#     return np.nan  # Return NaN if the date does not fall into any range

# # Re-apply the function to assign correction numbers
# df['correction_number'] = df['date_time'].apply(lambda date: assign_correction_number(date, date_ranges))
# subsamples['correction_number'] = subsamples['date_time'].apply(lambda date: assign_correction_number(date, date_ranges))

# # Make sure no rows have NaN for correction_number
# assert not df['correction_number'].isnull().any(), "There are rows in df with NaN correction_number"
# assert not subsamples['correction_number'].isnull().any(), "There are rows in subsamples with NaN correction_number"

# for correction_number in date_ranges.keys():
#     file_df_indices = df['correction_number'] == correction_number
#     file_subsamples = subsamples[subsamples['correction_number'] == correction_number]

#     # Check if there are at least two subsamples to perform interpolation
#     if len(file_subsamples) >= 2:
#         n_iterations = 100
#         bootstrapped_pH_values = []
        
#         # Dynamic fraction to omit based on the number of subsamples
#         fraction_to_omit = min(0.3, (len(file_subsamples) - 1) / len(file_subsamples))

#         for iteration in range(n_iterations):
#             # Randomly sample a subset of subsamples
#             bootstrapped_subsamples = file_subsamples.sample(frac=1 - fraction_to_omit)
#             bootstrapped_subsamples = bootstrapped_subsamples[np.isfinite(bootstrapped_subsamples['diff'])].sort_values(by='date_time').drop_duplicates(subset='date_time')

#             # Ensure that at least two samples are present after dropping duplicates
#             if len(bootstrapped_subsamples) > 1:
#                 # Perform interpolation
#                 interp = PchipInterpolator(bootstrapped_subsamples['date_time'].astype(np.int64), bootstrapped_subsamples['diff'], extrapolate=False)
#                 temp_pH_difference = interp(df.loc[file_df_indices, 'date_time'].astype(np.int64))

#                 # Assign interpolated values back to the DataFrame
#                 df.loc[file_df_indices, 'pchip_pH_difference_temp'] = temp_pH_difference
                
#                 # Calculate and store the corrected pH values
#                 temp_pH_corrected = df.loc[file_df_indices, 'pH_insitu_ta_est'] - temp_pH_difference
#                 bootstrapped_pH_values.append(temp_pH_corrected)

#         # Calculate uncertainty as the standard deviation across bootstrapped iterations
#         if bootstrapped_pH_values:
#             pH_uncertainty = np.std(np.column_stack(bootstrapped_pH_values), axis=1)
#             df.loc[file_df_indices, 'pH_uncertainty'] = pH_uncertainty
#     else:
#         # Skip this iteration and print a message
#         print(f"Skipping bootstrapping for correction number {correction_number}: not enough subsamples.")


# # Continue with the rest of the script for moving average and plotting...

# # === SIMPLE MOVING AVERAGE
# # Compute simple moving average (SMA) over period of 30 minutes
# df["SMA"] = df["pH_optode_corrected"].rolling(60, min_periods=1).mean()
# df["SMA_uncertainty"] = df["pH_uncertainty"].rolling(60, min_periods=1).mean()

# # Save the results
# # df.to_csv('./data/processing/processed_uws_data_with_uncertainty.csv', index=False)
# # subsamples.to_csv('./data/processing/subsamples_pH_correction_with_uncertainty.csv', index=False)

# print("Processing and uncertainty estimation completed.")

# # Create plot
# fig, ax = plt.subplots(figsize=(6, 4), dpi=300)

# # Plotting the uncorrected and corrected pH values along with uncertainties
# L = df["SMA"].notnull()
# ax.scatter(df["date_time"][L], df["pH_insitu_ta_est"][L], s=0.1, label="Uncorrected pH", color='xkcd:light pink', alpha=0.6)
# ax.scatter(df["date_time"][L], df["SMA"][L], s=0.1, label="Corrected pH", color='b', alpha=0.6)
# ax.fill_between(df["date_time"][L], df["SMA"][L] - (df["SMA_uncertainty"][L] +1), df["SMA"][L] + (df["SMA_uncertainty"][L] + 1), color='b', alpha=0.2)
# ax.scatter(subsamples["date_time"], subsamples["pH_initial_talk_corr"], color='k', label='Subsamples $pH_{TA/DIC}$', s=20, alpha=0.6, edgecolor='k', zorder=6)

# # Improve plot aesthetics
# ax.set_ylabel("$pH_{total}$")
# ax.set_ylim(8.05, 8.2)
# ax.grid(alpha=0.3)
# fig.autofmt_xdate()

# # Add a legend with custom marker sizes
# handles, labels = ax.get_legend_handles_labels()
# custom_handles = [
#     plt.Line2D([], [], marker='o', color='w', label='Uncorrected pH', markersize=6, markerfacecolor='xkcd:light pink'),
#     plt.Line2D([], [], marker='o', color='w', label='Corrected pH', markersize=6, markerfacecolor='b'),
# ] + handles[2:]  # Append other handles without modification
# legend = ax.legend(handles=custom_handles, loc="upper left")

# plt.show()

# #%%
# import matplotlib.pyplot as plt

# # Get unique filenames from the DataFrame
# unique_filenames = df['filename'].unique()

# # Set up the figure size and layout
# plt.figure(figsize=(14, 14))

# # Loop through each unique filename and create a plot
# for i, filename in enumerate(unique_filenames, start=1):
#     # Filter the dataframe for the current filename
#     file_df = df[df['filename'] == filename]
    
#     # Create a subplot for each filename
#     plt.subplot(len(unique_filenames), 1, i)
#     plt.scatter(file_df['date_time'], file_df['pH_optode_corrected'], label=f'Corrected pH for {filename}')
#     plt.title(f'Corrected pH for {filename}')
#     plt.xlabel('Date Time')
#     plt.ylabel('pH')
#     plt.legend()
#     plt.tight_layout()

# # Show the plot
# plt.show()
