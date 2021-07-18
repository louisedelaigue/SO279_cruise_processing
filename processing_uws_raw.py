import data_processing as dp

# Import raw continuous optode measurements (optional: process it // time-consuming)
df = dp.raw_process('./data/pH/UWS/UWS_continuous_file_list.xlsx', './data/pH/UWS', 'data/SMB/smb_all_hr.dat')
# Save pre BGC processing data
df.to_csv('./data/processing/preprocessing_uws_data.csv', index=False)

# Correct salinity and estimate alkalinity
df = dp.bgc_process(df)
# Save raw UWS data
df.to_csv('./data/processing/raw_uws_data.csv', index=False)
