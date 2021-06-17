import pandas as pd, numpy as np

# Import underway discrete samples
df = pd.read_csv('./data/processing/processed_uws_subsamples.csv')

# Create dupcode column
df_list = df['sample_id'].tolist()
df['dupcode'] = np.nan
for subsample in df_list:
    if len(subsample) == 2:
        df.loc[df['sample_id']==subsample, 'dupcode'] = subsample[0]
    else:
        df.loc[df['sample_id']==subsample, 'dupcode'] = subsample[:2]
df['dupcode'] = df['dupcode'].astype(int)

# Compute mean, absolute difference and difference/mean
sample_list = df['dupcode'].unique().tolist()
for sample in sample_list:
    L = df['dupcode'] == sample
    temp = df[L]
    df.loc[df['dupcode']==sample, 'difference'] = np.abs(np.diff(temp['total_nitrite']))[0]
    df.loc[df['dupcode']==sample, 'mean'] = temp['total_nitrite'].mean()
    df.loc[df['dupcode']==sample, 'diff/mean'] = df['difference']/df['mean']
    
# Compute FU number
average = df['diff/mean'].mean()
FU = average * 3
print(FU)

# FU = 1.3059930318262205

#%%
df_sub = df.copy()
dup_list = df_sub['dupcode'].unique().tolist()
for duplicate in dup_list:
    L = df_sub['dupcode']==duplicate
    temp = df_sub[L]
    df_sub.loc[df_sub['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['total_nitrate_nitrite']))[0]
    df_sub.loc[df_sub['dupcode']==duplicate, 'mean'] = temp['total_nitrate_nitrite'].mean()
    df_sub.loc[df_sub['dupcode']==duplicate, 'diff/mean'] = df_sub['difference']/df_sub['mean']

# Distribute flags based on FU and diff/mean in main df
sample_list = df_sub['sample_id'].tolist()
for sample in sample_list:
    a = df_sub.loc[df_sub['sample_id']==sample, 'diff/mean'].values
    if a > 1.3059930318262205:
        df.loc[df['sample_id']==sample, 'Nitrite_flag'] = 3
    else:
        df.loc[df['sample_id']==sample, 'Nitrite_flag'] = 2