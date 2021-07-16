import pandas as pd, numpy as np
import os
import calkulate as calk

# Make a list of files inside folder
file_list = os.listdir(path='./data/CTD/')
file_list = ' '.join(file_list).replace('.cnv','').split()

# Create loop to extract data
data = {}
for file in file_list:
    fname = "./data/CTD/{}.cnv".format(file)
    data[file] = pd.read_table(fname, encoding="unicode_escape")
    data[file]['station'] = file
    
    # Only keep one line for each niskin bottle
    data[file] = data[file].groupby(by=["station", "niskin"]).mean().reset_index()
    L = data[file]['niskin'] == 0
    data[file] = data[file][~L]

# Create one df for all CTD data
all_dfs = [data['STN1'],
           data['STN3'],
           data['STN4'],
           data['STN5'],
           data['STN6'],
           data['STN7'],
           data['STN9']]
ctd_data = pd.concat(all_dfs).reset_index(drop=True)
ctd_data = ctd_data.sort_values(by=['station', 'niskin'])

# Create a column with average salinity, temperature and oxygen (a and b)
ctd_data['salinity'] = ctd_data[['salinity_a', 'salinity_b']].mean(axis=1)
ctd_data['temperature'] = ctd_data[['temperature_a', 'temperature_b']].mean(axis=1)

# Drop columns not pertinent to carbonate chemistry
columns = [
        'salinity_a',
        'salinity_b',
        'temperature_a',
        'temperature_b',
        'oxygen_a',
        'oxygen_b',
        'fluorescence',
        'irradiance',
        'tubirdity',
        'time_seconds',
        'time_elapsed_min',
        'time_elapsed_seconds',
        'flag',
    ]
ctd_data.drop(columns, axis =1, inplace=True)

# Simplify CTD station names
ctd_data['niskin'] = ctd_data['niskin'].astype(str)
ctd_data['station'] = ctd_data['station'].str.replace('STN', '')

# Add silicate and nutrient data
# === SILICATE
# Import spreadsheets and create one df
si1 = pd.read_excel('./data/nutrients/210324-LouiseD-Si-AR1.xlsx', skiprows=6)
si1 = si1.drop(0)
si2 = pd.read_excel('./data/nutrients/210329-LouiseD-Si-AR1R1.xlsx', skiprows=6)
si2 = si2.drop(0)
all_si = [si1, si2]
si = pd.concat(all_si).reset_index(drop=True)

# Rename columns with sensible names
rn = {
      "UNIT":"sample",
      "µmol/L":"total_silicate"
      }
si.rename(rn, axis=1, inplace=True)

# Remove useless rows
si = si[~si["sample"].isin(["CRM BU-1271", "COCKT1008X250", "WASHWATER"])]

# Rename samples 
sample_list = si['sample'].tolist()
sample_names = []
for sample in sample_list:
    if len(sample.split("-"))== 3:
        stn = sample.split("-")[0]
        sample_names.append(sample)
    else:
        sample_names.append(stn + "-" + sample)

si['sample_names'] = sample_names

# Drop the column with wrong names
si.drop('sample', axis =1, inplace=True)

# Create columns for station, niskin and duplicate to match CTD data
si['station'] = si['sample_names'].apply(lambda x: x.split("-")[0]).str[-1]
si['niskin'] = si['sample_names'].apply(lambda x: x.split("-")[1])
si['duplicate'] = si['sample_names'].apply(lambda x: x.split("-")[2])
si.drop('sample_names', axis =1, inplace=True)

# Change duplicated row for Station 7 Niskin 22 Duplicate 1.2 
# (should be 2, typo in original file from analysis)
si.loc[si['total_silicate']==0.592, 'duplicate'] = '2'

# === NUTRIENTS
# Import spreadsheet
nuts1 = pd.read_excel('./data/nutrients/210414-LouiseD-NP-AR1.xlsx', skiprows=6)
nuts1 = nuts1.drop(0)
nuts2 = pd.read_excel('./data/nutrients/210428-LouiseD-NP-AR1.xlsx', skiprows=6)
nuts2 = nuts2.drop(0)
nuts3 = pd.read_excel('./data/nutrients/210414-LouiseD-NP-BR1.xlsx', skiprows=6)
all_nuts = [nuts1, nuts2, nuts3]
nuts = pd.concat(all_nuts).reset_index(drop=True)

# Rename columns to sensible names
rn = {
    'METH':'sample',
    'NO3+NO2':'total_nitrate_nitrite',
    'PO4':'total_phosphate',
    'NH4':'total_ammonium',
    'NO2':'total_nitrite',
    'NO3':'total_nitrate'
}
nuts.rename(rn, axis=1, inplace=True)

# Remove useless rows
nuts = nuts[~nuts['sample'].isin(['CRM BU-0899 OCT20',
                                     'CRM BU-1310 NEW',
                                     'COCKT1008X250',
                                     'CRM CH-2333',
                                     'WASHWATER',
                                     'WASWATER',
                                     'COCKTAIL1008X250',
                                     'COCKTAIL1008X500',
                                     'UNIT'
                                     ])]

# Rename samples
sample_list = nuts['sample'].tolist()
sample_names = []
for sample in sample_list:
    if len(sample.split("-"))== 3:
        stn = sample.split("-")[0]
        sample_names.append(sample)
    else:
        sample_names.append(stn + "-" + sample)

nuts['sample_names'] = sample_names

# Create columns for station, niskin and duplicate to match CTD data
nuts['station'] = nuts['sample_names'].apply(lambda x: x.split("-")[0]).str[-1]
nuts['niskin'] = nuts['sample_names'].apply(lambda x: x.split("-")[1])
nuts['niskin'] = nuts['niskin'].replace({'N':''})
nuts['niskin'] = nuts['niskin'].map(lambda x: x.lstrip('N'))
nuts['duplicate'] = nuts['sample_names'].apply(lambda x: x.split("-")[2])
nuts.drop('sample_names', axis =1, inplace=True)

# Create station codes for merging
si['station'] = si['station'].astype(str)
si['niskin'] = si['niskin'].astype(str)
si['duplicate'] = si['duplicate'].astype(str)

si['stncode'] = si['station'] + si['niskin'] + si['duplicate']
nuts['stncode'] = nuts['station'] + nuts['niskin'] + nuts['duplicate']

# Drop useless columns
columns = [
    'sample',
    'station',
    'niskin',
    'duplicate',
    ]
nuts.drop(columns, axis =1, inplace=True)

# Merge nutrients together
nut_data = pd.merge(left=nuts, right=si, how='inner', on='stncode')

# Merge nutrients with CTD data
ctd_data = pd.merge(ctd_data, nut_data, on=['station','niskin'], how='left')

# Calculate total nitrate for all stations (filling missing 6, 7 and 9)
ctd_data['total_nitrate'] = ctd_data['total_nitrate_nitrite'] - ctd_data['total_nitrite']

# Drop Niskins not sampled for carbonate chemistryNo documenta
# ctd_data.dropna(subset=['duplicate'], how='all', inplace=True)

# Calculate density of each sample
ctd_data['density'] = calk.density.seawater_1atm_MP81(23, ctd_data['salinity'])

# Convert nutrients from umol/L to umol/kg
ctd_data['total_phosphate'] = ctd_data['total_phosphate'] / ctd_data['density']
ctd_data['total_ammonium'] = ctd_data['total_ammonium'] / ctd_data['density']
ctd_data['total_nitrate_nitrite'] = ctd_data['total_nitrate_nitrite'] / ctd_data['density']
ctd_data['total_nitrite'] = ctd_data['total_nitrite'] / ctd_data['density']
ctd_data['total_nitrate'] = ctd_data['total_nitrate'] /ctd_data['density']
ctd_data['total_silicate'] = ctd_data['total_silicate'] / ctd_data['density']

# === QUALITY CONTROL
# Add flag column
# Quality flag convention: 2 = acceptable, 3 = questionable, 4 = known bad, 9 = missing value (lab issue)
ctd_data['Phosphate_flag'] = 2
ctd_data['Ammonium_flag'] = 2
ctd_data['Nitrate_and_Nitrite_flag'] = 2
ctd_data['Nitrite_flag'] = 2
ctd_data['Nitrate_flag'] = 2
ctd_data['Silicate_flag'] = 2

# Flag case by case
# === PHOSPHATE
# STN 1
ctd_data.loc[ctd_data['stncode']=='1151', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='182', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='1102', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='1141', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='1142', 'Phosphate_flag'] = 3

# STN 3
ctd_data.loc[ctd_data['stncode']=='3131', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='382', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='3141', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='3142', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='361', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='362', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='331', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='332', 'Phosphate_flag'] = 3

# STN 4
ctd_data.loc[ctd_data['stncode']=='4121', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='4141', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='4142', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='4131', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='4132', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='411', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='412', 'Phosphate_flag'] = 3

# STN 5
ctd_data.loc[ctd_data['stncode']=='5121', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='5111', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='512', 'Phosphate_flag'] = 4

# STN 6
ctd_data.loc[ctd_data['stncode']=='681', 'Phosphate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='671', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='672', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='611', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='612', 'Phosphate_flag'] = 3

# STN 7
ctd_data.loc[ctd_data['stncode']=='791', 'Phosphate_flag'] = 4

# STN 4
ctd_data.loc[ctd_data['stncode']=='4131', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='4132', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='4101', 'Phosphate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='9102', 'Phosphate_flag'] = 3

# === NITRATE
# STN 1
ctd_data.loc[ctd_data['stncode']=='1151', 'Nitrate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='182', 'Nitrate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='1102', 'Nitrate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='1141', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='1142', 'Nitrate_flag'] = 3

# STN 3
ctd_data.loc[ctd_data['stncode']=='3131', 'Nitrate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='382', 'Nitrate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='362', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='362', 'Nitrate_flag'] = 3

# STN 4
ctd_data.loc[ctd_data['stncode']=='4121', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='4122', 'Nitrate_flag'] = 3

# STN 5
ctd_data.loc[ctd_data['stncode']=='512', 'Nitrate_flag'] = 4
ctd_data.loc[ctd_data['stncode']=='5121', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='5122', 'Nitrate_flag'] = 3

# STN 6 
ctd_data.loc[ctd_data['stncode']=='6121', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='6122', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='681', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='682', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='671', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='672', 'Nitrate_flag'] = 3

# STN 7
ctd_data.loc[ctd_data['stncode']=='791', 'Nitrate_flag'] = 4

# STN 9
ctd_data.loc[ctd_data['stncode']=='9131', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='9132', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='9101', 'Nitrate_flag'] = 3
ctd_data.loc[ctd_data['stncode']=='9102', 'Nitrate_flag'] = 3

# === NITRITE
# Create dupcode column
ctd_data_sub = ctd_data.copy()
L = ctd_data_sub['total_nitrite'].isnull()
ctd_data_sub = ctd_data_sub[~L]

ctd_data_sub['dupcode'] = ctd_data_sub['station'] + ctd_data_sub['niskin']

# Compute mean, absolute difference and difference/mean using only rows with nutrient data
dup_list = ctd_data_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = ctd_data_sub['dupcode']==duplicate
    temp = ctd_data_sub[L]
    ctd_data_sub.loc[L, 'difference'] = np.abs(np.diff(temp['total_nitrite']))[0]
    ctd_data_sub.loc[L, 'mean'] = temp['total_nitrite'].mean()
    ctd_data_sub.loc[L, 'diff/mean'] = ctd_data_sub['difference']/ctd_data_sub['mean']

# Distribute flags based on PN and diff/mean in main df
# Precision number calculated in separate script
sample_list = ctd_data_sub['stncode'].tolist()
for sample in sample_list:
    a = ctd_data_sub.loc[ctd_data_sub['stncode']==sample, 'diff/mean'].values
    if a > 1.346392401087416:
        ctd_data.loc[ctd_data['stncode']==sample, 'Nitrite_flag'] = 3
    else:
        ctd_data.loc[ctd_data['stncode']==sample, 'Nitrite_flag'] = 2       

# === SILICATE
# Compute mean, absolute difference and difference/mean using only rows with nutrient data
dup_list = ctd_data_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = ctd_data_sub['dupcode']==duplicate
    temp = ctd_data_sub[L]
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['total_silicate']))[0]
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'mean'] = temp['total_silicate'].mean()
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'diff/mean'] = ctd_data_sub['difference']/ctd_data_sub['mean']

# Distribute flags based on PN and diff/mean in main df
sample_list = ctd_data_sub['stncode'].tolist()
for sample in sample_list:
    a = ctd_data_sub.loc[ctd_data_sub['stncode']==sample, 'diff/mean'].values
    if a > 0.040382900391576666:
        ctd_data.loc[ctd_data['stncode']==sample, 'Silicate_flag'] = 3
    else:
        ctd_data.loc[ctd_data['stncode']==sample, 'Silicate_flag'] = 2

# === NITRATE NITRITE
# Compute mean, absolute difference and difference/mean using only rows with nutrient data
dup_list = ctd_data_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = ctd_data_sub['dupcode']==duplicate
    temp = ctd_data_sub[L]
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['total_nitrate_nitrite']))[0]
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'mean'] = temp['total_nitrate_nitrite'].mean()
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'diff/mean'] = ctd_data_sub['difference']/ctd_data_sub['mean']

# Distribute flags based on PN and diff/mean in main df
sample_list = ctd_data_sub['stncode'].tolist()
for sample in sample_list:
    a = ctd_data_sub.loc[ctd_data_sub['stncode']==sample, 'diff/mean'].values
    if a > 1.0644479832449498:
        ctd_data.loc[ctd_data['stncode']==sample, 'Nitrate_and_Nitrite_flag'] = 3
    else:
        ctd_data.loc[ctd_data['stncode']==sample, 'Nitrate_and_Nitrite_flag'] = 2

# === AMMONIUM
# Compute mean, absolute difference and difference/mean using only rows with nutrient data
dup_list = ctd_data_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = ctd_data_sub['dupcode']==duplicate
    temp = ctd_data_sub[L]
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['total_ammonium']))[0]
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'mean'] = temp['total_ammonium'].mean()
    ctd_data_sub.loc[ctd_data_sub['dupcode']==duplicate, 'diff/mean'] = ctd_data_sub['difference']/ctd_data_sub['mean']

# Distribute flags based on PN and diff/mean in main df
sample_list = ctd_data_sub['stncode'].tolist()
for sample in sample_list:
    a = ctd_data_sub.loc[ctd_data_sub['stncode']==sample, 'diff/mean'].values
    if a > 1.3213859347936425:
        ctd_data.loc[ctd_data['stncode']==sample, 'Ammonium_flag'] = 3
    else:
        ctd_data.loc[ctd_data['stncode']==sample, 'Ammonium_flag'] = 2

# Distribute nans for flags where there's no nutrient data
ctd_data.loc[ctd_data['total_phosphate'].isnull(), 'Phosphate_flag'] = np.nan
ctd_data.loc[ctd_data['total_ammonium'].isnull(), 'Ammonium_flag'] = np.nan
ctd_data.loc[ctd_data['total_nitrate_nitrite'].isnull(), 'Nitrate_and_Nitrite_flag'] = np.nan
ctd_data.loc[ctd_data['total_nitrite'].isnull(), 'Nitrite_flag'] = np.nan
ctd_data.loc[ctd_data['total_nitrate'].isnull(), 'Nitrate_flag'] = np.nan
ctd_data.loc[ctd_data['total_silicate'].isnull(), 'Silicate_flag'] = np.nan

# Ensure all data except stncode are numbers
ctd_data['station'] = pd.to_numeric(ctd_data['station'])
ctd_data['niskin'] = pd.to_numeric(ctd_data['niskin'])
ctd_data['total_nitrate_nitrite'] = pd.to_numeric(ctd_data['total_nitrate_nitrite'])
ctd_data['total_phosphate'] = pd.to_numeric(ctd_data['total_phosphate'])
ctd_data['total_ammonium'] = pd.to_numeric(ctd_data['total_ammonium'])
ctd_data['total_nitrite'] = pd.to_numeric(ctd_data['total_nitrite'])
ctd_data['total_nitrate'] = pd.to_numeric(ctd_data['total_nitrate'])
ctd_data['duplicate'] = pd.to_numeric(ctd_data['duplicate'])

# Save file to .csv
ctd_data.to_csv('./data/processing/processed_ctd_data.csv', index=False)