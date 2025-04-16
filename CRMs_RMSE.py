import pandas as pd, numpy as np

# Load data
df = pd.read_csv("./data/processing/dbs.csv")

# Only keep columns of interest
df = df[['analysis_datetime', 'bottle', 'alkalinity', 'dic']]

# Only keep CRMs
L = (df["bottle"].str.startswith("CRM")) & (df["bottle"].str.endswith("-1"))
df = df[L]
    
# Setting specific DIC or TALK outliers to NaN based on datetime
df.loc[df['analysis_datetime'] == '2021-03-10 12:57:00', ['alkalinity', 'dic']] = np.nan
df.loc[df['analysis_datetime'] == '2021-03-19 10:07:00', ['alkalinity', 'dic']] = np.nan

# Extract date part from the datetime for grouping by day
df['analysis_datetime'] = pd.to_datetime(df['analysis_datetime'])
df['Date'] = df['analysis_datetime'].dt.date

# Function to calculate RMSE
def rmse(group):
    mean_alk = group['alkalinity'].mean()
    mean_dic = group['dic'].mean()
    mse_alk = ((group['alkalinity'] - mean_alk) ** 2).mean()
    mse_dic = ((group['dic'] - mean_dic) ** 2).mean()
    return pd.Series({
        'RMSE_Alkalinity': np.sqrt(mse_alk),
        'RMSE_DIC': np.sqrt(mse_dic)
    })

# Group by Date and apply RMSE function
rmse_results = df.groupby('Date').apply(rmse)
# print(rmse_results)

# Filter where RMSE_Alkalinity is not 0 and calculate mean
mean_rmse_alkalinity = rmse_results[rmse_results['RMSE_Alkalinity'] != 0]['RMSE_Alkalinity'].mean()

# Filter where RMSE_DIC is not 0 and calculate mean
mean_rmse_dic = rmse_results[rmse_results['RMSE_DIC'] != 0]['RMSE_DIC'].mean()

print("Mean RMSE for Alkalinity:", mean_rmse_alkalinity)
print("Mean RMSE for DIC:", mean_rmse_dic)
