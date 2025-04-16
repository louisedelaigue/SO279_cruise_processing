import copy
import numpy as np, pandas as pd
from matplotlib import pyplot as plt
import PyCO2SYS as pyco2, koolstof as ks, calkulate as calk
from koolstof import vindta as ksv

# Import logfile and dbs file
logfile = ks.read_logfile(
    "data/VINDTA/logfile.bak",
    methods=[
        "3C standard separator",
        "3C standard separator modified LD",
        "3C standard separator modified LD temp",
    ],
)
dbs = ks.read_dbs("data/VINDTA/SO279.dbs") #

# Drop weird first row
dbs.drop(index=dbs.index[dbs.bottle == "03/02/21"], inplace=True)

# Create empty metadata columns
for meta in [
    "salinity",
    "dic_certified",
    "alkalinity_certified",
    "total_phosphate",
    "total_silicate",
    "total_ammonium",
]:
    dbs[meta] = np.nan

# Assign metadata values for CRMs
prefixes = ["CRM-189-", "CRM1-189-"] # typo in CRM name 'CRM1-189-0350-2'
dbs["crm"] = dbs.bottle.str.startswith("CRM")
dbs["crm_batch_189"] = dbs.bottle.str.startswith(tuple(prefixes))
dbs.loc[dbs.crm_batch_189, "dic_certified"] = 2009.48  # micromol/kg-sw
dbs.loc[dbs.crm_batch_189, "alkalinity_certified"] = 2205.26  # micromol/kg-sw
dbs.loc[dbs.crm_batch_189, "salinity"] = 33.494
dbs.loc[dbs.crm_batch_189, "total_phosphate"] = 0.45  # micromol/kg-sw
dbs.loc[dbs.crm_batch_189, "total_silicate"] = 2.1  # micromol/kg-sw
dbs.loc[dbs.crm_batch_189, "total_ammonium"] = 0  # micromol/kg-sw

# ---------------------------------------------------------vvv- UPDATE BELOW HERE! -vvv-
# Assign temperature = 25.0 for VINDTA analysis temperature
dbs["temperature_override"] = 25.0

# Add optional column 'file_good' to ignore popped CRMs (19/03)
dbs['file_good'] = True
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0226-2"]), "file_good"] = False
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0285-1"]), "file_good"] = False
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0285-2"]), "file_good"] = False
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0285-3"]), "file_good"] = False

# === CTD DATA
# Import CTD metadata
ctd_data = pd.read_csv('./data/processing/processed_ctd_data.csv')

# Extract station, niskin and duplicate numbers from bottle names in dbs file
sample_list = dbs['bottle'].tolist()
sample_station = []
sample_niskin = []
sample_duplicate = []
for sample in sample_list:
    if sample.startswith('STN'):
        stn = sample[3]
        nsk = sample[5:7]
        dup = sample[-1]
        sample_station.append(stn)
        sample_niskin.append(nsk)
        sample_duplicate.append(dup)
    else:
        sample_station.append('0')
        sample_niskin.append('0')
        sample_duplicate.append('0')

dbs['station_r'] = sample_station
dbs['niskin_r'] = sample_niskin
dbs['duplicate'] = sample_duplicate

dbs['niskin_r'] = dbs['niskin_r'].str.lstrip('0')
dbs['niskin_r'] = dbs['niskin_r'].replace('', '0')

dbs['stncode'] = dbs['station_r'] + dbs['niskin_r'] + dbs['duplicate']
dbs['stncode'] = dbs['stncode'].astype(str)
dbs.replace(to_replace='nannannan', value=np.nan, inplace=True)

# Remove bottle STN4N13-1 from TA/DIC sample list as bottle broke during sample processing on ship
ctd_data['stncode'] = ctd_data['stncode'].astype(str)
ctd_data['stncode'] = ctd_data['stncode'].map(lambda x: x.rstrip('.0'))
code_list = ctd_data['stncode']
L = code_list == '4131' 
code_list = code_list[~L].tolist() # drop bottle STN4N13-1 as bottle broke during processing
code_list = list(filter(lambda x: str(x) != 'nan', code_list))

# Assign salinity and nutrients to dbs columns
for code in code_list:
        dbs.loc[dbs['stncode']==code, 'salinity'] = ctd_data.loc[ctd_data['stncode']==code, 'salinity'].values
        dbs.loc[dbs['stncode']==code, 'total_silicate'] = ctd_data.loc[ctd_data['stncode']==code, 'total_silicate'].values
        dbs.loc[dbs['stncode']==code, 'total_phosphate'] = ctd_data.loc[ctd_data['stncode']==code, 'total_phosphate'].values

# === SUBSAMPLES
# Import subsamples metadata
subsamples = pd.read_csv('./data/processing/processed_uws_subsamples.csv')

# Assign metadata to samples (nutrients and salinity)
subsamples_list = subsamples.sample_id.tolist()
for subsample in subsamples_list:
    dbs.loc[dbs['bottle']==subsample, 'salinity'] = subsamples.loc[subsamples['sample_id']==subsample, 'salinity'].values
    dbs.loc[dbs['bottle']==subsample, 'total_phosphate'] = subsamples.loc[subsamples['sample_id']==subsample, 'total_phosphate'].values
    dbs.loc[dbs['bottle']==subsample, 'total_silicate'] = subsamples.loc[subsamples['sample_id']==subsample, 'total_silicate'].values
  
# === JUNKS
# Assign metadata for junks
dbs['salinity'] = dbs['salinity'].fillna(35)
dbs['total_phosphate'] = dbs['total_phosphate'].fillna(0)
dbs['total_silicate'] = dbs['total_silicate'].fillna(0)
dbs['total_ammonium'] = dbs['total_ammonium'].fillna(0)

# Assign alkalinity metadata
dbs["analyte_volume"] = 95.939  # TA pipette volume in ml
dbs["file_path"] = "data/VINDTA/SO279/"

# === LAB BOOK NOTES
# Change DIC cell name for 10/03
dbs.loc[dbs['analysis_datetime'].dt.day==10, 'dic_cell_id'] = 'C_Mar10-21_0803'

# Assign TA acid batches
dbs["analysis_batch"] = 0
dbs.loc[(dbs['analysis_datetime'].dt.day >= 10) & (dbs['analysis_datetime'].dt.day < 18), 'analysis_batch'] = 1
dbs.loc[(dbs['analysis_datetime'].dt.day >= 18) & (dbs['analysis_datetime'].dt.day < 27), 'analysis_batch'] = 2
dbs.loc[(dbs['analysis_datetime'].dt.day >= 27) & (dbs['analysis_datetime'].dt.day <= 30), 'analysis_batch'] = 3

# Cut points with weird blank behaviour
dbs['blank_good'] = True
dbs.loc[dbs['bottle'] == 'SOS037', 'blank_good'] = False
dbs.loc[dbs['bottle'] == 'SOS038', 'blank_good'] = False
dbs.loc[dbs['bottle'] == 'SOS039', 'blank_good'] = False
dbs.loc[dbs['bottle'] == 'CRM-189-0531-2', 'blank_good'] = True
dbs.loc[dbs['bottle'] == 'CRM-189-0776-2', 'blank_good'] = True

dbs.loc[dbs['bottle'] == 'CRM-189-0836-1', 'blank_good'] = False
dbs.loc[dbs['bottle'] == 'STN9N18-2', 'blank_good'] = False
dbs.loc[dbs['bottle'] == 'STN9N09-1', 'blank_good'] = False
dbs.loc[dbs['bottle'] == 'CRM-189-0464-2', 'blank_good'] = False

# Select which DIC CRMs to use/avoid for calibration --- only fresh bottles
dbs["k_dic_good"] = dbs.crm & dbs.bottle.str.endswith("-1")
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0226-1"]), "k_dic_good"] = True
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0285-1"]), "k_dic_good"] = False
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0285-4"]), "k_dic_good"] = False
dbs.loc[np.isin(dbs.bottle, ['CRM-189-0464-2']), "k_dic_good"] = False

# Select which TA CRMs to use/avoid for calibration
dbs["reference_good"] = ~np.isnan(dbs.alkalinity_certified)
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0963-1"]), "reference_good"] = False
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0350-2"]), "reference_good"] = True
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0226-1"]), "reference_good"] = False
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0285-4"]), "reference_good"] = True
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0464-2"]), "reference_good"] = True
dbs.loc[np.isin(dbs.bottle, ["CRM-189-1024-1"]), "reference_good"] = False
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0963-2"]), "reference_good"] = False
dbs.loc[np.isin(dbs.bottle, ["CRM-189-0775-1"]), "reference_good"] = False

# ---------------------------------------------------------^^^- UPDATE ABOVE HERE! -^^^-
# Get blanks and apply correction
# dbs.get_blank_corrections()
# dbs.plot_blanks(figure_path="figs/vindta/dic_blanks/")

sessions = ksv.blank_correction(
    dbs,
    logfile,
    blank_col="blank",
    counts_col="counts",
    runtime_col="run_time",
    session_col="dic_cell_id",
    use_from=6,
)

ksv.plot_increments(dbs, logfile, use_from=6)
ksv.plot_blanks(dbs, sessions)

# Calibrate
ksv.calibrate_dic(dbs, sessions)

# Plot calibration factors
ksv.plot_k_dic(dbs, sessions, show_ignored=True)

# Plot CRM offsets
ksv.plot_dic_offset(dbs, sessions)

# Calibrate DIC and plot calibration
# dbs.calibrate_dic()
# dic_sessions = copy.deepcopy(dbs.sessions)
# # dbs.plot_k_dic(figure_path="figs/vindta/")
# # dbs.plot_dic_offset(figure_path="figs/vindta/")

# # Calibrate and solve alkalinity and plot calibration
calk.io.get_VINDTA_filenames(dbs)
calk.dataset.calibrate(dbs)
calk.dataset.solve(dbs)
calk.plot.titrant_molinity(dbs, figure_fname="figs/vindta/titrant_molinity.png", show_bad=False)
calk.plot.alkalinity_offset(dbs, figure_fname="figs/vindta/alkalinity_offset.png", show_bad=False)

# Demote dbs to a standard DataFrame
dbs = pd.DataFrame(dbs)

# Compare initial pH measurement with PyCO2SYS value from TA & DIC
dbs["pH_alk_dic_25"] = pyco2.sys(
    dbs.alkalinity.to_numpy(),
    dbs.dic.to_numpy(),
    1,
    2,
    temperature=dbs.temperature_initial.to_numpy(),
    salinity=dbs.salinity.to_numpy(),
    total_phosphate=dbs.total_phosphate.to_numpy(),
    total_silicate=dbs.total_silicate.to_numpy(),
)["pH_free"]

# Plot pH comparison
L = (dbs['bottle'].str.startswith('SOS'))
fig, ax = plt.subplots(dpi=300)
ax.scatter("pH_alk_dic_25", "pH_initial", data=dbs[~L], s=20, alpha=0.5)
ax.set_aspect(1)
ax.grid(alpha=0.3)
ax.set_xlabel("pH from DIC and alkalinity")
ax.set_ylabel("pH from electrode")
pH_range = [
    min(dbs[L].pH_alk_dic_25.min(), dbs[L].pH_initial.min()),
    max(dbs[L].pH_alk_dic_25.max(), dbs[L].pH_initial.max()),
]
ax.plot(pH_range, pH_range, lw=0.8)
plt.savefig("figs/vindta/pH_comparison.png")

# ---------------------------------------------------------vvv- UPDATE BELOW HERE! -vvv-
# Double check CRMs
L = (dbs['crm_batch_189'] == True)
CRMs = pd.concat([dbs['bottle'][L],
                    dbs['dic_cell_id'][L],
                    dbs['dic'][L],
                    dbs['k_dic_good'][L],
                    dbs['blank_good'][L],
                    dbs['alkalinity'][L],
                    dbs['reference_good'][L],
                    dbs['titrant_molinity_here'][L]],
                    axis=1)

# Correct bottle name typos in dbs
dbs.loc[dbs['bottle']=='27b2', 'bottle'] = '27b'
dbs.loc[dbs['bottle']=='STN6N23-2_2', 'bottle'] = 'STN6N23-2' # twisted line
dbs.loc[dbs['bottle']=='STN3N07-2_2', 'bottle'] = 'STN3N07-2' # twisted line

# Add a Flag column for TA and DIC
# Quality flag convention: 2 = acceptable, 3 = questionable, 4 = known bad, 9 = missing value (lab issue)
dbs['flag_talk'] = 2
dbs['flag_tco2'] = 2
dbs.loc[dbs['analysis_datetime'].dt.day==11, 'flag_talk'] = 3    # uncertain TA values - rinsing solution tube out of solution
dbs.loc[dbs['analysis_datetime'].dt.day==16, 'flag_tco2'] = 3    # uncertain DIC values - forgot stirrer in coulometer cell
dbs.loc[dbs['bottle'] == '24a', 'flag_tco2'] = 3                 # weird blank behaviour
dbs.loc[dbs['bottle'] == '15b', 'flag_tco2'] = 3                 # weird blank behaviour
dbs.loc[dbs['bottle'] == '3a', 'flag_tco2'] = 3                  # weird blank behaviour
dbs.loc[dbs['bottle'] == 'CRM-189-0775-1', 'flag_tco2'] = 3      # weird blank behaviour
dbs.loc[dbs['bottle'] == 'CRM-189-1086-2', 'flag_tco2'] = 3      # weird blank behaviour
dbs.loc[dbs['bottle'] == 'STN5N07-2', 'flag_tco2'] = 3           # bad blank_here vs blank
dbs.loc[dbs['bottle'] == 'STN3N07-2', 'flag_tco2'] = 3           # bad blank_here vs blank
dbs.loc[dbs['bottle'] == 'STN6N19-1', 'flag_tco2'] = 3           # bad blank_here vs blank
dbs.loc[dbs['bottle'] == 'STN1N10-1', 'flag_tco2'] = 3           # bad blank_here vs blank
dbs.loc[dbs['bottle'] == 'STN3N24-1', 'flag_tco2'] = 3           # bad blank_here vs blank
dbs.loc[dbs['bottle'] == '13a', 'flag_talk'] = 4                 # TA didn't fill enough, bottle popped
dbs.loc[dbs['bottle'] == 'SOS062', 'flag_talk'] = 4              # TA didn't fill enough, bottle popped
dbs.loc[dbs['bottle'] == 'CRM-189-0226-1', 'flag_talk'] = 4      # bad value
dbs.loc[dbs['bottle'] == 'CCRM-189-0963-1', 'flag_talk'] = 4     # bad value
dbs.loc[dbs['bottle'] == '13a', 'flag_talk'] = 9                 # TA didn't fill enough, bottle popped
dbs.loc[dbs['bottle'] == 'SOS062', 'flag_talk'] = 9              # TA didn't fill enough, bottle popped

# === SUBSAMPLES PROCESSING
# == ALKALINITY
# Create sub dataframe to hold subsampled alkalinity duplicates
subsamples_data_talk = pd.DataFrame()
subsamples_data_talk['sample_id'] = subsamples['sample_id'].astype(str)
subsamples_data_talk['analysis_datetime'] = np.nan
subsamples_data_talk['depth'] = 3
subsamples_data_talk['dupcode'] = np.nan
subsamples_data_talk['talk'] = np.nan
subsamples_data_talk['flag_talk'] = np.nan
subsamples_data_talk['difference'] = np.nan
subsamples_data_talk['number_of_duplicates'] = np.nan
subsamples_data_talk['pH_initial_talk'] = np.nan

# Import alkalinity, salinity and flags from dbs to sub dataframe
subsamples_list = subsamples['sample_id'].unique().tolist()
for subsample in subsamples_list:
    subsamples_data_talk.loc[subsamples_data_talk['sample_id']==subsample, 'talk'] = dbs.loc[dbs['bottle']==subsample, 'alkalinity'].values
    subsamples_data_talk.loc[subsamples_data_talk['sample_id']==subsample, 'flag_talk'] = dbs.loc[dbs['bottle']==subsample, 'flag_talk'].values
    subsamples_data_talk.loc[subsamples_data_talk['sample_id']==subsample, 'pH_initial_talk'] = dbs.loc[dbs['bottle']==subsample, 'pH_initial'].values
    subsamples_data_talk.loc[subsamples_data_talk['sample_id']==subsample, 'analysis_datetime'] = dbs.loc[dbs['bottle']==subsample, 'analysis_datetime'].values
    if len(subsample) == 2:
        subsamples_data_talk.loc[subsamples_data_talk['sample_id']==subsample, 'dupcode'] = subsample[0]
    else:
        subsamples_data_talk.loc[subsamples_data_talk['sample_id']==subsample, 'dupcode'] = subsample[:2]

# Convert datetime object
subsamples_data_talk['analysis_datetime'] = pd.to_datetime(subsamples_data_talk['analysis_datetime'])

# Convert duplicate code to integer
subsamples_data_talk['dupcode'] = subsamples_data_talk['dupcode'].astype(int)

# Compute differences for each duplicate pair
duplicate_list = subsamples_data_talk['dupcode'].unique().tolist()
for duplicate in duplicate_list:
    temp = (subsamples_data_talk.loc[subsamples_data_talk['dupcode']==duplicate]).reset_index(drop=True)
    subsamples_data_talk.loc[subsamples_data_talk['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['talk']))[0]
    subsamples_data_talk.loc[subsamples_data_talk['dupcode']==duplicate, 'number_of_duplicates'] = 2

# Remove bad duplicate from pairs with flag = 2 and flag = 3
# /!\ if difference < 4 umol/kg, take the average of the pair and give a flag = 3
# /!\ if difference > 4 umol/kg, keep flag = 2 duplicate and change flag to = 3
good_duplicates = ['3b',
                  '13b',
                  '15a',
                  '16b',
                  '17b',
                  '22a',
                  '24b'
                  ]

for duplicate in good_duplicates:
    subsamples_data_talk.loc[subsamples_data_talk['sample_id']==duplicate, 'flag_talk'] = 3
    subsamples_data_talk.loc[subsamples_data_talk['sample_id']==duplicate, 'difference'] = np.nan
    subsamples_data_talk.loc[subsamples_data_talk['sample_id']==duplicate, 'number_of_duplicates'] = 1

bad_duplicates = ['3a',
                  '13a',
                  '15b',
                  '16a',    # outlier in pH comparison plot
                  '17a',
                  '22b',
                  '24a'
                  ]

for duplicate in bad_duplicates:
    subsamples_data_talk = subsamples_data_talk[subsamples_data_talk['sample_id'] != duplicate]

# Calculate precision number
P_subsample_talk = (np.sqrt(np.pi)/2) * (np.abs(subsamples_data_talk['difference'].mean()))
print('Precision for subsamples alkalinity is {}.'.format(round(P_subsample_talk, 3)))

# Plot TA vs. depth to check for outliers
fig, ax = plt.subplots(dpi=300)
ax.scatter("talk",
            "depth",
            data=subsamples_data_talk,
            c='flag_talk',
            s=20,
            alpha=0.5)
ax.grid(alpha=0.3)
ax.set_xlabel("TA")
ax.set_ylabel("Depth (m)")
ax.set_title('Subsampled duplicates for TA')

# From plot, create internal/external flag columns
# where flag = 2 if difference is different than nan
# ^^^ above rows were originally = 3 because of stirrer issue on 16/03
# but plot suggests values are fine
# Remaining flag = 3 indicate only 1 duplicate was kept in a pair, due to 
# lab issue (inc. blank behaviour) or obvious outlier
rn = {
      'dupcode':'sample',
      'flag_talk':'internal_flag'
      }
subsamples_data_talk.rename(rn, axis=1, inplace=True)
subsamples_data_talk['flag_talk'] = subsamples_data_talk['internal_flag'].copy()

subsamples_data_talk.loc[(subsamples_data_talk['analysis_datetime'].dt.day==11) & (subsamples_data_talk['difference'].notnull()), 'flag_talk'] = 2

# Groupby to average remaining subsamples
# /!\ if duplicate pair includes flag = 2 and flag = 3, final flag = 3
subsamples_data_talk_grouped = subsamples_data_talk.groupby('sample', as_index=False).mean()
subsamples_data_talk_grouped.loc[subsamples_data_talk_grouped['flag_talk']==2.5, 'flag_talk'] = 3

# Plot TA vs. depth for final overview
fig, ax = plt.subplots(dpi=300)
ax.scatter('talk',
           'depth',
           data=subsamples_data_talk_grouped,
           c='flag_talk',
           s=20,
           alpha=0.5
           )
ax.grid(alpha=0.3)
ax.set_xlabel('TA')
ax.set_ylabel('Depth (m)')
ax.set_title('Final processing for subsamples TA')

# == DIC
# Create sub dataframe to hold subsampled dic duplicates
subsamples_data_tco2 = pd.DataFrame()
subsamples_data_tco2['sample_id'] = subsamples['sample_id'].astype(str)
subsamples_data_tco2['analysis_datetime'] = np.nan
subsamples_data_tco2['depth'] = 3
subsamples_data_tco2['dupcode'] = np.nan
subsamples_data_tco2['tco2'] = np.nan
subsamples_data_tco2['flag_tco2'] = np.nan
subsamples_data_tco2['difference'] = np.nan
subsamples_data_tco2['number_of_duplicates'] = np.nan

# Import DIC and flags from dbs to sub dataframe
for subsample in subsamples_list:
    subsamples_data_tco2.loc[subsamples_data_tco2['sample_id']==subsample, 'tco2'] = dbs.loc[dbs['bottle']==subsample, 'dic'].values
    subsamples_data_tco2.loc[subsamples_data_tco2['sample_id']==subsample, 'flag_tco2'] = dbs.loc[dbs['bottle']==subsample, 'flag_tco2'].values
    subsamples_data_tco2.loc[subsamples_data_tco2['sample_id']==subsample, 'analysis_datetime'] = dbs.loc[dbs['bottle']==subsample, 'analysis_datetime'].values
    if len(subsample) == 2:
        subsamples_data_tco2.loc[subsamples_data_tco2['sample_id']==subsample, 'dupcode'] = subsample[0]
    else:
        subsamples_data_tco2.loc[subsamples_data_tco2['sample_id']==subsample, 'dupcode'] = subsample[:2]

# Convert datetime object
subsamples_data_tco2['analysis_datetime'] = pd.to_datetime(subsamples_data_tco2['analysis_datetime'])

# Convert duplicate code to integer
subsamples_data_tco2['dupcode'] = subsamples_data_tco2['dupcode'].astype(int)

# Compute differences for each duplicate pair
duplicate_list = subsamples_data_tco2['dupcode'].unique().tolist()
for duplicate in duplicate_list:
    temp = subsamples_data_tco2.loc[subsamples_data_tco2['dupcode']==duplicate]
    subsamples_data_tco2.loc[subsamples_data_tco2['dupcode']==duplicate, 'difference'] = np.abs(np.diff(temp['tco2']))[0]
    subsamples_data_tco2.loc[subsamples_data_tco2['dupcode']==duplicate, 'number_of_duplicates'] = 2

# Remove bad duplicate from pairs with flag = 2 and flag = 3
# /!\ if difference < 4 umol/kg, take the average of the pair and give a flag = 3
# /!\ if difference > 4 umol/kg, keep flag = 2 duplicate and change flag to = 3
good_duplicates = ['3b',
                  '6b',
                  '18b',
                  '23a',
                  '37b',
                  '38b',
                  '42b',
                  '50a'
                  ]

for duplicate in good_duplicates:
    subsamples_data_tco2.loc[subsamples_data_tco2['sample_id']==duplicate, 'flag_tco2'] = 3
    subsamples_data_tco2.loc[subsamples_data_tco2['sample_id']==duplicate, 'difference'] = np.nan
    subsamples_data_tco2.loc[subsamples_data_tco2['sample_id']==duplicate, 'number_of_duplicates'] = 1

bad_duplicates = ['3a', # outlier in pH comparison plot
                  '6a',
                  '18a',
                  '23b',
                  '37a',
                  '38a',
                  '42a',
                  '50b'
                  ]

for duplicate in bad_duplicates:
    subsamples_data_tco2 = subsamples_data_tco2[subsamples_data_tco2['sample_id'] != duplicate]

# Calculate precision number for DIC
P_subsample_tco2 = (np.sqrt(np.pi)/2) * (np.abs(subsamples_data_tco2['difference'].mean()))
print('Precision for subsamples DIC is {}.'.format(round(P_subsample_tco2, 3)))
# /!\ P prior to processing is 4.426

# Plot DIC vs. depth to check for outliers
fig, ax = plt.subplots(dpi=300)
ax.scatter('tco2',
           'depth',
           data=subsamples_data_tco2,
           c='flag_tco2',
           s=20,
           alpha=0.5
           )
ax.grid(alpha=0.3)
ax.set_xlabel("DIC")
ax.set_ylabel("Depth (m)")
ax.set_title('Subsampled duplicates for DIC')

# From plot, create internal/external flag columns
# where flag = 2 if difference is different than nan
# ^^^ above rows were originally = 3 because of stirrer issue on 16/03
# but plot suggests values are fine
# Remaining flag = 3 indicate only 1 duplicate was kept in a pair, due to 
# lab issue (inc. blank behaviour) or obvious outlier
rn = {
      'dupcode':'sample',
      'flag_tco2':'internal_flag'
      }
subsamples_data_tco2.rename(rn, axis=1, inplace=True)
subsamples_data_tco2['flag_tco2'] = subsamples_data_tco2['internal_flag'].copy()

subsamples_data_tco2.loc[(subsamples_data_tco2['analysis_datetime'].dt.day==16) & (subsamples_data_tco2['difference'].notnull()), 'flag_tco2'] = 2

# Groupby to average remaining subsamples
# /!\ if duplicate pair includes flag = 2 and flag = 3, final flag = 3
subsamples_data_tco2_grouped = subsamples_data_tco2.groupby(by='sample', as_index=False).mean()
subsamples_data_tco2_grouped.loc[subsamples_data_tco2_grouped['internal_flag']==2.5, 'internal_flag'] = 3
subsamples_data_tco2_grouped.loc[subsamples_data_tco2_grouped['flag_tco2']==2.5, 'flag_tco2'] = 3

# Plot DIC vs. depth for final overview
fig, ax = plt.subplots(dpi=300)
ax.scatter('tco2',
           'depth',
           data=subsamples_data_tco2_grouped,
           c='flag_tco2',
           s=20,
           alpha=0.5
           )
ax.grid(alpha=0.3)
ax.set_xlabel('DIC')
ax.set_ylabel('Depth (m)')
ax.set_title('Final processing for subsamples DIC')

# == FINAL DATASET
# Add sample column
subsamples['dupcode'] = np.nan
for subsample in subsamples_list:
    if len(subsample) == 2:
        subsamples.loc[subsamples['sample_id']==subsample, 'dupcode'] = subsample[0]
    else:
        subsamples.loc[subsamples['sample_id']==subsample, 'dupcode'] = subsample[:2]
subsamples['dupcode'] = subsamples['dupcode'].astype(int)

# Give first sample same date_time (4 min difference)
subsamples.loc[subsamples['sample_id']=='1b', 'date_time'] = subsamples.loc[subsamples['sample_id']=='1a', 'date_time'].values

# Groupby subsample dataset to keep one row per sample
subsamples = subsamples.groupby('date_time', as_index=False).mean()

# Add DIC data
subsamples = subsamples.merge(subsamples_data_tco2_grouped, how='inner', left_on='dupcode', right_on='sample')

# Add TA data
subsamples = subsamples.merge(subsamples_data_talk_grouped, how='inner', left_on='dupcode', right_on='sample')

# Drop useless columns
subsamples.drop(columns=['sample_x',
                         'sample_y',
                         'depth_y'], inplace=True)

# Rename columns
rn = {
      'dupcode':'sample',
      'depth_x':'depth',
      'internal_flag_x':'internal_flag_tco2',
      'difference_x':'duplicate_difference_tco2',
      'number_of_duplicates_x':'n_duplicates_tco2',
      'internal_flag_y':'internal_flag_talk',
      'difference_y':'duplicate_difference_talk',
      'number_of_duplicates_y':'n_duplicates_talk'
      }

subsamples.rename(rn, axis=1, inplace=True)

# === CTD PROCESSING
# ALKALINITY
# Create sub dataframe to hold CTD alkalinity duplicates
ctd_data_talk = pd.DataFrame()
ctd_data_talk['station'] = ctd_data['station']
ctd_data_talk['niskin'] = ctd_data['niskin']
ctd_data_talk['stncode'] = ctd_data['stncode']
ctd_data_talk['depth'] = ctd_data['depth']
ctd_data_talk['talk'] = np.nan
ctd_data_talk['flag_talk'] = np.nan
ctd_data_talk['pH_initial_talk'] = np.nan
ctd_data_talk['difference'] = np.nan
ctd_data_talk['number_of_duplicates'] = np.nan

# Import alkalinity and flags from dbs to sub dataframe
for code in code_list:
    ctd_data_talk.loc[ctd_data_talk['stncode']==code, 'talk'] =  dbs.loc[dbs['stncode']==code, 'alkalinity'].values
    ctd_data_talk.loc[ctd_data_talk['stncode']==code, 'flag_talk'] = dbs.loc[dbs['stncode']==code, 'flag_talk'].values
    ctd_data_talk.loc[ctd_data_talk['stncode']==code, 'pH_initial_talk'] = dbs.loc[dbs['stncode']==code, 'pH_initial'].values

# Compute differences for each duplicate pair
ctd_data_talk['station'] = ctd_data_talk['station'].astype(str)
ctd_data_talk['niskin'] = ctd_data_talk['niskin'].astype(str)
ctd_data_talk['dupcode'] = ctd_data_talk['station'] + ctd_data_talk['niskin']

sample_list = ctd_data_talk['dupcode'].unique().tolist()
for sample in sample_list:
    L = ctd_data_talk['dupcode'] == sample
    if ctd_data_talk['dupcode'][L].count() == 1:
        ctd_data_talk.loc[ctd_data_talk['dupcode']==sample, 'difference'] = np.nan
        ctd_data_talk.loc[ctd_data_talk['dupcode']==sample, 'number_of_duplicates'] = 1
    else:
        temp = ctd_data_talk[L]
        ctd_data_talk.loc[ctd_data_talk['dupcode']==sample, 'difference'] = np.abs(np.diff(temp['talk']))[0]
        ctd_data_talk.loc[ctd_data_talk['dupcode']==sample, 'number_of_duplicates'] = 2
        
# Remove sample '4131' as no TA/DIC (broken bottle)
# Assign difference = nan and number of duplicates = 1 for other duplicate of pair
ctd_data_talk.dropna(subset=['talk'], how='all', inplace=True)
ctd_data_talk.loc[ctd_data_talk['dupcode']=='4132', 'difference'] = np.nan
ctd_data_talk.loc[ctd_data_talk['dupcode']=='413', 'number_of_duplicates'] = 1

# Calculate precision number for TA (CTD data)
P_ctd_talk = (np.sqrt(np.pi)/2) * (np.abs(ctd_data_talk['difference'].mean()))
print('Precision for CTD alkalinity is {}.'.format(round(P_ctd_talk, 3)))

# Groupby to average remaining subsamples
# /!\ if duplicate pair includes flag = 2 and flag = 3, final flag = 3
# /!\ format change for station and niskin columns otherwise dropped during groupby
ctd_data_talk['station'] = ctd_data_talk['station'].astype(int)
ctd_data_talk['niskin'] = ctd_data_talk['niskin'].astype(int)
ctd_data_talk_grouped = ctd_data_talk.groupby('dupcode').mean()

# Plot TA vs. depth to check for outliers
fig, ax = plt.subplots(dpi=300)
ax.scatter('talk', 'depth', data=ctd_data_talk_grouped, c='flag_talk', s=20, alpha=0.5)
ax.grid(alpha=0.3)
ax.set_xlabel('TA')
ax.set_ylabel('Depth (m)')
ax.set_title('Final processing for CTD TA')
plt.gca().invert_yaxis()

# === CTD PROCESSING
# == DIC
# Create sub dataframe to hold CTD DIC duplicates
ctd_data_tco2 = pd.DataFrame()
ctd_data_tco2['station'] = ctd_data['station']
ctd_data_tco2['niskin'] = ctd_data['niskin']
ctd_data_tco2['depth'] = ctd_data['depth']
ctd_data_tco2['stncode'] = ctd_data['stncode']
ctd_data_tco2['tco2'] = np.nan
ctd_data_tco2['flag_tco2'] = np.nan
ctd_data_tco2['difference'] = np.nan
ctd_data_tco2['number_of_duplicates'] = np.nan

# Import DIC and flags from dbs to sub dataframe
for code in code_list:
    ctd_data_tco2.loc[ctd_data_tco2['stncode']==code, 'tco2'] =  dbs.loc[dbs['stncode']==code, 'dic'].values
    ctd_data_tco2.loc[ctd_data_tco2['stncode']==code, 'flag_tco2'] = dbs.loc[dbs['stncode']==code, 'flag_tco2'].values

# Keep flag = 2
# /!\ this removes STN3N07-2 and STN5N07-2 which both have weird blank behaviours
L = ctd_data_tco2['flag_tco2'] == 2
ctd_data_tco2 = ctd_data_tco2[L]

# Compute differences for each duplicate pair
ctd_data_tco2['station'] = ctd_data_tco2['station'].astype(str)
ctd_data_tco2['niskin'] = ctd_data_tco2['niskin'].astype(str)
ctd_data_tco2['dupcode'] = ctd_data_tco2['station'] + ctd_data_tco2['niskin']
sample_list = ctd_data_tco2['dupcode'].unique().tolist()

for sample in sample_list:
    L = ctd_data_tco2['dupcode'] == sample
    if ctd_data_tco2['dupcode'][L].count() == 1:
        ctd_data_tco2.loc[ctd_data_tco2['dupcode']==sample, 'difference'] = np.nan
        ctd_data_tco2.loc[ctd_data_tco2['dupcode']==sample, 'number_of_duplicates'] = 1
    else:
        temp = ctd_data_tco2[L]
        ctd_data_tco2.loc[ctd_data_tco2['dupcode']==sample, 'difference'] = np.abs(np.diff(temp['tco2']))[0]
        ctd_data_tco2.loc[ctd_data_tco2['dupcode']==sample, 'number_of_duplicates'] = 2

# Remove sample '4131' as no TA/DIC (broken bottle)
# Assign difference = nan and number of duplicates = 1 for other duplicate of pair
ctd_data_tco2.dropna(subset=['tco2'], how='all', inplace=True)
ctd_data_tco2.loc[ctd_data_tco2['dupcode']=='4132', 'difference'] = np.nan
ctd_data_tco2.loc[ctd_data_tco2['dupcode']=='413', 'number_of_duplicates'] = 1

# Calculate precision number for DIC (CTD data)
P_ctd_tco2 = (np.sqrt(np.pi)/2) * (np.abs(ctd_data_tco2['difference'].mean()))
print('Precision for CTD DIC is {}.'.format(round(P_ctd_tco2, 3)))

# Groupby to average remaining subsamples
# /!\ if duplicate pair includes flag = 2 and flag = 3, final flag = 3
# /!\ format change for station and niskin columns otherwise dropped during groupby
ctd_data_tco2['station'] = ctd_data_tco2['station'].astype(int) # otherwise dropped during groupby
ctd_data_tco2['niskin'] = ctd_data_tco2['niskin'].astype(int) # otherwise dropped during groupby
ctd_data_tco2_grouped = ctd_data_tco2.groupby('dupcode').mean()

# Plot DIC vs. depth to check for outliers
fig, ax = plt.subplots(dpi=300)
ax.scatter('tco2', 'depth', data=ctd_data_tco2_grouped, c='flag_tco2', s=20, alpha=0.5)
ax.grid(alpha=0.3)
ax.set_xlabel('DIC')
ax.set_ylabel('Depth (m)')
ax.set_title('Final processing for CTD DIC')
plt.gca().invert_yaxis()

# == FINAL DATASET
# Groupby CTD dataset to keep one row per sample
ctd_data['station'] = ctd_data['station'].astype(int) # otherwise dropped during groupby
ctd_data['niskin'] = ctd_data['niskin'].astype(int) # otherwise dropped during groupby
ctd_data = ctd_data.groupby(['station', 'niskin'], as_index=False).mean()

# Drop duplicate column
ctd_data.drop(columns=['duplicate'], inplace=True)

# Add DIC data
ctd_data = ctd_data.merge(ctd_data_tco2_grouped, how='outer', left_on=['station', 'niskin'], right_on=['station', 'niskin'])

# Add TA data
ctd_data = ctd_data.merge(ctd_data_talk_grouped, how='outer', left_on=['station', 'niskin'], right_on=['station', 'niskin'])

# Drop duplicated columns
ctd_data.drop(columns=['depth_y'], inplace=True)

rn = {
      'depth_x':'depth',
      'difference_x':'duplicate_difference_tco2',
      'number_of_duplicates_x':'n_duplicates_tco2',
      'difference_y':'duplicate_difference_talk',
      'number_of_duplicates_y':'n_duplicates_talk'
      }

ctd_data.rename(rn, axis=1, inplace=True)


# Save CTD and UWS datasets to csv.
subsamples.to_csv('./data/processing/processed_vindta_subsamples.csv', index=False)
ctd_data.to_csv('./data/processing/processed_vindta_ctd.csv', index=False)
dbs.to_csv('./data/processing/dbs.csv', index=False)
