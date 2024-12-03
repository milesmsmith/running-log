#!/usr/bin/env python
# coding: utf-8

# In[189]:


from garminconnect import Garmin
import datetime
import os
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import interp1d
import garth


# In[89]:

email = "Garmin Connect Username"
password = "Garmin Connect Password"
lab_vo2 = 72.5

email = os.getenv("GARMIN_EMAIL")
password = os.getenv("GARMIN_PASSWORD")


garth.http.USER_AGENT = {"User-Agent": ("GCM-iOS-5.7.2.1")} # Patch bug in garminconnect code

garmin_api = Garmin(email=email, password=password)
garmin_api.login()


# In[150]:


activities = garmin_api.get_activities(0, 10000)

df = pd.DataFrame(columns=['Date', 'Start Time', 'Distance', 'Duration', 'Pace', 'Elevation Gain', 'Heart Rate', 'VO2 Max', 'Cadence', 'Activity Load'])

for i in range(len(activities)):
    # print(activities[i])
    activityType = activities[i]['activityType']['typeKey']
    if activityType == 'running':
        try:
            distance = activities[i]['distance']/1609 # [units: miles]
        except:
            pass
            
        try:
            vO2Max = activities[i]['vO2MaxValue'] # [units: mL/kg-min]
        except:
            vO2Max = None

        try:
            duration = activities[i]['movingDuration']/60 # [units: minutes]
        except:
            duration = activities[i]['duration']/60 # [units: minutes]

        try:
            avgHR = activities[i]['averageHR'] # [units: bpm]
        except:
            avgHR = None

        startTime = activities[i]['startTimeLocal'] # [units: bpm]

        try:
            cadence = activities[i]['averageRunningCadenceInStepsPerMinute'] # [units: bpm]
        except:
            cadence = None

        try:
            elevationGain = activities[i]['elevationGain'] # [units: bpm]
        except:
            elevationGain = None

        # splitSummaries = activities[i]['splitSummaries']
        try:
            activityLoad = activities[i]['activityTrainingLoad']
        except:
            activityLoad = None

        avgPace = duration/distance
        date = datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S").date()
        time = datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S").time()

        new_row = {
            'Date': date,
            'Start Time': time,
            'Distance': distance,
            'Duration': duration,
            'Pace': avgPace,
            'Elevation Gain': elevationGain,
            'Heart Rate': avgHR,
            'VO2 Max': vO2Max,
            'Cadence': cadence,
            'Activity Load': activityLoad
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

# In[151]:


df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S')
dates = df['Date'].to_numpy()
distance = df['Distance'].to_numpy()
VO2_Max = df['VO2 Max'].to_numpy()
dates = [pd.to_datetime(d) for d in dates]
df = df.set_index('Date')
weekly_distance = df['Distance'].resample('W-SAT').sum()
weekly_start = weekly_distance.index - pd.Timedelta(days=6)

# In[208]:


vo2df = pd.read_excel('VDOTtoIAAF.xlsx')
vdot = vo2df['VDOT']
iaaf = vo2df['IAAF Points (2017 Mens)']

vdot2iaaf = interp1d(vdot,iaaf, kind='quadratic')

iaaf_garmin = vdot2iaaf(VO2_Max)


# In[219]:


racesdf = pd.read_excel('RACEtoIAAF.xlsx')
race_dates = racesdf['Date'].to_numpy()
race_dates = [pd.to_datetime(d) for d in race_dates]
race_score = racesdf['IAAF Points']


# In[230]:


plt.rcParams['font.family'] = 'Arial'  # Set the font to Arial
plt.rcParams['font.size'] = 10  # Set the font size to 12

start_date = pd.to_datetime('2018-1-1', format='%Y-%m-%d')
end_date = pd.to_datetime('2025-1-1', format='%Y-%m-%d')

vo2_fig, vo2_ax = plt.subplots(figsize=(6, 3), dpi=300)
vo2_ax2 = vo2_ax.twinx()
# vo2_ax.grid()
vo2_ax.plot(dates, VO2_Max, color='#CA3031',zorder=3, linewidth=1, label='Garmin Estimated VO2 Max')
vo2_ax2.plot(dates, iaaf_garmin, color='#0F9ED5',zorder=3, linewidth=0.5, label='Garmin Estimated IAAF Score')
vo2_ax2.scatter(race_dates, race_score, color='#0F9ED5',zorder=3, s=3, label='Race Results')
# vo2_ax.hlines(y=[lab_vo2], xmin=start_date, xmax=end_date, zorder=2, colors='#CA3031', linestyles='dotted', label='Lab Measured VO2 Max (2022)')
# vo2_ax2.hlines(y=[vdot2iaaf(lab_vo2)], xmin=start_date, xmax=end_date, zorder=2, colors='#0F9ED5', linestyles='dotted', label='Lab Measured VO2 Max (2022)')
vo2_ax.set_ylabel('Watch VO2 Max Estimation (mL/(kg-min))', color='#CA3031')
vo2_ax2.set_ylabel('IAAF Points (2017 Mens)', color='#0F9ED5')
vo2_ax.set_xlabel('Time (Years)')
vo2_ax.set_title('Relationship Between Estimated VO2 Max and Track Race Performance')
vo2_ax.tick_params(axis="x",direction="in", pad=5)
vo2_ax.set_xlim([start_date, end_date])
vo2_ax.set_xlim([start_date, end_date])
# vo2_fig.legend(bbox_to_anchor=(1.35, 0.75))
plt.tight_layout()
plt.show()
