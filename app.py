import streamlit as st
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import math

from matplotlib import pyplot as plt
import plotly.graph_objects as go
import cufflinks as cf
from plotly.offline import iplot, init_notebook_mode
import plotly.express as px

#matplotlib inline
init_notebook_mode(connected=True)
cf.go_offline(connected=True)

cf.set_config_file(theme="pearl")

st.sidebar.title('Assignment')
st.sidebar.text('Hover over the points for more information')

employees_data = pd.read_csv('employees.csv')
print(employees_data.info())
sns.heatmap(employees_data.isnull())
print(employees_data.tail())

lat_lon = pd.read_csv('employees_1.csv', sep=';')
employees_data = pd.concat([employees_data,lat_lon], axis=1)
#employees_data.head(2)

hq_location = {"Name":"Head quater", "Street": "Betonimienkuja 3", "Postal code": "02150", 
                            "City": "Espoo", "Country": "FI", "Latitude": 60.1807142, "Longitude": 24.8318569}
hq_location_df = pd.DataFrame(hq_location,index=[0])
#print(hq_location_df)
employees_data = pd.concat([hq_location_df,employees_data],ignore_index=True)
#employees_data.head(2)

# Distance calculation
def coordinate_dislat(x1):
    val = (x1-math.radians(60.180714))
    return val
def coordinate_dislon(y1):
    val= (y1-math.radians(24.8318569))
    return val
# calculating the radian value
employees_data['radx']= employees_data["Latitude"].apply(math.radians)
employees_data['rady']= employees_data["Longitude"].apply(math.radians)
# performing difference in randian value with the headquater radians
employees_data['Dlat'] = employees_data['radx'].apply(coordinate_dislat)
employees_data['Dlon'] = employees_data['rady'].apply(coordinate_dislon)

## Haversine formula for the actual distance calculation in map
# a = sin²(ΔlatDifference/2) + cos(lat1).cos(lt2).sin²(ΔlonDifference/2)
# shortest_distance = 2 * sina(sqrt(a)) * radius of earth

# Adusting dataframe environment to perform above formula and to find shortest distance to the headquater

employees_data["Sin_sq_dlat"]=employees_data["Dlat"].apply(lambda x: math.sin(x/2)**2)
employees_data["Sin_sq_dlon"]=employees_data["Dlon"].apply(lambda x: math.sin(x/2)**2)
employees_data["cos_rad_headquater"]=employees_data["Dlon"].apply(lambda x: math.cos(math.radians(60.180714)))
employees_data['cos_radx'] = employees_data['radx'].apply(lambda x: math.cos(x))
radius_of_earth = 6371
# finding the value of a
employees_data["value_of_a"] = employees_data['Sin_sq_dlat'] + employees_data['cos_rad_headquater'] * employees_data['cos_radx'] * employees_data['Sin_sq_dlon']
# finding the value of distance from headquater
employees_data['distance_to_headquater_km'] = employees_data['value_of_a'].apply(lambda x: 2* radius_of_earth * math.asin(math.sqrt(x)))
#rounding the distance value
employees_data['distance_to_headquater_km'] = employees_data['distance_to_headquater_km'].apply(round)
# Poping out unnecessary column generated during the calculation
del_column = ['radx', 'rady', 'Dlat', 'Dlon', 'Sin_sq_dlat', 'Sin_sq_dlon', 'cos_rad_headquater', 'cos_radx', 'value_of_a']
employees_data = employees_data.drop(del_column,axis=1)
#print(employees_data.head(2))

#print(employees_data.describe())
# shows the value of shortest distance 1889 km which inside of Finland is quite not true, let's check the actual rows
#print(employees_data[employees_data.distance_to_headquater_km==1889])
# This address is somewhere in UK .
# We are analysing the data in Finland so let's pop it out too.
employees_data = employees_data.drop(64,axis=0)
#print(employees_data.describe())
#employees_data[62:66]

# downloading the data from the server
url = "https://geo.stat.fi/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=postialue:pno_tilasto&outputFormat=csv"
data = pd.read_csv(url)
#print(data.head(2))

# Out of lots of column, we are at this moment just selecting the average yearly income and postal code from the downloded data. 
data_selected = data[["postinumeroalue", "hr_ktu"]]
# Renaming the column to have the better understanding of data
data_selected = data_selected.rename(columns={'postinumeroalue':'Postal code', 'hr_ktu': 'Yearly_avg_income'})
#print(data_selected.head(2))

# changing the data types
employees_data['Postal code']=employees_data['Postal code'].apply(int)
# performing left join
employees_data = employees_data.merge(data_selected, on = 'Postal code', how = 'left')
#print(employees_data.info())

# above heatmap shows somewhere in the index between 40 to 45 shows the null value, let's fix this issue
#print(employees_data.Yearly_avg_income[40:45])
# it seems like index 44 have not the yearly_avg_income
# further let's see what we can find in that index
#print(employees_data.iloc[44,:])
# checking if there is null value in data_selected data frame
#sns.heatmap(data_selected.isnull())
#It seems to have all the postal code and values
#further checking the information of null value index
#print(employees_data[employees_data['Postal code']==26360])
#print(data_selected[data_selected['Postal code']==26360])
# While cross checking the google maps and data_selected data frame, it is found that there is a typo. It seems, 
# instead of 20360 there is 26360
# Let's correct this typo and fill the nan value with correct information
# on reviewing avg yearly income of the postal code region 20360 is 21333.
employees_data['Postal code'][44]=20360
employees_data['Yearly_avg_income'][44]=21333
employees_data['City'][43] = 'Helsinki'
employees_data['City'][36] = 'Oulu'

closest_to_headquater = employees_data.sort_values('distance_to_headquater_km').iloc[1,:]
#print('----------------------------------')
#print(f'The employee who lives closest to the headquater is {closest_to_headquater.Name}')
#print('----------------------------------')
#print(closest_to_headquater)

#Adjusting new column with status of employee to determine the employee location and headquater location.
employees_data['Status'] = employees_data.distance_to_headquater_km==0
employees_data.Status='Employee'
employees_data.Status[0] = 'Headquater'
within_ten_km = employees_data[employees_data.distance_to_headquater_km <= 10]
#print('---------------------------------')
#print(f"Number of people living within 10 km from the office is {len(within_ten_km)-1}")
# Within_ten_km dataframe includes the headquater itself so to find number of people we have to substract 1 from the length.
#print('---------------------------------')

# sorting wealthiest region among the employees address
wealthiest_region = employees_data.sort_values('Yearly_avg_income', ascending=False)
# Thus three employees among all the employees living in wealthiest region is:
employees_in_welthiest_region = wealthiest_region.iloc[:3]
#Adusting the new columns for the visualization

#print('----------------------------------------')
#print(f'The name of three employee living in welthiest region are {employees_in_welthiest_region.Name[21]} , {employees_in_welthiest_region.Name[43]}, and {employees_in_welthiest_region.Name[77]}.')
#print("----------------------------------------")
#print('There information in below:')
#print(employees_in_welthiest_region)

#Developing function for plotting map.
def plot_map(dataframe,color,title):
    fig = px.scatter_geo(dataframe, lat='Latitude', lon = 'Longitude',
                     color = color, size= 'Yearly_avg_income', 
                     hover_data =['distance_to_headquater_km'],
                     hover_name ='Name', scope='europe', basemap_visible=True, width=800,height=800,
                     opacity=0.5,projection='mercator',center = {'lat':60, 'lon':24},
                    title=title) 
    fig.show()

    
option = st.sidebar.selectbox('Select from the below dropdown for the options', 
                      ('Overall Information', 
                      'Who lives closest to the company Headquater',
                      'How many people live within 10 KM of the office',
                      'Three employees living in the wealthiest regions'))
st.sidebar.write('You have selected:', option)
#plot_map(employees_data, 'Status', 'Distance and Yearly avg information of Employee')

df = employees_data.sort_values('distance_to_headquater_km').iloc[:2,:]
#plot_map(df,'Name','Neareast employee to the Headquater')

#plot_map(within_ten_km,'Name','Employee within 10 km radius')

#plot_map(employees_in_welthiest_region,'Name','Wealthiest Region Employee')
if option == 'Overall Information':
    fig = px.scatter_geo(employees_data, lat='Latitude', lon = 'Longitude',
                         color = 'Status', size= 'Yearly_avg_income', 
                         hover_data =['distance_to_headquater_km'],
                         hover_name ='Name', scope='europe', basemap_visible=True, width=800,height=800,
                         opacity=0.5,projection='mercator',center = {'lat':60, 'lon':24},
                        title='Overall Information')
    st.plotly_chart(fig)
elif option == 'Who lives closest to the company Headquater':
    
    st.subheader('Closest person to live from Headquater is ' + closest_to_headquater.Name)
    fig = px.scatter_geo(df, lat='Latitude', lon = 'Longitude',
                         color = 'Name', size= 'Yearly_avg_income', 
                         hover_data =['distance_to_headquater_km'],
                         hover_name ='Name', scope='europe', basemap_visible=True, width=800,height=800,
                         opacity=0.5,projection='mercator',center = {'lat':60, 'lon':24},
                        title='Closest to the Company Headquater')
    st.plotly_chart(fig)
elif option == 'How many people live within 10 KM of the office':
    
    st.subheader('Number of people living within 10 KM radius is ' + str(len(within_ten_km)-1))
    fig = px.scatter_geo(within_ten_km, lat='Latitude', lon = 'Longitude',
                         color = 'Name', size= 'Yearly_avg_income', 
                         hover_data =['distance_to_headquater_km'],
                         hover_name ='Name', scope='europe', basemap_visible=True, width=800,height=800,
                         opacity=0.5,projection='mercator',center = {'lat':60, 'lon':24},
                        title='Within 10 KM radius from Headquater')
    st.plotly_chart(fig)
elif option == 'Three employees living in the wealthiest regions':
    st.subheader('The name of three employee living in welthiest region are ' + str(employees_in_welthiest_region.Name[21]) +', ' + str(employees_in_welthiest_region.Name[43]) +',  and ' + str(employees_in_welthiest_region.Name[77])+'.')
    
    fig = px.scatter_geo(employees_in_welthiest_region, lat='Latitude', lon = 'Longitude',
                         color = 'Name', size= 'Yearly_avg_income', 
                         hover_data =['distance_to_headquater_km'],
                         hover_name ='Name', scope='europe', basemap_visible=True, width=800,height=800,
                         opacity=0.5,projection='mercator',center = {'lat':60, 'lon':24},
                        title='Three wealthiest regions employee among all the employee')
    st.plotly_chart(fig)
