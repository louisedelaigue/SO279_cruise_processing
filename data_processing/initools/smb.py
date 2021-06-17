import pandas as pd, numpy as np
import re
import datetime

def smb(data, smb_filepath):
    """Add relevant metadata (SMB) to PyroScience DataFrame."""
    # data = logbook(datasheet_filepath, txt_filepath)
    chunky = pd.read_csv('./data/SMB/smb_all_hr.dat',
                     chunksize=150000,
                     na_values=9999,
                     delimiter='\t',
                     encoding= 'unicode_escape',
                     low_memory=False)

    # create empty list to hold cleaned up chunks
    smb_list = []
    
    # rename temp_source column to python friendly, then only keep where 
    # temp_source has data, then store cleaned up chunks into smb_list
    for file in chunky:
        file = file.drop([file.index[0], file.index[1]])
        file.reset_index(drop=True)
        rn = {
           'SMB.RSSMB.T_SBE38':'SBE38_water_temp'
           }
        file.rename(rn, axis=1, inplace=True)
        # file.dropna(subset=['SBE38_water_temp'], inplace=True)
        smb_list.append(file)
    
    # create 1 df holding all cleaned up smb data
    smb = pd.concat(smb_list)
    
    # rename headers with python friendly names
    rn = {
          'date time':'date_time',
          'Weatherstation.PDWDC.Airtemperature':'WS_airtemp',
          'Weatherstation.PDWDC.Barometric':'WS_baro',
          'Weatherstation.PDWDC.Course':'WS_course',
          'Weatherstation.PDWDC.Date':'WS_date',
          'Weatherstation.PDWDC.Heading':'WS_heading',
          'Weatherstation.PDWDC.Humidity':'WS_humidity',
          'Weatherstation.PDWDC.Latitude':'WS_lat',
          'Weatherstation.PDWDC.Longitude':'WS_lon',
          'Weatherstation.PDWDC.Longwave':'WS_longwave',
          'Weatherstation.PDWDC.NormalizedTo':'WS_normto',
          'Weatherstation.PDWDC.Pyrogeometer':'WS_pyrogeometer',
          'Weatherstation.PDWDC.SensorValue':'WS_sensorvalue',
          'Weatherstation.PDWDC.Sentence':'WS_sentence',
          'Weatherstation.PDWDC.Shortwave':'WS_shortwave',
          'Weatherstation.PDWDC.Speed':'WS_speed',
          'Weatherstation.PDWDC.Timestamp':'WS_timestamp',
          'Weatherstation.PDWDC.Watertemperature':'WS_watertemp',
          'Weatherstation.PDWDC.Winddirection_rel':'WS_winddirection_rel',
          'Weatherstation.PDWDC.Winddirection_true':'WS_winddirection_true',
          'Weatherstation.PDWDC.Windspeed_rel':'WS_windspeed_rel',
          'Weatherstation.PDWDC.Windspeed_true':'WS_windspeed_true',
          'Weatherstation.PDWDC.Windspeed_true_Bft':'WS_windspeed_true_bft',
          'SMB.RSSMB.Chl':'chl',
          'SMB.RSSMB.C_SBE45':'SBE_45_C',
          'SMB.RSSMB.Date':'date',
          'SMB.RSSMB.Delay':'delay',
          'SMB.RSSMB.Depth':'depth',
          'SMB.RSSMB.EW':'ew',
          'SMB.RSSMB.Flow':'flow',
          'SMB.RSSMB.Latitude':'lat',
          'SMB.RSSMB.Longitude':'lon',
          'SMB.RSSMB.Name':'smb_name',
          'SMB.RSSMB.NS':'ns',
          'SMB.RSSMB.RVK':'system',
          'SMB.RSSMB.Sal_SBE45':'SBE45_sal',
          'SMB.RSSMB.Sentence':'sentence',
          'SMB.RSSMB.SN':'sn',
          'SMB.RSSMB.SV_SBE45':'SBE45_sv',
          'SMB.RSSMB.SV_insito':'insitu_sv',
          'SMB.RSSMB.Status':'smb_status',
          'SMB.RSSMB.SV_AML':'smb_sv_aml',
          'SMB.RSSMB.T_SBE45':'SBE45_water_temp',
          'SMB.RSSMB.Time':'smb_time',
          'SMB.RSSMB.Tur':'smb_tur'
          }
    
    smb.rename(rn, axis=1, inplace=True)
    
    # convert SMB date format to match PyroSci date format
    def date_convert(date_to_convert):
         return datetime.datetime.strptime(date_to_convert, '%Y/%m/%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
    smb['date_time'] = smb['date_time'].apply(date_convert)
    
    # merge SMB w/ PyroSci data
    df = data.merge(right=smb, 
                    how='inner',
                    on=['date_time'])
    
    # only keep datapoints where the difference between cell and outside temp is 
    # less than 1 degree Celcius
    df['temp_diff'] = abs(df.temp_cell - df.SBE38_water_temp)
    df = df[df['temp_diff'] < 1.0]    
    
    # convert column formats to be more useful for analysis
    df["pH"] = np.float64(df.pH_cell)
    df["date_time"] = pd.to_datetime(df.date_time, format='%d-%m-%Y %H:%M:%S')
    
    # format lat and lon columns (remove space)
    df['lat'] = df['lat'].apply(lambda x: ''.join(filter(None, x.split(' '))))
    df['lon'] = df['lon'].apply(lambda x: ''.join(filter(None, x.split(' '))))
    
    def dms_to_dd(lat_or_lon):
        """Convert coordinates from degrees to decimals."""
        deg, minutes, seconds, direction =  re.split('[°\.\'\"]', lat_or_lon)
        ans = (
            (float(deg) + float(minutes)/60) + float(seconds)/(60*60)
        ) * (-1 if direction in ['W', 'S'] else 1)
        return pd.Series({'decimals': ans})
    
    # convert lat/lon to decimals
    df['lat'] = df.lat.apply(dms_to_dd)
    df['lon'] = df.lon.apply(dms_to_dd)
    
    df.reset_index(inplace=True)
    return df