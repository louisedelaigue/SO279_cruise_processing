import pandas as pd
import numpy as np
import PyCO2SYS as pyco2

# Load data
subsamples = pd.read_csv("./data/processing/processed_vindta_subsamples.csv")

# Import RMSE for TALK and tco2 based on NUTS analysis
talk_rmse = 1.1792962721848792
tco2_rmse = 2.1070920505299284

# Calculate real pH values without adding variability
real_ph_TA_tCO2 = pyco2.sys(
    par1=subsamples['talk'].to_numpy(),
    par2=subsamples['tco2'].to_numpy(),
    par1_type=1,
    par2_type=2,
    opt_pH_scale=1,
    salinity=subsamples["salinity"].to_numpy(),
    temperature=subsamples["temperature"].to_numpy()
)['pH_total']

real_ph_pH_initial_talk_tCO2 = pyco2.sys(
    par1=subsamples['pH_initial_talk'].to_numpy(),
    par2=subsamples['tco2'].to_numpy(),
    par1_type=3,
    par2_type=2,
    opt_pH_scale=3,
    pressure=3,
    salinity=subsamples["salinity"].to_numpy(),
    temperature=25,
    temperature_out=subsamples["temperature"].to_numpy()
)['pH_total_out']

# Store real pH values in the subsamples DataFrame
subsamples['pH_real_TA_tCO2'] = real_ph_TA_tCO2
subsamples['pH_real_initial_talk_tCO2'] = real_ph_pH_initial_talk_tCO2

# Number of Monte Carlo iterations
n_iterations = 1000

# Initialize DataFrames to store pH values for Monte Carlo simulations
pH_values_TA_tCO2 = pd.DataFrame({
    'iteration': np.repeat(np.arange(n_iterations), len(subsamples)),
    'subsample_index': np.tile(np.arange(len(subsamples)), n_iterations),
    'pH_total': np.zeros(n_iterations * len(subsamples))
})

pH_values_pH_initial_talk_tCO2 = pd.DataFrame({
    'iteration': np.repeat(np.arange(n_iterations), len(subsamples)),
    'subsample_index': np.tile(np.arange(len(subsamples)), n_iterations),
    'pH_total': np.zeros(n_iterations * len(subsamples))
})


# Monte Carlo simulation
for i in range(n_iterations):
    # Generate random samples for TALK and tco2 within +/- RMSE
    talk_samples = subsamples['talk'] + np.random.normal(0, talk_rmse, subsamples.shape[0])
    tco2_samples = subsamples['tco2'] + np.random.normal(0, tco2_rmse, subsamples.shape[0])

    # Calculate pH using the randomly sampled TA and tco2
    ph_results_TA_tCO2 = pyco2.sys(
        par1=talk_samples.to_numpy(),
        par2=tco2_samples.to_numpy(),
        par1_type=1,
        par2_type=2,
        opt_pH_scale=1,
        salinity=subsamples["salinity"].to_numpy(),
        temperature=subsamples["temperature"].to_numpy()
    )['pH_total']

    # Calculate pH using pH_initial_talk and randomly sampled tco2
    ph_results_pH_initial_talk_tCO2 = pyco2.sys(
        par1=subsamples['pH_initial_talk'].to_numpy(),
        par2=tco2_samples,
        par1_type=3,
        par2_type=2,
        opt_pH_scale=3,
        pressure=3,
        salinity=subsamples["salinity"].to_numpy(),
        temperature=25,
        temperature_out=subsamples["temperature"].to_numpy()
    )['pH_total_out']

    # Store results in respective DataFrames
    pH_values_TA_tCO2.loc[pH_values_TA_tCO2['iteration'] == i, 'pH_total'] = ph_results_TA_tCO2
    pH_values_pH_initial_talk_tCO2.loc[pH_values_pH_initial_talk_tCO2['iteration'] == i, 'pH_total'] = ph_results_pH_initial_talk_tCO2

# Compute the RMSE for each calculation type
pH_values_TA_tCO2['squared_differences'] = (pH_values_TA_tCO2['pH_total'] - pH_values_TA_tCO2.groupby('subsample_index')['pH_total'].transform('mean'))**2
rmse_pH_TA_tCO2 = np.sqrt(pH_values_TA_tCO2.groupby('subsample_index')['squared_differences'].mean())

pH_values_pH_initial_talk_tCO2['squared_differences'] = (pH_values_pH_initial_talk_tCO2['pH_total'] - pH_values_pH_initial_talk_tCO2.groupby('subsample_index')['pH_total'].transform('mean'))**2
rmse_pH_pH_initial_talk_tCO2 = np.sqrt(pH_values_pH_initial_talk_tCO2.groupby('subsample_index')['squared_differences'].mean())

# Merge the RMSE data with the original subsamples data
subsamples['subsample_index'] = subsamples.index  # Add index column if not present

# Create a DataFrame for RMSE values
rmse_df = pd.DataFrame({
    'subsample_index': rmse_pH_TA_tCO2.index,
    'RMSE_pH_TA_tCO2': rmse_pH_TA_tCO2.values,
    'RMSE_pH_pH_initial_talk_tCO2': rmse_pH_pH_initial_talk_tCO2.values
})

subsamples_with_uncertainty = pd.merge(subsamples, rmse_df, on='subsample_index', how='left')

# Save the merged DataFrame
subsamples_with_uncertainty.to_csv("./data/processing/processed_vindta_subsamples_with_uncertainty.csv", index=False)
