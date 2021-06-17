# Data processing for SO279 cruise

<img src=Capture.JPG width="500" height="500"/>

## Data
Data used in this repo come from the SO279 cruise across the North Atlantic in the Azores Region (December 2020). Discrete samples were taken from the CTD (77 measurements, _SO279_CTD_data.csv_) and the underway water system (UWS; 51 measurements, _SO279_subsamples_data.csv_). A high-resolution (1 measurement every 30 seconds) time series of surface ocean pH cross-calibrated using UWS discrete samples is also available (_SO279_UWS_data.csv_).

CTD and UWS discrete samples dataset contain respectively 77 measurements (all from the CTD rosette) and 51 measurements (all from the UWS) of seawater dissolved inorganic carbon (DIC) , total alkalinity (TA) and nutrients (Si, PO4, NH4, NO3 and NO2). The UWS time series dataset contains a high-resolution (1 measurement every 30 seconds) time series of surface ocean pH measured with a PyroScience fiber-based pH sensor (PHROBSC-PK8T) and cross-calibrated using discrete carbonate system observations (total alkalinity, dissolved inorganic carbon and nutrients). Samples were collected during R/V Sonne cruise SO279 in Dec 2020 in the Azores Region of the North Atlantic Ocean, as part of the NAPTRAM research programme to build an understanding of the transport pathways of plastic and microplastic debris in the North Atlantic. Measurements were carried out using VINDTA 3C instruments (#017, Marianda, Germany) at the NIOZ Royal Netherlands Institute for Sea Research. Bad results resulting from technical issues during analysis have been removed from these results, so there are no recognised issues. The data were collected as part of an international effort from the JPI Oceans project HOTMIC and BMBF project PLASTISEA , and forms a joint effort of HOTMIC and PLASTISEA researchers from a range of countries and institutes. The NIOZ created the metadata entry and is responsible for holding master copies of the data.

## Data processing
Scripts below are used in the processing of CTD and UWS data. Each script's function is briefly highlighted and variables are listed. More details can be found in _methods.docx_ (main folder, to be updated). 

All calculations pertainting to the carbonate system were done using the Python toolbox [PyCO2SYS](https://pyco2sys.readthedocs.io/en/latest/) and default carbonic acid dissociation constants (Sulpis et al., 2020).

All column header abbreviations and variable flags follow _Best Practice Data Standards for Discrete Chemical Oceanographic Observations_ (Jiang et al, in prep).

### CTD discrete samples
Final dataset can be found in _'./data'_ as **SO279_CTD_data.csv**. Dataset includes the following variables:
* EXPOCODE
* Cruise_ID
* Year_UTC
* Month_UTC
* Day_UTC
* Time_UTC
* Latitude
* Longitude
* Depth
* CTDTEMP_ITS90
* CTDSAL_PSS78
* DIC
* DIC_flag
* TA
* TA_flag
* Silicate
* Silicate_flag
* Phosphate
* Phosphate_flag
* Nitrate
* Nitrate_flag
* Nitrite
* Nitrite_flag
* Nitrate_and_Nitrite
* Nitrate_and_Nitrite_flag
* Ammonium
* Ammonim_flag
    
Processing steps include the following scripts and order:
1. _processing_ctd_raw.py_: Retrieves CTD data for all Niskins and adds nutrient data.

2. _processing_vindta.py_: Processes TA and DIC lab analysis. Calculates pH(TA, DIC, 25, free scale), pH(initial during TA titration, 25, free scale) and pH(TA, DIC, in-situ temperature, total scale). The following variables are added to the dataset:

3. _processing_CTD_format.py_: Reorganizes dataset in a csv user-friendly format.

### UWS discrete samples
Final dataset can be found in _'./data'_ as **SO279_UWS_data.csv**. Dataset includes the sames variables as the CTD discrete samples dataset.

* _processing_uws_raw.py_: Retrieves raw continuous pH(optode) data from all underway Pyroscience optode pH files. Adds corresponding biogeochemical data from the SMB salinograph on board. Corrects salinity. Estimates TA(est) for the North Atlantic Ocean from salinity and temperature according to Lee et al. (2006). Calculates pH(TA(est), pH(optode), in-situ temperature, total scale). Creates a dataset including the following variables:
    * _filename_
    * _sec_
    * _pH_cell_
    * _temp_cell_
    * _dphi_
    * _signal_intensity_
    * _ambient_light_
    * _ldev_
    * _status_ph_
    * _status_temp_
    * _WS_airtemp_
    * _WS_baro_
    * _WS_course_
    * _WS_date_
    * _WS_heading_
    * _WS_humidity_
    * _WS_humidity_
    * _WS_lat_
    * _WS_lon_
    * _WS_longwave_
    * _WS_normto_
    * _WS_pyrogeometer_
    * _WS_sensorvalue_
    * _WS_sentence_
    * _WS_shortwave_
    * _WS_speed_
    * _WS_timestamp_
    * _WS_watertemp_
    * _WS_winddirection_rel
    * _WS_winddirection_true_
    * _WS_windspeed_rel_
    * _WS_windspeed_true_
    * _WS_windspeed_true_bft_
    * _chl_
    * _SBE_45_c_
    * _date_
    * _delay_
    * _depth_
    * _ew_
    * _flow_
    * _lat_
    * _lon_
    * _smb_name_
    * _ns_
    * _system_
    * _SBE45_sal_
    * _sentence_
    * _SMB.RSSMB.SMB_SN_
    * _SBE45_sv_
    * _insitu_sv_
    * _smb_status_
    * _smb_sv_aml_
    * _SBE38_water_temp_
    * _SBE45_water_temp_
    * _smb_time_
    * _smb_tur_
    * _temp_diff_
    * _pH_
    * _pchip_salinity_
    * _sal_corr_
    * _ta_est_
    * _pH_insitu_ta_est_

* _processing_uws_subsamples.py_: Retrieves UWS subsample data and adds nutrient data. For each subsample, the closest (in time) salinity (corrected) and temperature is fetched from the continuous pH dataset.

* _processing_vindta.py_: Processes TA and DIC lab analysis. Calculates pH(TA, DIC, 25, free scale), pH(initial during TA titration, 25, free scale) and pH(TA, DIC, in-situ temperature, total scale). The following variables are added to the dataset:
    * _talk_ (Total Alkalinity)
    * _flag_talk_
    * _tco2_ (Dissolved Inorganic Carbon)
    * _flag_tco2_
    * _pH_talk_tco2_25_
    * _pH_init_talk_
    * _pH_talk_tco2_insitu_temp_

* _processing_uws_pH_correction.py_: All duplicate subsamples are averaged (mean). 

## Further processing
* _so279_sal_compilation.py_: compiles salinity mean, min and max for each cruise day.

* _so279_satdat_interp.py_: interpolates satellite data along latitude, longitude and time to match cruise data.

## Graphs
* _so279_gif_X.py_: (X = sal, sla or sst) creates a gif of the evolution of sea level anomaliy, surface salinity or surface temperature throughout the duration of the cruise, in the study area.

* _so279_plot_init.py_: creates a graph for:
    * Temperature from the optode sensor and in-situ temperature from the ships' SMB salinograph vs. time
    * In-situ temperature (SMB) and in-situ salinity (SMB) vs. time
    * In-situ pH (recalc) and in-situ temperature (SMB) vs. time

* _so279_track_phinsitu.py_: creates a map showing the ship's track with pH evolution.

* _so279_track_ship.py_: creates a map showing the ship's track with time indication.

* _so279_transect.py_: creates figure plotting transect on map, with four subsequent graphs of 1. in-situ pH, 2. surface salinity (SMB), 3. surface temperature (SMB) and 4. sea level anomaly (interpolated from CMEMS data) vs. time.
