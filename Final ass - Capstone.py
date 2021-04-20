#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
pd.set_option("display.max_rows", 20, "display.max_columns", 20)
import numpy as np # library to handle data in a vectorized manner
import matplotlib.cm as cm
import matplotlib.colors as colors
import random # library for random number generation
import json # library to handle JSON files
import urllib
#The following packages are useful but I did not use here
#!pip install beautifulsoup4
#from bs4 import BeautifulSoup
#!pip install lxml

get_ipython().system('pip install geopy')
from geopy.geocoders import Nominatim # module to convert an address into latitude and longitude values

# libraries for displaying images
from IPython.display import Image 
from IPython.core.display import HTML 
    
# tranforming json file into a pandas dataframe library
from pandas.io.json import json_normalize

# import k-means from clustering stage
from sklearn.cluster import KMeans

get_ipython().system(' pip install folium==0.5.0')
import folium # plotting library

print('Folium installed')
print('Libraries imported.')


# In[3]:


Val_df = pd.read_csv(r"C:\Users\Andrew\Downloads\ValenciaData.csv")
Val_df.head()


# In[30]:


Spain_json=result['results']


# In[31]:


# define the dataframe columns
column_names = ['PostCode', 'PlaceName', 'Latitude', 'Longitude'] 

# instantiate the dataframe
Spain_df = pd.DataFrame(columns=column_names)
Spain_df


# In[38]:


for data in Spain_json:
    codigopostal = data['Postal_Code']
    zona = data['Place_Name']
    lat = data['Latitude']
    long = data['Longitude']

    Spain_df = Spain_df.append({'PostCode': codigopostal,
                                          'PlaceName': zona,
                                          'Latitude': lat,
                                          'Longitude': long}, ignore_index=True)
print(Spain_df)


# In[40]:


df1=Val_df.merge(Spain_df, on='PostCode', how='left')
df1


# In[4]:


#adding a condition to filter out the majority of unneccessary data for elsewhere in Spain
where = urllib.parse.quote_plus("""
{
    "Postal_Code": {
        "$gt": 45999
    }
}
""")
url = 'https://parseapi.back4app.com/classes/Spainpostalcode_Spain_Postal_Code?limit=50&order=Postal_Code&keys=Place_Name,Postal_Code,Longitude,Latitude&where=%s' % where
headers = {
    'X-Parse-Application-Id': 'L1J6TLuzAJOD0PTSbaxxAL6MumtHfwkyr2Fg41Xq', # This is your app's application id
    'X-Parse-REST-API-Key': '0W3mihPdwBy2bud7Tj7fSS4CLR223AX1Qii5zZYd' # This is your app's REST API key
}
rawdata = json.loads(requests.get(url, headers=headers).content.decode('utf-8')) # Here you have the data that you need
print(rawdata)


# In[5]:


#improve the clarity of the output
Spain_data_json=rawdata['results']
Spain_data_json


# In[6]:


#creating a new empty dataframe to put this data
# define the dataframe columns
column_names = ['PostCode', 'PlaceName', 'Latitude', 'Longitude'] 

# instantiate the dataframe
Spain_df = pd.DataFrame(columns=column_names)
Spain_df


# In[16]:


#populate the new dataframe

for data in Spain_data_json:
    codigopostal = data['Postal_Code']
    zona = data['Place_Name']
    lat = data['Latitude']
    long = data['Longitude']

    Spain_df = Spain_df.append({'PostCode': codigopostal,
                                          'PlaceName': zona,
                                          'Latitude': lat,
                                          'Longitude': long}, ignore_index=True)
Spain_df.head()


# In[11]:


#Verify that dataframes contain the same datatype to enable merging
Spain_df['PostCode']=Spain_df['PostCode'].astype(str)
Val_df['PostCode']=Val_df['PostCode'].astype(str)


# In[13]:


#merging
df1=Val_df.merge(Spain_df, on='PostCode', how='left')
df1


# In[23]:


#remove NaN values
df1.dropna(subset = ['PlaceName'], inplace=True)
df1


# In[78]:





# In[80]:


for index,value in df1['Neighbourhood'].items():
    try:
        address=value+', Valencia, Spain'
        geolocator = Nominatim(user_agent="foursquare_agent")
        location = geolocator.geocode(address)
        latitude = location.latitude
        longitude = location.longitude
        df1['Latitude'][index]=latitude
        df1['Longitude'][index]=longitude
    except:
        pass
df1


# In[52]:


for index, row in df1.iterrows():
    try:
        address = df1['Neighbourhood'][index] + ", ES"
        geolocator = Nominatim(user_agent="foursquare_agent")
        location = geolocator.geocode(address)
        latitude = location.latitude
        longitude = location.longitude
        df1['Latitude'][i]=latitude
        df1['Longitude'][i]=longitude
    except AttributeError:
        pass
df1


# In[81]:


#Create a clustering based on coordinates and median salary
kclusters=6
val_clustering = df1.drop(['PostCode','Neighbourhood','NumberOfTaxpayers','PlaceName'],1)
val_clustering


# In[82]:


# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(val_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10]


# In[84]:


#add cluster data to the main dataframe
df1.insert(8, 'Cluster2', kmeans.labels_)
df1


# In[85]:


#find address of Valencia in order to create correctly centred folium map
address = 'Valencia, ES'

geolocator = Nominatim(user_agent="tora_the_explorer")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print('The geograpical coordinates of Valencia are {}, {}.'.format(latitude, longitude))


# In[94]:


#generate map to visualize the neighbourhoods
# create map
map_Valencia = folium.Map(location=[latitude, longitude], zoom_start=11)
kclusters=6
# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lng, neigh, medsal, cluster2 in zip(df1['Latitude'], df1['Longitude'], df1['Neighbourhood'], df1['MedianSalary'], df1['Cluster2']):
    label = folium.Popup(str(neigh) + ', Cluster ' + str(cluster2), parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=10,
        popup=label,
        color=rainbow[cluster2-1],
        fill=True,
        fill_color=rainbow[cluster2-1],
        fill_opacity=0.7).add_to(map_Valencia)
       
map_Valencia


# In[95]:


#sort dataframe by median salary in descending order
df2=df1.sort_values(by='Cluster2', ascending=False, na_position='first', inplace=False)
df2


# In[99]:


CLIENT_ID = 'YEOIOK2UK5DZ2CUM4NQCTZBFJ124FL2TSJTPIJ0EBLDQL1JU' # your Foursquare ID
CLIENT_SECRET = 'FZOLLHQ5PGTLLVZ3DDJONQ2TQ1WDUMPRKNPF40LJOW30HEN4' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version
LIMIT = 100 # A default Foursquare API limit value
ACCESS_TOKEN = '20HBIOBQI4QJ4NAN11RRB2GGJUTNDW5VSEECRZOZXS5LK2YN'

print('Your credentails:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)


# In[100]:


address = 'Pla de Remei, ES'

geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print(latitude, longitude)


# In[101]:


search_query = 'bar'
radius = 500
print(search_query + ' .... OK!')

url = 'https://api.foursquare.com/v2/venues/search?client_id={}&client_secret={}&ll={},{}&oauth_token={}&v={}&query={}&radius={}&limit={}'.format(CLIENT_ID, CLIENT_SECRET, latitude, longitude,ACCESS_TOKEN, VERSION, search_query, radius, LIMIT)
url


# In[104]:


results = requests.get(url).json()

venues = results['response']['venues']
PDR_venues = json_normalize(venues)

PDR_venues


# In[105]:


# function that extracts the category of the venue
def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


# In[106]:


filtered_columns = ['name', 'categories', 'location.lat', 'location.lng']
PDR_venues =PDR_venues.loc[:, filtered_columns]

# filter the category for each row
PDR_venues['categories'] = PDR_venues.apply(get_category_type, axis=1)

# clean columns, not required here
#PDR_venues.columns = [col.split(".")[-1] for col in PDR_venues.columns]

PDR_venues.head()


# In[109]:


#Update long and lat column titles
PDR_venues.rename(columns={'location.lat': 'latitude', 'location.lng': 'longitude'}, inplace=True)
PDR_venues


# In[110]:


print('{} venues were returned by Foursquare.'.format(PDR_venues.shape[0]))


# In[111]:


print('There are {} uniques categories.'.format(len(PDR_venues['categories'].unique())))


# In[112]:


#reupdate the central map coordinates
address = 'Pla de Remei, ES'

geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print(latitude, longitude)


# In[119]:


PDR_map = folium.Map(location=[latitude, longitude], zoom_start=16)
# add a red circle marker to represent central point of Pla de Remei
folium.features.CircleMarker(
    [latitude, longitude],
    radius=10,
    color='red',
    popup='CENTRE',
    fill = True,
    fill_color = 'red',
    fill_opacity = 0.6
).add_to(PDR_map)
# add all venues as blue circle markers
for lat, lng, label in zip(PDR_venues.latitude, PDR_venues.longitude, PDR_venues.categories):
    folium.features.CircleMarker(
        [lat, lng],
        radius=5,
        color='blue',
        popup=label,
        fill = True,
        fill_color='blue',
        fill_opacity=0.6
    ).add_to(PDR_map)
    
PDR_map


# In[ ]:




