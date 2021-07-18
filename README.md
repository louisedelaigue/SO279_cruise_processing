[![DOI](https://zenodo.org/badge/377739875.svg)](https://zenodo.org/badge/latestdoi/377739875)

# Data processing for SO279 cruise

<img src=Capture.JPG width="500" height="500"/>

## Data
Data used in this repo come from the SO279 cruise across the North Atlantic in the Azores Region (December 2020). Discrete samples were taken from the CTD (77 measurements, _SO279_CTD_discrete_samples.csv_) and the underway water system (UWS; 51 measurements, _SO279_UWS_discrete_samples.csv_). A high-resolution (1 measurement every 30 seconds) time series of surface ocean pH cross-calibrated using UWS discrete samples is also available (_SO279_UWS_time_series.csv_). All raw data is also accessible in this repo apart from the ship's thermo-salinograph data as the file exceeded GitHub maximum file size (can be shared upon request).

CTD and UWS discrete samples dataset contain respectively 77 measurements (all from the CTD rosette) and 51 measurements (all from the UWS) of seawater dissolved inorganic carbon (DIC) , total alkalinity (TA) and nutrients (Si, PO4, NH4, NO3 and NO2). The UWS time series dataset contains a high-resolution (1 measurement every 30 seconds) time series of surface ocean pH measured with a PyroScience fiber-based pH sensor (PHROBSC-PK8T) and cross-calibrated using discrete carbonate system observations (total alkalinity, dissolved inorganic carbon and nutrients). Samples were collected during R/V Sonne cruise SO279 in Dec 2020 in the Azores Region of the North Atlantic Ocean, as part of the NAPTRAM research programme to build an understanding of the transport pathways of plastic and microplastic debris in the North Atlantic. Measurements were carried out using VINDTA 3C instruments (#017, Marianda, Germany) at the NIOZ Royal Netherlands Institute for Sea Research. Bad results resulting from technical issues during analysis have been removed from these results, so there are no recognised issues. The data were collected as part of an international effort from the JPI Oceans project HOTMIC and BMBF project PLASTISEA , and forms a joint effort of HOTMIC and PLASTISEA researchers from a range of countries and institutes. The NIOZ created the metadata entry and is responsible for holding master copies of the data.

## Cruise report
The short cruise report can be found in the main folder of this repo as _SO279_GPF_20-3_089_SCR.pdf_.

## Data processing
All data processing presented in this repo was done by Louise Delaigue and Matthew Humphreys from the NIOZ Royal Netherlands Institute for Sea Research.

Scripts below are used in the processing of CTD and UWS data. Each script's function is briefly highlighted and variables are listed.

All calculations pertainting to the carbonate system were done using the Python toolbox [PyCO2SYS](https://pyco2sys.readthedocs.io/en/latest/) and default carbonic acid dissociation constants (Sulpis et al., 2020). VINDTA lab analysis was processed using the packages [Calkulate](https://calkulate.readthedocs.io/en/latest/) and [koolstof](https://github.com/mvdh7/koolstof).

All column header abbreviations and variable flags follow _Best Practice Data Standards for Discrete Chemical Oceanographic Observations_ (Jiang et al, in prep).

### Scripts order (quick processing)
Further below is a description of all scripts pertaining to the above mentioned datasets. All CTD discrete samples can be ran independently from UWS-related scripts. However for efficiency, it is advised to run all scripts in the following order:
1. _processing_uws_raw.py_
2. _processing_subsamples_raw.py_
3. _processing_ctd_raw.py_
4. _processing_vindta.py_
5. _processing_subsamples_format.py_
6. _processing_ctd_format.py_
7. _processing_uws_pH_correction.py_
8. _processing_uws_format.py_

### CTD discrete samples
Final dataset can be found in _'./data'_ as **SO279_CTD_discrete_samples.csv**. Dataset includes the following variables:
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

2. _processing_vindta.py_: Processes TA and DIC lab analysis for both CTD and UWS discrete samples. Calculates pH(TA, DIC, 25, free scale), pH(initial during TA titration, 25, free scale) and pH(TA, DIC, in-situ temperature, total scale).

3. _processing_CTD_format.py_: Reorganizes dataset in a csv user-friendly format.

### UWS discrete samples
Final dataset can be found in _'./data'_ as **SO279_UWS_discrete_samples.csv**. Dataset includes the sames variables as the CTD discrete samples dataset.

Processing steps include the following scripts and order:
1. _processing_subsamples_raw.py_: Retrieves UWS discrete samples data and adds nutrients. The closest (in time) correcyed salinity and in-situ temperature is added to each sample from the UWS continuous pH dataset.

2. _processing_vindta.py_: Processes TA and DIC lab analysis for both CTD and UWS discrete samples. Calculates pH(TA, DIC, 25, free scale), pH(initial during TA titration, 25, free scale) and pH(TA, DIC, in-situ temperature, total scale).

3. _processing_subsamples_format.py_: Reorganizes dataset in a csv user-friendly format.

### UWS pH time series
Final dataset can be found in _'./data'_ as **SO279_UWS_time_series.csv**. Dataset includes the following variables:
* EXPOCODE
* Cruise_ID
* Year_UTC
* Month_UTC
* Day_UTC
* Time_UTC
* Latitude
* Longitude
* Depth
* Temperature
* TEMP_pH
* Salinity
* Salinity_flag
* pH_TS_measured (optode)
* pH_flag

Processing steps include the following scripts and order:
1. _processing_uws_raw.py_: Retrieves raw continuous pH(optode) data from all underway Pyroscience optode pH files. Adds corresponding biogeochemical data from the SMB thermo-salinograph on board. Corrects salinity. Estimates TA(est) for the North Atlantic Ocean from salinity and in-situ temperature according to Lee et al. (2006). Calculates pH(TA(est), pH(optode), in-situ temperature, total scale).

2. _processing_uws_pH_correction.py_: Cross-calibrates measured pH(total scale) using processed UWS discrete samples.

3. _processing_UWS_format.py_: Reorganizes dataset in a csv user-friendly format.

### Other processing
Flagging for nutrients was done according to a precision number. For nutrient variable and pair of duplicates, the difference between duplicates was divided by the mean value of the duplicate pair (giving diff/mean). For each nutrient variable, the precision number was given by the mean of all _(diff_mean)_. Then, each duplicate was compared against the precision number: a flag = 3 was given to all duplicates greater than the precision number and a flag = 2 was given to all duplicates less than the precision number.

:warning: Precision numbers were computed from the UWS discrete samples, as the reproducibility was much more superior than the CTD discrete samples.

Scripts for the computation of precision numbers can be found as _processing_X_precision_number.py_.
