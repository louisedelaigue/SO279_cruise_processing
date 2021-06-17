from data_processing import read_pyrosci
from data_processing import logbook
from data_processing import smb
from data_processing import salinity
from data_processing import alkalinity
# from data_processing import pH

def raw_process(datasheet_filepath, txt_filepath, smb_filepath):
    data_dict, file_list = read_pyrosci(datasheet_filepath, txt_filepath)
    data = logbook(data_dict, file_list)
    df = smb(data, smb_filepath)
    return df

def bgc_process(df):
    dat_sal = salinity(df)
    dat_alk = alkalinity(dat_sal)
    # dat_pH = pH(dat_alk, uws_sub_filepath)
    return dat_alk
