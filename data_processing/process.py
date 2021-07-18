from data_processing import read_pyrosci
from data_processing import logbook
from data_processing import smb
from data_processing import salinity
from data_processing import alkalinity

def raw_process(datasheet_filepath, txt_filepath, smb_filepath):
    data_dict, file_list = read_pyrosci(datasheet_filepath, txt_filepath)
    data = logbook(data_dict, file_list)
    df = smb(data, smb_filepath)
    return df

def bgc_process(df):
    dat_sal = salinity(df)
    dat_alk = alkalinity(dat_sal)
    return dat_alk
