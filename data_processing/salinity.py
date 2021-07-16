import pandas as pd, numpy as np
from scipy.interpolate import PchipInterpolator

def salinity(data):  
    # Assign nan to SMB name column, then fill with rolling previous pump name
    df = data.copy()
    df.loc[df.smb_name == ' ', 'smb_name'] = np.nan
    df['smb_name'].fillna(method='ffill', inplace=True)
    
    # Drop 6 outliers in salinity data (before storm)
    L = (df['date_time'] < '2020-12-25 00:00:00') & (df['date_time'] > '2020-12-15 00:00:00') & (df['SBE45_sal'] < 35.4)
    df = df[~L]
    
    # Find index where pump name changes
    change_loc = np.where(np.roll(df['smb_name'], 1)!= df['smb_name'])[0].tolist()
    
    # Add start and end points to list
    end = df.index[-1]
    change_loc.append(end)
    
    # Create df to hold computed differences
    points = pd.DataFrame({'location':change_loc})
    points['point'] = np.nan
    points['date_time'] = np.nan   
    
    for i in range(1, len(change_loc) -1):
        first = df['SBE45_sal'][change_loc[i-1]:change_loc[i]].iloc[-10:].mean()
        last = df['SBE45_sal'][change_loc[i]:change_loc[i+1]].iloc[:10].mean()
        points.loc[points.location==change_loc[i], 'point'] = abs(first - last) / 2
        points.loc[points.location==change_loc[i], 'date_time'] = df['date_time'][change_loc[i]]
        print('loop {}: {}, {}'.format(i, first, last))

    # Drop start and end points
    points.dropna(axis=0, how='any', inplace=True)
    
    # Drop differences during storm for now
    L = points['point'] < 1
    points = points[L]
    
    # Check that datetime colums are datetime objects
    df['date_time'] = pd.to_datetime(df['date_time'])
    points['date_time'] = pd.to_datetime(points['date_time'])
    
    # PCHIP difference points over date_time range in df
    points.sort_values(by=['point'], ascending=True)
    interp_obj = PchipInterpolator(points['date_time'], points['point'], extrapolate=False)
    df['pchip_salinity'] = interp_obj(df['date_time'])
    
    # Replace end nan with last pchip value
    # This is because can only interpolate in between points, not outside
    df['pchip_salinity'].fillna(method='ffill', inplace=True)
    
    # Replace start nan with first mean point
    df['pchip_salinity'].fillna(0.404055, inplace=True)
    
    # Compute the difference between uncorrected salinity and pchip points
    # df['diff'] = abs(df['SBE45_sal'] - df['pchip_salinity']) / 2
    
    # Correct pump A and B
    # L = df['smb_name'] == 'SMB_A'
    df['salinity'] = np.nan
    
    # Add corrected salinity value to df as a function of pump name
    pump_name = df['smb_name'].unique().tolist()
    for name in pump_name:
        if name == 'SMB_A':
            df.loc[df['smb_name']=='SMB_A', 'salinity'] = df['SBE45_sal'] - df['pchip_salinity']
        else:
            df.loc[df['smb_name']=='SMB_B', 'salinity'] = df['SBE45_sal'] + df['pchip_salinity']

    # === Quality control
    # Add flag
    df['flag_salinity'] = 2
    # Flag = 9 for missing values
    df.loc[df['salinity'].isnull(), 'flag_salinity'] = 9
    # ==Flag bad salinity during storm    
    # Add flag = 3
    df.loc[(df['date_time'].dt.day == 26)  & (df['salinity'] < 35.9) & (df['salinity'] > 26), 'flag_salinity'] = 3
    
    # Add flag = 4
    df.loc[(df['salinity'] < 27), 'flag_salinity'] = 4
    df.loc[(df['date_time'].dt.day == 27), 'flag_salinity'] = 4
    
    # Replace flag = 4 by nan
    df.loc[(df['flag_salinity']==4), 'salinity'] = np.nan

    return df
