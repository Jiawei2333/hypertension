import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.parser import parse
import os

# Define a "hypertensive index" which classify blood pressure as 1 if pressure > 180/110, else 0
def hyperten_index(df):
    hyperten_label = [1 if value1 >= hyperten_threshold_high or value2 >= hyperten_threshold_low else 0
                    for value1, value2 in zip(df['Pressure_high'], df['Pressure_low'])]
    str_hyperten = ''.join(str(entry) for entry in hyperten_label)
    return hyperten_label, str_hyperten
	
# Hypertensive emergency alert
def hyperten_emergency(df, str_hyperten):
    hyperten_idx = 0  # hyperten_idx is the index of '111' in str_hyperten
    df_pointer = 0    # df_pointer "memorize" the real index in the original df
    while len(str_hyperten) > 0:
        hyperten_idx = str_hyperten.find('111') # Find if 3 consecutive readings are > 180/110
        if hyperten_idx == -1: # No hypertensive emergency, break the while loop
            break
        else:
            df_pointer += hyperten_idx   # Find '111', move df_pointer to the hyperten_idx position
            # Check whether the consecutive 3 readings are within 1 hour
            time_start, time_end = df.iloc[df_pointer]['TimeStamp'], df.iloc[df_pointer + 2]['TimeStamp']
            time_delta = time_end - time_start
            # If the consecutive 3 readings are within 1 hour, check the remaining readings
            # If any of the reading is 0, alert[0] should be kept as 0
            # if all following readings are 1, raise hypertensive emergency alert
            if time_delta < timedelta(hours = 1) and str_hyperten[hyperten_idx:].find('0') == -1:
                # Raised hypertensive emergency alert
                return True
            # hypertensive emergency alert is nullified, check the rest of the str_hyperten
            str_hyperten = str_hyperten[hyperten_idx + 1:]
            df_pointer += 1
    
    return False # No hypertensive emergency
	
# Monthly high alert
def monthly_high(df):
    df_pressure = df[['Pressure_high', 'Pressure_low']]
    mean = df_pressure.mean()
    # Check if last month average is more than 140/90
    if mean['Pressure_high'] >= monthly_threshold_high or mean['Pressure_low'] >= monthly_threshold_low:
        return True
    else:
        return False
		
# Missed reading alert (1)
# Any time there is a gap of 7 days in readings of last month
def gap_7days(df):
    for i in range(len(df)-1): # Iterate over all the instances except the last one
        row, next_row = df.iloc[i], df.iloc[i+1]
        gap_7 = next_row['TimeStamp'] - row['TimeStamp']
        # Any time there is a gap of 7 days in readings of last month,
        # raise missed reading alert, and break the for loop
        if gap_7 > timedelta(days = 7):
            return True
    return False
	
# Missed reading alert (2)
# No follow-up within an hour after 180/110
def no_follow_up(df, hyperten_label):
    for j in range(len(hyperten_label)):
        if hyperten_label[j] == 1: 
            # If a reading is > 180/110 and it is the last reading (no following up)
            # Raise missed reading alert
            if j == len(hyperten_label):
                return True
            else:
                time_hyperten, next_time = df.iloc[j]['TimeStamp'], df.iloc[j + 1]['TimeStamp']
                time_gap = next_time - time_hyperten
                if time_gap > timedelta(hours = 1): # No follow-up within an hour after 180/110, 
                    return True # raise missed reading alert, and break the for loop
    return False
	
# Main function
def raise_alerts(df, ID):
    '''
    A function that takes in an id and DataFrame file, and returns the following:

    (1)- hypertensive emergency if 3 consecutive readings within a hour are more than 180/110 (any one reading higher)
        a - this alert is nullified if any reading afterwards is lower.

    (2) - monthly high if last month average is more than 140/90

    (3) - missed reading if 
        a. Any time there is a gap of 7 days in readings of last month. 
        b. No follow-up within an hour after 180/110
    '''
    df_ID = df[df['ID'] == ID]
    hyperten_label, str_hyperten = hyperten_index(df_ID)
    print(hyperten_label, str_hyperten)
    if hyperten_emergency(df_ID, str_hyperten):
        alerts[0] = 1
    # Filter the df data and get the readings from last month: df_last_mo
    now = datetime.now()
    last_month = now.month - 1
    mask = [True if time.month == last_month else False for time in df_ID['TimeStamp']]
    df_last_mo = df_ID.loc[mask]
    if monthly_high(df_last_mo):
        alerts[1] = 1
    if gap_7days(df_last_mo) or no_follow_up(df_ID, hyperten_label):
        alerts[2] = 1
    return alerts
	
	
	
# Load data
path = 'D:\\git\\hypertension'

df = pd.read_csv(os.path.join(path, 'blood_pressure.csv'))
# Parse time string to timestamp
df['TimeStamp'] = df['TimeStamp'].map(lambda x: parse(x, dayfirst = True))

split_values = df['BloodPressure'].str.split('/', expand = True) # Split high and low pressure
df[['Pressure_high', 'Pressure_low']] = split_values.astype(int) # Attach these two columns to df

# alerts[0]: hypertensive emergency
# alerts[1]: monthly high
# alerts[2]: missed reading
alerts = [0, 0, 0] # Inicialize alerts. 0 stands for no alert while 1 stands for alert

# Define hypertension thresholds
hyperten_threshold_high = 180
hyperten_threshold_low = 110
# Define monthly high thresholds
monthly_threshold_high = 140
monthly_threshold_low = 90

# Call main function and return alerts
alerts = raise_alerts(df, 1)
print(alerts)