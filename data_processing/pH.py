import pandas as pd, numpy as np
import PyCO2SYS as pyco2
from scipy.interpolate import PchipInterpolator

def pH(data, uws_sub_filepath):
    df = data.copy()
    # ============================================================================
    # TEST
    df['zscore'] = abs((df['pH_insitu'] - df['pH_insitu'].mean())/df['pH_insitu'].std(ddof=0))
    L = df['zscore'] < 2
    df = df[L]    
    # ============================================================================       
    # Import UWS subsampling df
    uws_sub = pd.read_csv(uws_sub_filepath)
    
    # Only keep first file
    # L = df['filename'] == '2020-12-08_204002_SO279_STN1_test'
    # df = df[L]
    
    # Only keep df pertinent to first file (excluding outlier)
    # uws_sub = uws_sub[0:6]
    # L = uws_sub.index == 4
    # uws_sub = uws_sub[~L]
    
    # Recalculate pH(TA/DIC) at insitu temperature
    uws_sub['pH_talk_tco2_insitu_temp'] = pyco2.sys(
        uws_sub.talk,
        uws_sub.tco2,
        1,
        2,
        salinity=uws_sub.salinity,
        temperature_out=uws_sub.temp_insitu,
        total_phosphate=uws_sub.total_phosphate,
        total_silicate=uws_sub.total_silicate,
        total_ammonia=uws_sub.total_ammonia,
    )['pH_total_out']
    
    # Recalculate pH(initial) at insitu temperature using DIC and convert from free scale to total scale
    uws_sub['pH_init_talk_total_tco2_insitu_temp'] = pyco2.sys(
        uws_sub.pH_init_talk,
        uws_sub.tco2,
        3,
        2,
        opt_pH_scale=3,
        salinity=uws_sub.salinity,
        temperature_out=uws_sub.temp_insitu,
        total_phosphate=uws_sub.total_phosphate,
        total_silicate=uws_sub.total_silicate,
        total_ammonia=uws_sub.total_ammonia,
    )['pH_total_out']
    
    # Remove outliers for pH(TA/DIC)
    uws_sub['zscore'] = abs((uws_sub['pH_talk_tco2_insitu_temp'] - uws_sub['pH_talk_tco2_insitu_temp'].mean())/uws_sub['pH_talk_tco2_insitu_temp'].std(ddof=0))
    L = uws_sub['zscore'] < 2
    uws_sub = uws_sub[L]
    
    # Remove outliers for pH(init elec)
    uws_sub['zscore'] = abs((uws_sub['pH_init_talk_total_tco2_insitu_temp'] - uws_sub['pH_init_talk_total_tco2_insitu_temp'].mean())/uws_sub['pH_init_talk_total_tco2_insitu_temp'].std(ddof=0))
    L = uws_sub['zscore'] < 2
    uws_sub = uws_sub[L]
    
    # Calculate offset between pH(TA/DIC) and pH(elec)
    uws_sub['offset'] = abs(uws_sub['pH_talk_tco2_insitu_temp'] - uws_sub['pH_init_talk_total_tco2_insitu_temp'])
    offset = uws_sub['offset'].mean()
    uws_sub['pH_elec_corr'] = uws_sub['pH_init_talk_total_tco2_insitu_temp'] + offset
    
    # Take the mean of the duplicates
    sub_points = uws_sub.groupby(by=['date_time']).mean().reset_index()
    
    # Check that datetime colums are datetime objects
    df['date_time'] = pd.to_datetime(df['date_time'])
    sub_points['date_time'] = pd.to_datetime(sub_points['date_time'])
    
    # Reindex sub_points so that date_time matches df(date_time)
    so279_nearest = df.set_index('date_time').reindex(sub_points.set_index('date_time').index, method='nearest').reset_index()
    
    # Add subpoints to df
    point_location = uws_sub['date_time'].tolist()
    sub_points['pH_optode'] = np.nan
    for location in point_location:
        sub_points.loc[sub_points['date_time']==location, 'pH_optode'] = sub_points['date_time'].map(so279_nearest.set_index('date_time')['pH_insitu'])
    
    # Subtract pH(elec, corr) from pH(optode)
    sub_points['diff'] = abs(sub_points['pH_elec_corr'] - sub_points['pH_optode'])
    
    # PCHIP difference points over date_time range in df
    sub_points.sort_values(by=['diff'], ascending=True)
    interp_obj = PchipInterpolator(sub_points['date_time'], sub_points['diff'], extrapolate=False)
    df['pchip_pH'] = interp_obj(df['date_time'])
    
    # Correct pH(optode) using PCHIP values
    df['pH_insitu_corr'] = df['pH_insitu'] - df['pchip_pH']
    
    # Compute simple moving average (SMA) over period of 30 minutes
    df['SMA'] = df['pH_insitu_corr'].rolling(60, min_periods=1).mean()
    
    return df