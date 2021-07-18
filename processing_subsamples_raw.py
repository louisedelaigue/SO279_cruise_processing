import pandas as pd, numpy as np
import calkulate as calk

# Import subsamples info sheet
subsamples = pd.read_csv('./data/pH/UWS/UWS_subsamples.csv')

# Format date_time properly
subsamples['second'] = 0
subsamples['date_time'] = pd.to_datetime(subsamples[['year',
                                                     'month',
                                                     'day',
                                                     'hour',
                                                     'minute',
                                                     'second'
                                                     ]])
subsamples['date_time'] = pd.to_datetime(subsamples['date_time'])

# Drop useless columns from subsamples sheet
columns_list = [
    'cast',
    'niskin',
    'year',
    'month',
    'day',
    'hour',
    'minute',
    'second',
    'depth',
    'flag'    
    ]

subsamples.drop(columns=columns_list, inplace=True)

# Import continuous pH measurements
cont = pd.read_csv('./data/processing/raw_uws_data.csv')

# Check that datetime colums are datetime objects
cont['date_time'] = pd.to_datetime(cont['date_time'])

# Reindex sub_points so that date_time matches cont(date_time)
nearest = cont.set_index('date_time').reindex(subsamples.set_index('date_time').index, method='nearest').reset_index()

# Get the closest insitu salinity and temperature value from continuous 
# measurements dataset
point_location = subsamples['date_time'].tolist()
for location in point_location:
    subsamples.loc[subsamples['date_time']==location, 'salinity'] = nearest.loc[nearest['date_time']==location, 'salinity']
    subsamples.loc[subsamples['date_time']==location, 'temperature'] = nearest.loc[nearest['date_time']==location, 'SBE38_water_temp']
    subsamples.loc[subsamples['date_time']==location, 'latitude'] = nearest.loc[nearest['date_time']==location, 'lat']
    subsamples.loc[subsamples['date_time']==location, 'longitude'] = nearest.loc[nearest['date_time']==location, 'lon']
    subsamples.loc[subsamples['date_time']==location, 'salinity_flag'] = nearest.loc[nearest['date_time']==location, 'flag_salinity']

# Processing for UWS nutrients
# Import spreadsheet
nuts1 = pd.read_excel('./data/nutrients/210301-LouiseD-NP-AR1.xlsx', skiprows=6)
nuts1 = nuts1.drop(0)
nuts2 = pd.read_excel('./data/nutrients/210301-LouiseD-NP-BR1.xlsx', skiprows=6)
nuts2 = nuts2.drop(0)
all_nuts = [nuts1, nuts2]
nuts = pd.concat(all_nuts).reset_index(drop=True)

si1 = pd.read_excel('./data/nutrients/210316-LouiseD-Si-AR1.xlsx', skiprows=5)
si1 = si1.drop(0)
si2 = pd.read_excel('./data/nutrients/210316-LouiseD-Si-BR1.xlsx', skiprows=5)
si2 = si2.drop(0)
all_si = [si1, si2]
si = pd.concat(all_si).reset_index(drop=True)

# Merge nuts and si batches
nut_data = pd.merge(left=nuts, right=si, how='inner', left_on='METH', right_on='METH')

# Rename/drop useless columns and rows
nut_data.drop(columns="Unnamed: 2", inplace=True)
rn = {
    'METH':'sample_id',
    'NO3+NO2':'NO3_NO2'
}
nut_data.rename(rn, axis=1, inplace=True)
nut_data = nut_data[nut_data['sample_id'].str.len() <= 3]

# Lowercase the sample names to match subsamples sheet
nut_data["sample_id"] = nut_data.sample_id.str.lower()

# Add nutrient data to subsamples
subsamples['total_phosphate'] = np.nan
subsamples['total_ammonium'] = np.nan
subsamples['total_silicate'] = np.nan
subsamples['total_nitrate_nitrite'] = np.nan
subsamples['total_nitrite'] = np.nan

sample_list = subsamples['sample_id'].tolist()
for sample in sample_list:
    subsamples.loc[subsamples['sample_id']==sample, 'total_phosphate'] = nut_data.loc[nut_data['sample_id']==sample, 'PO4'].values
    subsamples.loc[subsamples['sample_id']==sample, 'total_ammonium'] = nut_data.loc[nut_data['sample_id']==sample, 'NH4'].values
    subsamples.loc[subsamples['sample_id']==sample, 'total_silicate'] = nut_data.loc[nut_data['sample_id']==sample, 'Si'].values
    subsamples.loc[subsamples['sample_id']==sample, 'total_nitrate_nitrite'] = nut_data.loc[nut_data['sample_id']==sample, 'NO3_NO2'].values
    subsamples.loc[subsamples['sample_id']==sample, 'total_nitrite'] = nut_data.loc[nut_data['sample_id']==sample, 'NO2'].values

# Calculate total nitrate
subsamples['total_nitrate'] = subsamples['total_nitrate_nitrite'] - subsamples['total_nitrite']

# Calculate density of each sample at lab temperature (= 23 deg C) and sample salinity
subsamples['density'] = calk.density.seawater_1atm_MP81(23, subsamples['salinity'])

# Convert nutrients from umol/L to umol/kg
subsamples['total_phosphate'] = subsamples['total_phosphate'] / subsamples['density']
subsamples['total_ammonium'] = subsamples['total_ammonium'] / subsamples['density']
subsamples['total_nitrate_nitrite'] = subsamples['total_nitrate_nitrite'] / subsamples['density']
subsamples['total_nitrite'] = subsamples['total_nitrite'] / subsamples['density']
subsamples['total_nitrate'] = subsamples['total_nitrate'] /subsamples['density']
subsamples['total_silicate'] = subsamples['total_silicate'] / subsamples['density']

# Save subsamples df as is for Precision Number computation in outside scripts
subsamples.to_csv('./data/processing/PN_uws_subsamples.csv', index=False)

# === QUALITY CONTROL
# Add flag column
# Quality flag convention: 2 = acceptable, 3 = questionable, 4 = known bad, 9 = missing value (lab issue)
subsamples['Phosphate_flag'] = 2
subsamples['Ammonium_flag'] = 2
subsamples['Nitrate_and_Nitrite_flag'] = 2
subsamples['Nitrite_flag'] = 2
subsamples['Nitrate_flag'] = 2
subsamples['Silicate_flag'] = 2

# Create duplicate code column
subsamples_list = subsamples['sample_id'].unique().tolist()
for subsample in subsamples_list:
    if len(subsample) == 2:
        subsamples.loc[subsamples['sample_id']==subsample, 'dupcode'] = subsample[0]
    else:
        subsamples.loc[subsamples['sample_id']==subsample, 'dupcode'] = subsample[:2]

# Flag for each nutrient
subsamples_sub = subsamples.copy()
L = subsamples_sub['total_phosphate'].isnull()
subsamples_sub = subsamples_sub[~L]

# === PHOSPHATE
# Compute mean, absolute difference and difference/mean using only rows with nutrient data
dup_list = subsamples_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = subsamples_sub['dupcode']==duplicate
    temp = subsamples_sub[L]
    subsamples_sub.loc[L, 'difference'] = np.abs(np.diff(temp['total_phosphate']))[0]
    subsamples_sub.loc[L, 'mean'] = temp['total_phosphate'].mean()
    subsamples_sub.loc[L, 'diff/mean'] = subsamples_sub['difference']/subsamples_sub['mean']

# Distribute flags based on Precision Number and diff/mean in main df
sample_list = subsamples_sub['sample_id'].tolist()
for sample in sample_list:
    a = subsamples_sub.loc[subsamples_sub['sample_id']==sample, 'diff/mean'].values
    if a > 1.1244298511197086:
        subsamples.loc[subsamples['sample_id']==sample, 'Phosphate_flag'] = 3
    else:
        subsamples.loc[subsamples['sample_id']==sample, 'Phosphate_flag'] = 2       

# === NITRATE
for duplicate in dup_list:
    L = subsamples_sub['dupcode']==duplicate
    temp = subsamples_sub[L]
    subsamples_sub.loc[L, 'difference'] = np.abs(np.diff(temp['total_nitrate']))[0]
    subsamples_sub.loc[L, 'mean'] = temp['total_nitrate'].mean()
    subsamples_sub.loc[L, 'diff/mean'] = subsamples_sub['difference']/subsamples_sub['mean']

# Distribute flags based on Precision Number and diff/mean in main df
sample_list = subsamples_sub['sample_id'].tolist()
for sample in sample_list:
    a = subsamples_sub.loc[subsamples_sub['sample_id']==sample, 'diff/mean'].values
    if a > 1.090059315150265:
        subsamples.loc[subsamples['sample_id']==sample, 'Nitrate_flag'] = 3
    else:
        subsamples.loc[subsamples['sample_id']==sample, 'Nitrate_flag'] = 2
        
# === NITRITE
# Compute mean, absolute difference and difference/mean using only rows with nutrient data
for duplicate in dup_list:
    L = subsamples_sub['dupcode']==duplicate
    temp = subsamples_sub[L]
    subsamples_sub.loc[L, 'difference'] = np.abs(np.diff(temp['total_nitrite']))[0]
    subsamples_sub.loc[L, 'mean'] = temp['total_nitrite'].mean()
    subsamples_sub.loc[L, 'diff/mean'] = subsamples_sub['difference']/subsamples_sub['mean']

# Distribute flags based on Precision Number and diff/mean in main df
sample_list = subsamples_sub['sample_id'].tolist()
for sample in sample_list:
    a = subsamples_sub.loc[subsamples_sub['sample_id']==sample, 'diff/mean'].values
    if a > 1.346392401087416:
        subsamples.loc[subsamples['sample_id']==sample, 'Nitrite_flag'] = 3
    else:
        subsamples.loc[subsamples['sample_id']==sample, 'Nitrite_flag'] = 2   

# === SILICATE
# Compute mean, absolute difference and difference/mean using only rows with nutrient data
dup_list = subsamples_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = subsamples_sub['dupcode']==duplicate
    temp = subsamples_sub[L]
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['total_silicate']))[0]
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'mean'] = temp['total_silicate'].mean()
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'diff/mean'] = subsamples_sub['difference']/subsamples_sub['mean']

# Distribute flags based on Precision Number and diff/mean in main df
sample_list = subsamples_sub['sample_id'].tolist()
for sample in sample_list:
    a = subsamples_sub.loc[subsamples_sub['sample_id']==sample, 'diff/mean'].values
    if a > 0.040382900391576666:
        subsamples.loc[subsamples['sample_id']==sample, 'Silicate_flag'] = 3
    else:
        subsamples.loc[subsamples['sample_id']==sample, 'Silicate_flag'] = 2
 
# === NITRATE NITRITE
# Compute mean, absolute difference and difference/mean using only rows with nutrient data
dup_list = subsamples_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = subsamples_sub['dupcode']==duplicate
    temp = subsamples_sub[L]
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['total_nitrate_nitrite']))[0]
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'mean'] = temp['total_nitrate_nitrite'].mean()
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'diff/mean'] = subsamples_sub['difference']/subsamples_sub['mean']

# Distribute flags based on Precision Number and diff/mean in main df
sample_list = subsamples_sub['sample_id'].tolist()
for sample in sample_list:
    a = subsamples_sub.loc[subsamples_sub['sample_id']==sample, 'diff/mean'].values
    if a > 1.0644479832449498:
        subsamples.loc[subsamples['sample_id']==sample, 'Nitrate_and_Nitrite_flag'] = 3
    else:
        subsamples.loc[subsamples['sample_id']==sample, 'Nitrate_and_Nitrite_flag'] = 2

# === AMMONIUM
# Compute mean, absolute difference and difference/mean using only rows with nutrient data
dup_list = subsamples_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = subsamples_sub['dupcode']==duplicate
    temp = subsamples_sub[L]
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['total_nitrate_nitrite']))[0]
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'mean'] = temp['total_nitrate_nitrite'].mean()
    subsamples_sub.loc[subsamples_sub['dupcode']==duplicate, 'diff/mean'] = subsamples_sub['difference']/subsamples_sub['mean']

# Distribute flags based on Precision Number and diff/mean in main df
sample_list = subsamples_sub['sample_id'].tolist()
for sample in sample_list:
    a = subsamples_sub.loc[subsamples_sub['sample_id']==sample, 'diff/mean'].values
    if a > 1.3213859347936425:
        subsamples.loc[subsamples['sample_id']==sample, 'Ammonium_flag'] = 3
    else:
        subsamples.loc[subsamples['sample_id']==sample, 'Ammonium_flag'] = 2

# Distribute nans for flags where there's no nutrient data
subsamples.loc[subsamples['total_phosphate'].isnull(), 'Phosphate_flag'] = np.nan
subsamples.loc[subsamples['total_ammonium'].isnull(), 'Ammonium_flag'] = np.nan
subsamples.loc[subsamples['total_nitrate_nitrite'].isnull(), 'Nitrate_and_Nitrite_flag'] = np.nan
subsamples.loc[subsamples['total_nitrite'].isnull(), 'Nitrite_flag'] = np.nan
subsamples.loc[subsamples['total_nitrate'].isnull(), 'Nitrate_flag'] = np.nan
subsamples.loc[subsamples['total_silicate'].isnull(), 'Silicate_flag'] = np.nan

# Distribute flag = 3 for which nutrient were converted to umol/kg with a salinity flag = 3
subsamples.loc[subsamples['sample_id']=='36a', 'Phosphate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36b', 'Phosphate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36a', 'Ammonium_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36b', 'Ammonium_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36a', 'Nitrate_and_Nitrite_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36b', 'Nitrate_and_Nitrite_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36a', 'Nitrate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36b', 'Nitrate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36a', 'Nitrite_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36b', 'Nitrite_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36a', 'Silicate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='36b', 'Silicate_flag'] = 3

# Distribute flag = 9 (missing value) for which nutrient were converted to 
# umol/kg with a salinity flag = 4
subsamples.loc[subsamples['sample_id']=='37a', 'Phosphate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37b', 'Phosphate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37a', 'Ammonium_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37b', 'Ammonium_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37a', 'Nitrate_and_Nitrite_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37b', 'Nitrate_and_Nitrite_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37a', 'Nitrate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37b', 'Nitrate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37a', 'Nitrite_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37b', 'Nitrite_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37a', 'Silicate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='37b', 'Silicate_flag'] = 9

# Distribute flag = 9 (missing value) for which salinity is missing
# and thus conversion cannot be done
subsamples.loc[subsamples['sample_id']=='14a', 'Phosphate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14b', 'Phosphate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14a', 'Ammonium_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14b', 'Ammonium_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14a', 'Nitrate_and_Nitrite_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14b', 'Nitrate_and_Nitrite_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14a', 'Nitrate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14b', 'Nitrate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14a', 'Nitrite_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14b', 'Nitrite_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14a', 'Silicate_flag'] = 9
subsamples.loc[subsamples['sample_id']=='14b', 'Silicate_flag'] = 9

# Distribute flag = 3 for unfiltered samples onboard the ship
subsamples.loc[subsamples['sample_id']=='4a', 'Phosphate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4b', 'Phosphate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4a', 'Ammonium_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4b', 'Ammonium_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4a', 'Nitrate_and_Nitrite_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4b', 'Nitrate_and_Nitrite_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4a', 'Nitrate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4b', 'Nitrate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4a', 'Nitrite_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4b', 'Nitrite_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4a', 'Silicate_flag'] = 3
subsamples.loc[subsamples['sample_id']=='4b', 'Silicate_flag'] = 3

# Save subsamplessheet to .csv
subsamples.to_csv('./data/processing/processed_uws_subsamples.csv', index=False)
