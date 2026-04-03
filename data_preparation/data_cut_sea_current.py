import pandas as pd
import numpy as np
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'gcoos_2010_12_sea_water_current.csv')  
data = pd.read_csv(file_path, sep=',')

data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
data['sea_water_speed'] = pd.to_numeric(data['sea_water_speed'], errors='coerce')
data['direction_of_sea_water_velocity'] = pd.to_numeric(data['direction_of_sea_water_velocity'], errors='coerce')

data = data.dropna(subset=['latitude', 'longitude', 'sea_water_speed', 'direction_of_sea_water_velocity'])

data = data[(data["direction_of_sea_water_velocity"] >= 0) & (data["direction_of_sea_water_velocity"] <= 360)]

data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%dT%H:%M:%SZ").dt.date

data = data[['latitude', 'longitude', 'date', 'sea_water_speed', 'direction_of_sea_water_velocity']].copy()

latitude_min, latitude_max = 21, 31
longitude_min, longitude_max = -99, -81

data = data[
    (data['latitude'] >= latitude_min) & 
    (data['latitude'] <= latitude_max) & 
    (data['longitude'] >= longitude_min) & 
    (data['longitude'] <= longitude_max)
]

data["current_x"] =  np.cos(np.radians(data["direction_of_sea_water_velocity"])).round(5)
data["current_y"] =  np.sin(np.radians(data["direction_of_sea_water_velocity"])).round(5)

data.loc[abs(data["current_x"]) < 1e-3, "current_x"] = 0
data.loc[abs(data["current_y"]) < 1e-3, "current_y"] = 0

data.drop(columns=["direction_of_sea_water_velocity"], inplace=True)

data['id'] = data.groupby(['latitude', 'longitude']).ngroup()

latitude_step = 1
longitude_step = 1

selected_points = []
for lat_start in np.arange(latitude_min, latitude_max, latitude_step):
    for lon_start in np.arange(longitude_min, longitude_max, longitude_step):
        lat_end = lat_start + latitude_step
        lon_end = lon_start + longitude_step

        subset = data[
            (data['latitude'] >= lat_start) & (data['latitude'] < lat_end) &
            (data['longitude'] >= lon_start) & (data['longitude'] < lon_end)
        ]
        
        if not subset.empty:
            selected_points.append(subset.iloc[0])

selected_points_df = pd.DataFrame(selected_points)

# 30 dni 
final_data = pd.DataFrame()
for _, point in selected_points_df.iterrows():
    point_data = data[
        (data['latitude'] == point['latitude']) &
        (data['longitude'] == point['longitude'])
    ].drop_duplicates(subset='date').sort_values(by='date').head(30)
    final_data = pd.concat([final_data, point_data])


output_file = "filtered_sea_current_data.csv"
final_data.to_csv(output_file, index=False)

