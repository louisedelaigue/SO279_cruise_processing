import PyCO2SYS as pyco2

def alkalinity(data):
    df = data.copy()
    # estimate TA for the North Atlantic Ocean from S and T according to Lee et al. (2006)
    def ta_nao(sss, sst):
        """Estimate TA in the North Atlantic Ocean."""
        return (
            2305 
            + (53.97 * (sss - 35)) 
            + (2.74 * ((sss - 35)**2)) 
            - (1.16 * (sst - 20)) 
            - (0.040 * ((sst - 20)**2)) 
            )
    
    # create new column with results in dataset
    df['ta_est'] = ta_nao(df.salinity, df.SBE38_water_temp)
    
    # recalculate pH at in-situ temperature (SBE38) using estimated TA
    carb_dict = pyco2.sys(df.ta_est, df.pH_cell, 1, 3, 
                          salinity=df.salinity,
                          temperature=df.temp_cell,
                          temperature_out=df.SBE38_water_temp,
                          pressure=0,
                          pressure_out=3,
                          opt_pH_scale=1,
                          opt_k_carbonic=16,
                          opt_total_borate=1
                          )
    
    # save in-situ pH to df
    df['pH_insitu_ta_est'] = carb_dict['pH_total_out']
    
    return df
