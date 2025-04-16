import pandas as pd
import numpy as np
import PyCO2SYS as pyco2

# Load data
subsamples = pd.read_csv("./data/processing/processed_vindta_subsamples.csv")

# Import RMSE for TALK and tCO2 based on NUTS analysis
tco2_rmse = 2.1070920505299284

# Number of Monte Carlo iterations
n_iterations = 2

# Initialize DataFrame to store pH values
pH_values_pH_initial_talk_tCO2 = pd.DataFrame({
    'iteration': np.repeat(np.arange(n_iterations), len(subsamples)),
    'subsample_index': np.tile(np.arange(len(subsamples)), n_iterations),
    'pH_total': np.zeros(n_iterations * len(subsamples))
})

# Iterate through each Monte Carlo simulation
for i in range(n_iterations):
    # Generate new tCO2 samples with added noise
    tco2_samples = subsamples['tco2'] + np.random.normal(0, tco2_rmse, subsamples.shape[0])
    
    # Calculate pH using the new tCO2 samples
    ph_results = pyco2.sys(
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
      
    # Store the results in the DataFrame
    pH_values_pH_initial_talk_tCO2.loc[pH_values_pH_initial_talk_tCO2['iteration'] == i, 'pH_total'] = ph_results

    # Optional: Print the current iteration's pH results to verify changes
    print(f"Iteration {i}: {ph_results}")

# Final results
print(pH_values_pH_initial_talk_tCO2)
