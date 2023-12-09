#%%[markdown]

## New York City Taxi Trip Duration

# Team Member (Team 5):
# 1)   Shanun Randev 
# 2)   Anand Raj
# 3)   Mowzli Sre 
# 4)   Bala krishna Reddy

## Dataset Info:

# The independent variables are as follows : 

# 1.	Id - unique identifier for each trip
# 2.	Vendor_id - a code indicating the provider associated with the trip record
# 3.	Pickup_datetime - date and time when the meter was engaged
# 4.	Dropoff_datetime - date and time when the meter was disengaged
# 5.	Passenger_count - number of passengers in the vehicle
# 6.	Pickup_longitude - Longitude where the meter was engaged
# 7.	Pickup_latitude - Latitude where the meter was engaged
# 8.	Dropoff_latitude - latitude where the meter was disengaged
# 9.	Dropoff_longitude - longitude where the meter was disengaged
# 10.	Store_and_fwd_flag- This flag indicates whether the trip record was held in vehicle memory before sending to the vendor because the vehicle did not have a connection to the server - Y = store and forward; N = not a store and forward trip.


#%%
#%%[markdown]

# Importing Libraries

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
from catboost import CatBoostRegressor

from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_squared_log_error


from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_squared_log_error






# Get the current working directory
current_directory = os.getcwd()

# Reading the CSV file
df = pd.read_csv(os.path.join(current_directory, "train.csv"))

print(df.head())

print(df.info())

# %%
#%%[markdown]

## Data Cleaning

#%%[markdown]

# Calculating haversine distance between 2 sets of GPS coordinates in the dataframe

#%%

def find_limits(data, variables, fold):
    limits = dict()
    for variable in variables:
        IQR = data[variable].quantile(0.75) - data[variable].quantile(0.25)
        lower_limit = data[variable].quantile(0.25) - (IQR * fold)
        upper_limit = data[variable].quantile(0.75) + (IQR * fold)
        limits[variable] = (lower_limit, upper_limit)
    return limits

#%%
def clip_variables(data, limits):
    clipped_data = data.copy()
    for variable, (lower_limit, upper_limit) in limits.items():
        clipped_data[variable] = clipped_data[variable].clip(lower=lower_limit, upper=upper_limit)
    return clipped_data


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



def dummy_manhattan_distance(df, lat1, long1, lat2, long2):
    a = haversine_distance(df, lat1, lat1, long1, long2)
    b = haversine_distance(df, lat1, lat2, long1, long1)
    return a + b


def bearing_array(df,lat1, long1, lat2, long2):
    AVG_EARTH_RADIUS = 6371  # in km
    long_delta_rad = np.radians(long2 - long1)
    lat1, long1, lat2, long2 = map(np.radians, (lat1, long1, lat2, long2))
    y = np.sin(long_delta_rad) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(long_delta_rad)
    return np.degrees(np.arctan2(y, x))



df.loc[:, 'trip_distance(km)'] = haversine_distance(df, 'pickup_latitude', 'dropoff_latitude', 'pickup_longitude','dropoff_longitude')

df.loc[:, 'center_latitude'] = (df['pickup_latitude'].values + df['dropoff_latitude'].values) / 2
df.loc[:, 'center_longitude'] = (df['pickup_longitude'].values + df['dropoff_longitude'].values) / 2

df.loc[:, 'distance_manhattan'] = dummy_manhattan_distance(df,'pickup_latitude', 'pickup_longitude', 'dropoff_latitude', 'dropoff_longitude')
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
# Finding empty trips
print('Empty trips: {}'.format(df[df.passenger_count == 0].shape[0]))

# Remove these rides which have 0 passenger (60 Trips)
df = df[df['passenger_count'] > 0]

# %%
# Taxi can accomodate only 6 members at max 
# Removing other passenger counts (7,8,9)
print('Trips with Passanger count - 7 : {}'.format(df[df.passenger_count == 9].shape[0])) # 

print('Trips with Passanger count - 8 : {}'.format(df[df.passenger_count == 8].shape[0]))

print('Trips with Passanger count - 9 : {}'.format(df[df.passenger_count == 7].shape[0]))

df = df[df['passenger_count'] < 7]

# %%
# df.columns

df['pickup_datetime'] = pd.to_datetime(df.pickup_datetime)
df['dropoff_datetime'] = pd.to_datetime(df.dropoff_datetime)

df['month'] = df.pickup_datetime.dt.month
df['week'] = df['pickup_datetime'].dt.isocalendar().week
df['weekday'] = df.pickup_datetime.dt.weekday
df['hour'] = df.pickup_datetime.dt.hour
df['minute'] = df.pickup_datetime.dt.minute
df['minute_oftheday'] = df['hour'] * 60 + df['minute']
df.drop(['minute'], axis=1, inplace=True)

# df.loc[:, 'pickup_date'] = df['pickup_datetime'].dt.date

# df.loc[:, 'dropoff_date'] = df['dropoff_datetime'].dt.date

# Creating a seprate column for trip duration using pickup time and drop off time 
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
# Removing rows with trip distance less than 1 metre

num_rows_distance_less_than_1_metre = len(df[df['trip_distance(km)'] <= 0.001])
print(f'Number of rows with trip distance less than 1 metre : {num_rows_distance_less_than_1_metre}')
 
df = df[df['trip_distance(km)'] > 0.001]

#%%
# Visulazing distribution of Trip Duration(Sec) 
sns.kdeplot(df['trip_duration(sec)'], fill=True)
plt.title('Density Plot of Trip Duration')
plt.xlabel('Trip Duration')
plt.ylabel('Density')
plt.show()

#%%[markdown]
## Outlier Detection 

#%%
# Plotting Pickup cordinates which are outside of New-York (pickup)
outlier_locations_pickup = df[((df.pickup_longitude <= -74.15) | (df.pickup_latitude <= 40.5774)| \
                (df.pickup_longitude >= -73.7004) | (df.pickup_latitude >= 40.9176))]

map_osm_pickup = folium.Map(location=[40.734695, -73.990372], zoom_start=3, tiles="cartodb positron")

# Plotting Outliers on Map (pickup)
sample_locations = outlier_locations_pickup.head(10000)
for i,j in sample_locations.iterrows():
    if int(j['pickup_latitude']) != 0:
        folium.Marker(list((j['pickup_latitude'],j['pickup_longitude']))).add_to(map_osm_pickup)
map_osm_pickup

# Plotting dropoff cordinates which are outside of New-York (dropoff)
outlier_locations_dropoff = df[((df.dropoff_longitude <= -74.15) | (df.dropoff_latitude <= 40.5774)| \
                (df.dropoff_longitude >= -73.7004) | (df.dropoff_latitude >= 40.9176))]

map_osm_dropoff = folium.Map(location=[40.734695, -73.990372], zoom_start=3, tiles="cartodb positron")

# Plotting Outliers on Map (dropoff)
sample_locations = outlier_locations_dropoff.head(10000)
for i,j in sample_locations.iterrows():
    if int(j['pickup_latitude']) != 0:
        folium.Marker(list((j['dropoff_latitude'],j['dropoff_longitude']))).add_to(map_osm_dropoff)
map_osm_dropoff



#%%


df = pd.concat([df, pd.get_dummies(df['store_and_fwd_flag'],dtype=int)], axis=1)
df.drop(['store_and_fwd_flag'], axis=1, inplace=True)
df = pd.concat([df, pd.get_dummies(df['vendor_id'],dtype=int)], axis=1)
df.drop(['vendor_id'], axis=1, inplace=True)


column_mapping = {1: '1', 2: '2'}

# Use the rename method to rename columns
df = df.rename(columns=column_mapping)





#%%




# #%%
# sns.kdeplot(df['passenger_count'], fill=True)
# plt.title('Density Plot of Trip Duration')
# plt.xlabel('Trip Duration')
# plt.ylabel('Density')
# plt.show()


#%%


cols_to_exclude = ['pickup_datetime', 'dropoff_datetime', 'N', 'Y', '1', '2', 'id']
cols_to_transform = df.drop(cols_to_exclude, axis = 1).columns

# print(df[cols_to_transform].columns)

transformer = PowerTransformer(method='yeo-johnson', standardize=False)
transformer.set_output(transform='pandas')

df[cols_to_transform] = transformer.fit_transform(df[cols_to_transform])


#%%

df.loc[:, 'avg_speed_h'] = 1000 * df['trip_distance(km)'] / df['trip_duration(sec)']
df.loc[:, 'avg_speed_m'] = 1000 * df['distance_manhattan'] / df['trip_duration(sec)']




#%%
Outlier_detection_IQR = True # IQR = 1.5

if Outlier_detection_IQR:
    variable_list = ['trip_duration(sec)','pickup_latitude','pickup_longitude','dropoff_latitude','dropoff_longitude','trip_distance(km)', 'avg_speed_h', 'avg_speed_m']
    fold_value = 1.5
    result = find_limits(df, variable_list, fold_value)

    df = clip_variables(df, result)
    print("Cleaned Data")


#%%
# Visulazing distribution of Trip Duration(Sec) 
sns.kdeplot(df['trip_duration(sec)'], fill=True)
plt.title('Density Plot of Trip Duration')
plt.xlabel('Trip Duration')
plt.ylabel('Density')
plt.show()

#%%
# Visulazing distribution of Trip Duration(Sec) - log Normal
sns.kdeplot(np.log(df['trip_duration(sec)'] + 1), fill=True)
plt.title('Density Plot of Trip Duration - log Normal')
plt.xlabel('Trip Duration')
plt.ylabel('Density')
plt.show()

#%%
# Visulazing distribution of Trip Distance(km) 
sns.kdeplot(df['trip_distance(km)'], fill=True)
plt.title('Density Plot of Trip Distance')
plt.xlabel('Trip Distance')
plt.ylabel('Density')
plt.show()

# %%
# Visulazing distribution of Trip Distance(km) - log Normal
sns.kdeplot(np.log(df['trip_distance(km)']), fill=True)
plt.title('Density Plot of Trip Distance - log Normal')
plt.xlabel('Trip Distance')
plt.ylabel('Density')
plt.show()

# %%
np.mean(df["trip_duration(sec)"])

# %%
# from sklearn.linear_model import LinearRegression
# from sklearn.model_selection import train_test_split, cross_val_score
# from sklearn.metrics import mean_squared_error

# # X = df[["trip_duration(sec)"]]
# # y = df[["trip_distance(km)"]]


# y = df["trip_duration"]
# df.drop(["trip_duration"], axis=1, inplace=True)
# df.drop(['id'], axis=1, inplace=True)
# X = df


# # Spliting the data into training and testing sets

# #----------------------------USE THIS SPLIT FOR TRAINING DATA AND TESTING-------------------------------#
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=123)
#-------------------------------------------------------------------------------------------------------#

# Fiting and Making Predictions
# lr = LinearRegression()
# lr.fit(X_train, y_train)
# y_pred = lr.predict(X_test)

# rmse = np.sqrt(mean_squared_error(y_test, y_pred))
# print("Root Mean Squared Error on Test Set:", rmse)

# # 5-fold cross-validation
# cv_scores = cross_val_score(lr, X, y, cv=5, scoring='neg_mean_squared_error')

# cv_scores = np.sqrt(np.abs(cv_scores))

# print("Cross-Validation Scores:", cv_scores)

# # Average cross-validation score
# print("Mean Cross-Validation Score:", np.mean(cv_scores))

#%%
# Removing Outliers - Experimental Code - DONOT Uncomment 

# import pandas as pd

# percentile_80_distance = df['trip_distance(km)'].quantile(0.8)
# percentile_80_duration = df['trip_duration(sec)'].quantile(0.8)

# df_filtered = df[(df['trip_distance(km)'] <= percentile_80_distance) & (df['trip_duration(sec)'] <= percentile_80_duration)]

# print(df_filtered)

# from sklearn.linear_model import LinearRegression
# from sklearn.model_selection import train_test_split, cross_val_score
# from sklearn.metrics import mean_squared_error
# import numpy as np

# X = df_filtered[["trip_duration(sec)"]]
# y = df_filtered[["trip_distance(km)"]]

# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=123)

# lr = LinearRegression()

# lr.fit(X_train, y_train)

# y_pred = lr.predict(X_test)

# rmse = np.sqrt(mean_squared_error(y_test, y_pred))
# print("Root Mean Squared Error on Test Set:", rmse)

# cv_scores = cross_val_score(lr, X, y, cv=5, scoring='neg_mean_squared_error')

# cv_scores = np.sqrt(np.abs(cv_scores))

# print("Cross-Validation Scores:", cv_scores)

# print("Mean Cross-Validation Score:", np.mean(cv_scores))

# Note : This gives better results than The Linear Regression we are using. 

# %%

# Assuming df is your DataFrame
pickup_locations = df[['pickup_longitude', 'pickup_latitude']]

# Define the number of clusters (adjust as needed)
num_clusters = 4

# Fit K-means clustering model
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
df['pickup_cluster'] = kmeans.fit_predict(pickup_locations)

#%%
# df.head()

#%%
# Count the occurrences of each cluster
cluster_counts = df['pickup_cluster'].value_counts().reset_index(name='pickup_count')

# Display the most common pickup clusters
top_n = 4  # You can adjust this based on your preference
print(f"Top {top_n} Most Common Pickup Clusters:")
print(cluster_counts.head(top_n))

# Optionally, visualize the clusters on a scatter plot
plt.scatter(df['pickup_latitude'], df['pickup_longitude'], c=df['pickup_cluster'], cmap='viridis', alpha=0.5)
plt.title('Pickup Clusters')
     

#%%
#getting common  pickup from each cluster
most_common_pickup_locations_per_cluster = df.groupby('pickup_cluster')[['pickup_latitude', 'pickup_longitude']].agg(lambda x: x.value_counts().index[0]).reset_index()

# Display the most common pickup locations within each cluster
print("Most Common Pickup Locations Within Each Cluster:")
print(most_common_pickup_locations_per_cluster)


#%%


y = df["trip_duration(sec)"]
df.drop(["trip_duration(sec)"], axis=1, inplace=True)
df.drop(['id', 'pickup_datetime', 'dropoff_datetime', 'pickup_cluster'], axis=1, inplace=True)
X = df


# In[224]:

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

X_train.shape, y_train.shape, X_test.shape, y_test.shape

# %%


model = CatBoostRegressor(iterations=100, learning_rate=0.1, depth=6)

# Fit the model
model.fit(X_train, y_train)

# Generate predictions
predictions_catboost = model.predict(X_test)
# %%


print('root mean square error for catboost')
rmse = np.sqrt(mean_squared_error(y_test, predictions_catboost))
print(rmse)




# %%

n_cores = multiprocessing.cpu_count()

xgb_model = xgb.XGBRegressor(n_jobs=n_cores)

# Random Search hyperparameter grid - XGBoost
param_dist = {
    'learning_rate': uniform(0.01, 0.2),
    'n_estimators': randint(50, 200),
    'max_depth': randint(3, 10),
}

# RandomizedSearchCV 
random_search = RandomizedSearchCV(
    xgb_model,
    param_distributions=param_dist,
    n_iter=10,
    scoring='neg_mean_squared_error',  # Using negative MSE for regression
    cv=5,
    verbose=1,
    random_state=123,
    n_jobs=n_cores,
)

# Fit RandomizedSearchCV 
random_search.fit(X_train, y_train)

best_xgb_model = random_search.best_estimator_

y_pred_xgb = best_xgb_model.predict(X_test)

# Root mean squared error on the test set
rmse_xgb = np.sqrt(mean_squared_error(y_test, y_pred_xgb))
print("Root Mean Squared Error on Test Set (XGBoost):", rmse_xgb)

# Best hyperparameters from the RandomizedSearchCV
print("Best Hyperparameters:", random_search.best_params_)




mse = mean_squared_error(y_test, y_pred_xgb)
print(f'Mean Squared Error for catboost: {mse}')




# %%

lr = LinearRegression()

lr.fit(X_train, y_train)

y_pred_lr = lr.predict(X_test)



rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
print("Root Mean Squared Error on Test Set (linear regression):", rmse_lr)




# mse_lr = mean_squared_error(y_test, y_pred_lr)
# print(f'Mean Squared Error for linear_reg: {mse_lr}')



# %%

rf_regressor = RandomForestRegressor(n_estimators=100, random_state=42)

# 5. Fit the model on the training data
rf_regressor.fit(X_train, y_train)

# 6. Make predictions on the test data (if applicable)
y_pred_rf = rf_regressor.predict(X_test)

# Evaluate the model
# mse_rf = mean_squared_error(y_test, y_pred_rf)
# print(f'Mean Squared Error: {mse_rf}')



rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
print("Root Mean Squared Error on Test Set (RFM):", rmse_rf)


# %%
