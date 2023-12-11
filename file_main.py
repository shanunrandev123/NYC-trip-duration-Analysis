
#%%
import os
import sys
# Getting the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Adding the parent directory to the Python path
sys.path.append(os.path.dirname(current_dir))

# from Outliers_detection import find_limits, clip_variables

# from Outliers_detection import mapping_outliers
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
import folium
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PowerTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
# from catboost import CatBoostRegressor

from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_squared_log_error

# import xgboost as xgb



# Get the current working directory
current_directory = os.getcwd()

# Reading the CSV file
df = pd.read_csv(os.path.join(current_directory, "train.csv"))

print(df.head(5))

print(df.info())


#%%

#calculates the lower and upper limits for each specified variable in a dataset based on the interquartile range (IQR) and a given fold value.
#The purpose of finding these limits is often related to identifying and handling outliers in the data.

def find_limits(data, variables, fold):
    limits = dict()
    for variable in variables:
        IQR = data[variable].quantile(0.75) - data[variable].quantile(0.25)
        lower_limit = data[variable].quantile(0.25) - (IQR * fold)
        upper_limit = data[variable].quantile(0.75) + (IQR * fold)
        limits[variable] = (lower_limit, upper_limit)
    return limits


#%%

#The purpose of this function is to enforce constraints on the values of specific variables, ensuring that they fall within a predefined range.
#This is often done to mitigate the impact of outliers or extreme values on statistical analyses, modeling, or visualization.
# It provides a way to handle values that are deemed too extreme without removing them entirely from the dataset.

def clip_variables(data, limits):
    clipped_data = data.copy()
    for variable, (lower_limit, upper_limit) in limits.items():
        clipped_data[variable] = clipped_data[variable].clip(lower=lower_limit, upper=upper_limit)
    return clipped_data
#%%


#Haversine distance is a formula used to calculate the distance between two points on the surface of a sphere,
#given their latitude and longitude in decimal degrees.
#This formula is often employed to calculate the distance between two locations on earth 
#where the earth is approximately spherical

def haversine_distance(df, lat1, lat2, long1, long2):
    
    r = 6371 #average radius of earth in kilometers
    
    phi1 = np.radians(df[lat1])
    
    phi2 = np.radians(df[lat2])
    
    delta_phi = np.radians(df[lat2] - df[lat1])
    
    delta_lambda = np.radians(df[long2] - df[long1])
    
    a = np.sin(delta_phi/2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    d = r * c
    
    return d

#%%

#calculates the compass bearing (direction) between two geographic points specified by their latitude and longitude coordinates.
#The bearing is the angle measured in degrees from the north direction (0 degrees) in a clockwise direction
#The Haversine formula is often used for navigation and geographical applications to determine the direction from one point to another.
#The resulting bearing is typically expressed as a value between 0 and 360 degrees where 0 degrees is north,
#90 degrees is east, 180 degrees is south, and 270 degrees is west


def bearing_array(df,lat1, long1, lat2, long2):
    AVG_EARTH_RADIUS = 6371  # in km
    long_delta_rad = np.radians(long2 - long1)
    lat1, long1, lat2, long2 = map(np.radians, (lat1, long1, lat2, long2))
    y = np.sin(long_delta_rad) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(long_delta_rad)
    return np.degrees(np.arctan2(y, x))


#%%


df.loc[:, 'trip_distance(km)'] = haversine_distance(df, 'pickup_latitude', 'dropoff_latitude', 'pickup_longitude','dropoff_longitude')

df.loc[:, 'center_latitude'] = (df['pickup_latitude'].values + df['dropoff_latitude'].values) / 2
df.loc[:, 'center_longitude'] = (df['pickup_longitude'].values + df['dropoff_longitude'].values) / 2

df.loc[:, 'direction'] = bearing_array(df,df['pickup_latitude'].values, df['pickup_longitude'].values,df['dropoff_latitude'].values, df['dropoff_longitude'].values)


#%%
# Check for Null Values
print(df.isnull().sum()) 
# No Null Values

# Check for Duplicates
print('Number of duplicates, trip ids: {}'.format(len(df) - len(df.drop_duplicates())))  
# No duplicates


#%%

# Displaying the minimum and maximum values for latitude and longitude
print('Pickup Latitude - Min: {}, Max: {}'.format(df.pickup_latitude.min(), df.pickup_latitude.max()))
print('Dropoff Latitude - Min: {}, Max: {}'.format(df.dropoff_latitude.min(), df.dropoff_latitude.max()))
print('Pickup Longitude - Min: {}, Max: {}'.format(df.pickup_longitude.min(), df.pickup_longitude.max()))
print('Dropoff Longitude - Min: {}, Max: {}'.format(df.dropoff_longitude.min(), df.dropoff_longitude.max()))

# Displaying the range of trip duration in seconds
print('Trip duration in seconds: {} to {}'.format(df.trip_duration.min(), df.trip_duration.max()))



#%%

# Number of unique vendors
print('Vendors count: {}'.format(len(df.vendor_id.unique())))  # Only 2 unique vendors

# Range of passenger counts
print('Passengers: {} to {}'.format(df.passenger_count.min(), df.passenger_count.max()))


#%%

print('Empty trips: {}'.format(df[df.passenger_count == 0].shape[0]))

# Remove these rides which have 0 passenger (60 Trips)
df = df[df['passenger_count'] > 0]

# Taxi can accomodate only 6 members at max 
# Removing other passenger counts (7,8,9)
print('Trips with Passanger count - 7 : {}'.format(df[df.passenger_count == 9].shape[0])) # 

print('Trips with Passanger count - 8 : {}'.format(df[df.passenger_count == 8].shape[0]))

print('Trips with Passanger count - 9 : {}'.format(df[df.passenger_count == 7].shape[0]))

df = df[df['passenger_count'] < 7]

#%%

df['pickup_datetime'] = pd.to_datetime(df.pickup_datetime)
df['dropoff_datetime'] = pd.to_datetime(df.dropoff_datetime)

df['month'] = df.pickup_datetime.dt.month
df['week'] = df['pickup_datetime'].dt.isocalendar().week
df['weekday'] = df.pickup_datetime.dt.weekday
df['hour'] = df.pickup_datetime.dt.hour
df['minute'] = df.pickup_datetime.dt.minute
df['minute_oftheday'] = df['hour'] * 60 + df['minute']
df.drop(['minute'], axis=1, inplace=True)


df['check_trip_duration'] = (df['dropoff_datetime'] - df['pickup_datetime']).map(lambda x : x.total_seconds())

duration_difference = df[np.abs(df['check_trip_duration'].values  - df['trip_duration'].values) > 1]

print(f"Trip Duration with 0 mins: {duration_difference}")

# Removing the rows with trip duration : 0 mins
print(df[df['trip_duration'] == 0]) # 0 Rows
df[df['trip_duration'] != 0]

# Removing the rows with more than 100 hours of trip  duration 
df[df['trip_duration'] < 360000] # 4 rows

df.rename(columns={'trip_duration': 'trip_duration(sec)'}, inplace=True)

#%%

df = df.drop('check_trip_duration', axis=1)


#%%

# Removing rows with trip distance less than 1 metre

num_rows_distance_less_than_1_metre = len(df[df['trip_distance(km)'] <= 0.001])
print(f'Number of rows with trip distance less than 1 metre : {num_rows_distance_less_than_1_metre}')
 
df = df[df['trip_distance(km)'] > 0.001]

#%%
# Plotting Pickup cordinates which are outside of New-York (pickup)
# outlier_locations_pickup_1 = df[((df.pickup_longitude <= -74.15) | (df.pickup_latitude <= 40.5774)| \
#                 (df.pickup_longitude >= -73.7004) | (df.pickup_latitude >= 40.9176))]

# print(outlier_locations_pickup_1)
# # outlier_locations_pickup_1
# map_osm_pickup = folium.Map(location=[40.734695, -73.990372], zoom_start=3, tiles="cartodb positron")


#%%

pickup_locations = df[['pickup_longitude', 'pickup_latitude']]

# Define the number of clusters (adjust as needed)
k_values = range(1, 15)
inertias = []

for k in k_values:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(pickup_locations)
    inertias.append(kmeans.inertia_)

# Plot the elbow curve
plt.plot(k_values, inertias, marker='o')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Inertia')
plt.title('Elbow Method for Optimal k')
plt.show()


#%%

num_clusters = 10

# Fit K-means clustering model
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
df['pickup_cluster'] = kmeans.fit_predict(pickup_locations)

plt.figure(figsize=(10, 6))
sns.scatterplot(x='pickup_longitude', y='pickup_latitude', hue='pickup_cluster', data=df, palette='viridis')
plt.title('K-means Clustering of Pickup Locations')
plt.xlabel('Pickup Longitude')
plt.ylabel('Pickup Latitude')
plt.legend(title='Cluster')
plt.show()

#%%

from geopy.geocoders import Nominatim


# Initialize a geocoder
geolocator = Nominatim(user_agent="shanun")




def get_address(latitude, longitude):
    location = geolocator.reverse((latitude, longitude), language='en')
    return location.address if location else "Address not found"

#selecting top 4 clusters
top_clusters = df['pickup_cluster'].value_counts().nlargest(4).index

print(top_clusters)

top_clusters = top_clusters.tolist()



# Filter the DataFrame to include only the rows with the top clusters
top_clusters_df = df[df['pickup_cluster'].isin(top_clusters)]


#%%
top_clusters_df['pickup_cluster'].value_counts()

#%%

#getting most common pickup per cluster

import folium
from folium.plugins import MarkerCluster


mean_latitude = top_clusters_df['pickup_latitude'].mean()
mean_longitude = top_clusters_df['pickup_longitude'].mean()
mymap = folium.Map(location=[mean_latitude, mean_longitude], zoom_start=12)



marker_clusters = []

# Add markers for each location in the top clusters with cluster names
for cluster in top_clusters:
    cluster_data = top_clusters_df[top_clusters_df['pickup_cluster'] == cluster]
    
    sampled_locations = cluster_data.sample(n=10, random_state=42)

    
    # Create a MarkerCluster with the cluster number as the name
    marker_cluster = MarkerCluster(name=str(cluster), overlay=True)
    
    # Add markers to the MarkerCluster
    for _, location in sampled_locations.iterrows():
        address = get_address(location['pickup_latitude'], location['pickup_longitude'])
        folium.Marker([location['pickup_latitude'], location['pickup_longitude']],
                      popup=f"Cluster: {cluster}<br>Address: {address}",
                      icon=None).add_to(marker_cluster)
    
    # Add the MarkerCluster to the list
    marker_clusters.append(marker_cluster)
    
    
for marker_cluster in marker_clusters:
    marker_cluster.add_to(mymap)

# Add a LayerControl to the map
folium.LayerControl().add_to(mymap)

mymap

#%%

#categorical encoding of the Store_and_fwd_flag and the vendor_id


df = pd.concat([df, pd.get_dummies(df['store_and_fwd_flag'],dtype=int)], axis=1)
df.drop(['store_and_fwd_flag'], axis=1, inplace=True)
df = pd.concat([df, pd.get_dummies(df['vendor_id'],dtype=int)], axis=1)
df.drop(['vendor_id'], axis=1, inplace=True)


column_mapping = {1: '1', 2: '2'}

# Use the rename method to rename columns
df = df.rename(columns=column_mapping)

#%%


cols_to_exclude = ['pickup_datetime', 'dropoff_datetime', 'N', 'Y', '1', '2', 'id']
cols_to_transform = df.drop(cols_to_exclude, axis = 1).columns

# print(df[cols_to_transform].columns)

transformer = PowerTransformer(method='yeo-johnson', standardize=False)
transformer.set_output(transform='pandas')

df[cols_to_transform] = transformer.fit_transform(df[cols_to_transform])


#%%

df.loc[:, 'avg_speed_h'] = 1000 * df['trip_distance(km)'] / df['trip_duration(sec)']

#%%
Outlier_detection_IQR = True # IQR = 1.5

if Outlier_detection_IQR:
    variable_list = ['trip_duration(sec)','pickup_latitude','pickup_longitude','dropoff_latitude','dropoff_longitude','trip_distance(km)', 'avg_speed_h', 'direction']
    fold_value = 1.5
    result = find_limits(df, variable_list, fold_value)

    df = clip_variables(df, result)
    print("Cleaned Data")


#%%



#%%
#Using yeo-johnson which is basically box cox transformation(we are using yeo -johnson because it can handle not only positive values but also negative values and zeros)



# print(df[cols_to_transform].columns)

#%%
#computing the avg speed

#%%


    
#%%

# Visulazing distribution of Trip Duration(Sec) 
sns.kdeplot(df['trip_duration(sec)'], fill=True)
plt.title('Density Plot of Trip Duration')
plt.xlabel('Trip Duration')
plt.ylabel('Density')
plt.show()
plt.figure(figsize=(10, 6))

#%%
# Visulazing distribution of Trip Distance(km) 

sns.kdeplot(df['trip_distance(km)'], fill=True)
plt.title('Density Plot of Trip Distance')
plt.xlabel('Trip Distance')
plt.ylabel('Density')
plt.show()

#%%

y = df["trip_duration(sec)"]
df.drop(["trip_duration(sec)"], axis=1, inplace=True)
df.drop(['id', 'pickup_datetime', 'dropoff_datetime', 'pickup_cluster'], axis=1, inplace=True)
X = df

#%%


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

X_train.shape, y_train.shape, X_test.shape, y_test.shape


#%%
lr = LinearRegression()

lr.fit(X_train, y_train)

y_pred_lr = lr.predict(X_test)



rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
print("Root Mean Squared Error on Test Set (linear regression):", rmse_lr)

# %%
