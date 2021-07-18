import pandas as pd
# from data_processing import read_pyrosci

def logbook(data_dict, file_list):
    """Apply logbook notes from cruise SO279 to Pyroscience DataFrame."""
    # data_dict, file_list = read_pyrosci(datasheet_filepath, txt_filepath)
    # FILES CLEAN UP
    # only keep relevant data (apply cruise notes)
    # file 1 - 2020-12-08_204002_SO279_STN1_test - real data only up to 91740 seconds,
    # then CRM for 420 seconds, then pH2 until the end
    L = data_dict['2020-12-08_204002_SO279_STN1_test'].sec <= 91740
    data_dict['2020-12-08_204002_SO279_STN1_test'] = data_dict['2020-12-08_204002_SO279_STN1_test'][L]
    # substract one hour to put data back in UTC
    # This only needs to be done for this one file because the pH laptop time was adjusted
    # after this point to be consistent with UTC.
    sh = pd.Timedelta(1, unit='h')
    data_dict['2020-12-08_204002_SO279_STN1_test']['date_time'] = pd.to_datetime(data_dict['2020-12-08_204002_SO279_STN1_test'].date_time,
                          format='%d-%m-%Y %H:%M:%S.%f') - sh
    
    # file 2 - 2020-12-11_163148_NAPTRAM2020 - no end of sampling because problem 
    # with pump which ruined the optode cap on 14/12
    # data is unstable after 251791 seconds
    L = data_dict['2020-12-11_163148_NAPTRAM2020'].sec <= 251791
    data_dict['2020-12-11_163148_NAPTRAM2020'] = data_dict['2020-12-11_163148_NAPTRAM2020'][L]
    
    # file 3 - 2020-12-15_214136_NAPTRAM20202 - NO end of sampling because problem
    # with pump which ruined the optode cap on 16/12
    # data is unstable after 79290.5 seconds
    L = data_dict['2020-12-15_214136_NAPTRAM20202'].sec <= 79290.5
    data_dict['2020-12-15_214136_NAPTRAM20202'] = data_dict['2020-12-15_214136_NAPTRAM20202'][L]
    
    # file 4 - 2020-12-17_134828_NAPTRAM20203 - stopped working on 18/12 at 11am 
    # BUT no need to use logical array as stopped optode on time
    
    # file 5 - 2020-12-18_222759_NAPTRAM20204 - in pH2 after 16h50 on 20/12
    # data real data only up to 152521 seconds
    L = data_dict['2020-12-18_222759_NAPTRAM20204'].sec <= 152521
    data_dict['2020-12-18_222759_NAPTRAM20204'] = data_dict['2020-12-18_222759_NAPTRAM20204'][L]
    
    # file 6 - 2020-12-20_182318_NAPTRAM20205 - membrane pump needed maintenance
    # BUT no need to use logical array as stopped optode on time
    
    # file 7 - 2020-12-21_112915_NAPTRAM20206 - didn't recalibrate as left optode 
    # in UWS seawater - after optode stabilization, values look fine 27/12 - 9h30ish,
    # VTD turned the pump off without telling me
    # running a CRM6 as a sample to try and estimate drift [NEXT FILE]
    # real data only up to 511263 seconds
    L = data_dict['2020-12-21_112915_NAPTRAM20206'].sec <= 511263
    data_dict['2020-12-21_112915_NAPTRAM20206'] = data_dict['2020-12-21_112915_NAPTRAM20206'][L]
    
    # file 8 - 2020-12-27_101200_NAPTRAM2020CRM6 - VTD turned pump off
    # this file is a unique CRM to try and estimate drift in previous file
    
    # file 9 - 2020-12-28_151321_NAPTRAM20207 - in pH2 after 20h40 on 30/12
    # data real data only up to 195991 seconds
    L = data_dict['2020-12-28_151321_NAPTRAM20207'].sec <= 195991
    data_dict['2020-12-28_151321_NAPTRAM20207'] = data_dict['2020-12-28_151321_NAPTRAM20207'][L]
    
    # for all files, ignore first 20 min for optode stabilization
    for file in file_list:
        L = (data_dict[file].sec > 1200)
        data_dict[file] = data_dict[file][L]
        data_dict[file]['date_time'] = pd.to_datetime(data_dict[file].date_time,
                          format='%d-%m-%Y %H:%M:%S.%f')
    
    # turn dict into single df
    data = pd.concat(data_dict.values(), ignore_index=True)
    
    # drop ms
    data['date_time'] = data['date_time'].apply(lambda x: x.strftime('%d-%m-%Y %H:%M:%S'))
    
    return data