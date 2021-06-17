def temp_restriction(df):
    """Constrain temperature difference between in-situ and 
    pH cell < 1"""
    df['temp_diff'] = abs(df.temp_cell - df.SBE38_water_temp)
    df = df[df['temp_diff'] < 1.0]
    return df