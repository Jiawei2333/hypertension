import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.parser import parse
import os

# bp: blood pressure as a DataFrame with the 1st column as systolic bp and 2nd column as diastolic bp
# by = 'each' checks every instance of bp
# by = 'mean' calculates and checks the mean of bp
def is_high_reading(bp, systolic_threshold = 180, diastolic_threshold = 110, by = 'each'):
    if by == 'each':
        is_systolic_high = bp['systolic_bp'] > systolic_threshold
        is_diastolic_high = bp['diastolic_bp'] > diastolic_threshold
    if by == 'mean':
        mean = bp.mean()
        is_systolic_high = mean['systolic_bp'] > systolic_threshold
        is_diastolic_high = mean['diastolic_bp'] > diastolic_threshold
    return is_systolic_high or is_diastolic_high
	
# Hypertensive emergency alert
def hyperten_emergency(df, alerts = [0, 0, 0]):
    idx = len(df)-1 # initialize index pointing to the last bp instance
    if is_high_reading(df.iloc[idx]):
        # if the current instance is high reading, check the previous 2 readings
        if idx > 1 and is_high_reading(df.iloc[idx -1]) and is_high_reading(df.iloc[idx -2]):
            timegap = df.iloc[idx]['TimeStamp'] - df.iloc[idx - 2]['TimeStamp']
            # if previous 2 readings are high and within 1 hour, raise hyperten emergency alert
            if timegap < timedelta(hours = 1):
                alerts[0] = 1
        # if no hyperten emergency alert is raised, check if there is no follow up after high reading
        elif datetime.now() - df.iloc[idx]['TimeStamp'] > timedelta(hours = 1):
            alerts[2] = 1
    # if the current instance is low reading,
    # check the previous readings to see if there is 'miss reading' for no follow up
    else:
        while idx > 0:
            next_time = df.iloc[idx]['TimeStamp']
            idx -= 1
            if is_high_reading(df.iloc[idx]):
                timegap = next_time - df.iloc[idx]['TimeStamp']
                if timegap > timedelta(hours = 1):
                    alerts[2] = 1
    return alerts

		
# Missed reading alert
# Any time there is a gap of 7 days in readings of last month
def gap_7days(df):
    for i in range(len(df)-1): # Iterate over all the instances except the last one
        row, next_row = df.iloc[i], df.iloc[i+1]
        gap_7 = next_row['TimeStamp'] - row['TimeStamp']
        # Any time there is a gap of 7 days in readings of last month,
        # raise missed reading alert, and break the for loop
        if gap_7 > timedelta(days = 7):
            return 'miss reading'
	

	
# Main function
def hypertension_alerts(df, ID):
    '''
    A function that takes in an id and DataFrame file, and returns the following:

    (1)- hypertensive emergency if 3 consecutive readings within a hour are more than 180/110 (any one reading higher)
        a - this alert is nullified if any reading afterwards is lower.

    (2) - monthly high if last month average is more than 140/90

    (3) - missed reading if 
        a. Any time there is a gap of 7 days in readings of last month. 
        b. No follow-up within an hour after 180/110
    '''
    # alerts[0]: hypertensive emergency
    # alerts[1]: monthly high
    # alerts[2]: missed reading
    alerts = [0, 0, 0] # Inicialize alerts. 0 stands for no alert while 1 stands for alert
    
    df_ID = df[df['ID'] == ID] # Pick up the df for patient with given ID
    # Choose the data from last month
    mask = df_ID['TimeStamp'] > datetime.now() - timedelta(days = 30)
    df_last_mo = df_ID[mask]
    # Check if monthly high
    is_monthly_high = is_high_reading(df_last_mo[['systolic_bp', 'diastolic_bp']],
                                      systolic_threshold = 140,
                                      diastolic_threshold = 90,
                                      by = 'mean')
    if is_monthly_high:
        alerts[1] = 1

    # Check hypertensive emergency or miss reading
    alerts = hyperten_emergency(df_ID, alerts)

    if gap_7days(df_last_mo) == 'miss reading':
        alerts[2] = 1
    
    return alerts
	
	
	
# Load data
path = 'D:\\git\\hypertension'

df = pd.read_csv(os.path.join(path, 'blood_pressure.csv'))
# Parse time string to timestamp
df['TimeStamp'] = df['TimeStamp'].map(lambda x: parse(x, dayfirst = True))

split_values = df['BloodPressure'].str.split('/', expand = True) # Split high and low pressure
df[['systolic_bp', 'diastolic_bp']] = split_values.astype(int) # Attach these two columns to df



# Call main function and return alerts
alerts = hypertension_alerts(df, 1)
print(alerts)