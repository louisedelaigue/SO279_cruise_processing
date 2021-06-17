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
    df.loc[df['dupcode']==sample, 'difference'] = np.abs(np.diff(temp['total_ammonia']))[0]
    df.loc[df['dupcode']==sample, 'mean'] = temp['total_ammonia'].mean()
    df.loc[df['dupcode']==sample, 'diff/mean'] = df['difference']/df['mean']
    
# Compute FU number
average = df['diff/mean'].mean()
FU = average * 3
print(FU)

# FU = 1.2793724837930212