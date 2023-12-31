import pandas as pd
import folium 
import geopandas as gpd
from folium.features import GeoJsonPopup, GeoJsonTooltip
import streamlit as st
from streamlit_folium import folium_static


st.sidebar.markdown("### US Housing Market Dashboard")
st.sidebar.markdown("This app is built using Streamlit and uses data source from redfin housing market data.")

#Add title and subtitle to the main interface of the app
st.title("U.S. Real Estate Insights")
st.markdown("Where are the hottest housing markets in the U.S.? Select the housing market metrics you are interested in and your insights are just a couple clicks away. Hover over the map to view more details.")



@st.cache_data
def read_csv(path):
    return pd.read_csv(path, compression='gzip', sep='\t', quotechar='"')
     
#Data prepartion to only retrieve fields that are relevent to this project
housing_price_df=read_csv('state_market_tracker.tsv000.gz')
housing_price_df=housing_price_df[['period_begin','period_end','period_duration','property_type','median_sale_price','median_sale_price_yoy','homes_sold','state_code']]
housing_price_df=housing_price_df[(housing_price_df['period_begin']>='2020-10-01') & (housing_price_df['period_begin']<='2021-10-01')]

#st.write(housing_price_df)  

@st.cache_data
def read_file(path):
    return gpd.read_file(path)

#Read the geojson file
gdf = read_file('us-state-boundaries.geojson')
#st.write(gdf.head())

#Merge the housing market data and geojson file into one dataframe
df_final = gdf.merge(housing_price_df, left_on="stusab", right_on="state_code", how="outer")
df_final=df_final[['period_begin','period_end','period_duration','property_type','median_sale_price','median_sale_price_yoy','homes_sold','state_code','name','stusab','geometry']]
df_final= df_final[~df_final['period_begin'].isna()]

# st.write(df_final.head()) 

#Create three columns/filters
col1, col2, col3 = st.columns(3)

with col1:
     period_list=df_final["period_begin"].unique().tolist()
     period_list.sort(reverse=True)
     year_month = st.selectbox("Snapshot Month", period_list, index=0)

with col2:
     prop_type = st.selectbox(
                "View by Property Type", ['All Residential', 'Single Family Residential', 'Townhouse','Condo/Co-op','Single Units Only','Multi-Family (2-4 Unit)'] , index=0)

with col3:
     metrics = st.selectbox("Select Housing Metrics", ["median_sale_price","median_sale_price_yoy", "homes_sold"], index=0)

df_final=df_final[df_final["period_begin"]==year_month]
df_final=df_final[df_final["property_type"]==prop_type]
df_final=df_final[['period_begin','period_end','period_duration','property_type',metrics,'state_code','name','stusab','geometry']]

# st.write(df_final.head()) 

#Initiate a folium map
m = folium.Map(location=[40, -100], zoom_start=4,tiles=None)
folium.TileLayer('CartoDB positron',name="Light Map",control=False).add_to(m)

#Plot Choropleth map using folium
choropleth1 = folium.Choropleth(
    geo_data='us-state-boundaries.geojson',     #This is the geojson file for the Unite States
    name='Choropleth Map of U.S. Housing Prices',
    data=df_final,                                  #This is the dataframe we created in the data preparation step
    columns=['state_code', metrics],                #'state code' and 'metrics' are the two columns in the dataframe that we use to grab the median sales price for each state and plot it in the choropleth map
    key_on='feature.properties.stusab',             #This is the key in the geojson file that we use to grab the geometries for each state in order to add the geographical boundary layers to the map
    fill_color='YlGn',
    nan_fill_color="White",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Housing Market Metrics',
    highlight=True,
    line_color='black').geojson.add_to(m)


geojson1 = folium.features.GeoJson(
               data=df_final,
               name='United States Housing Prices',
               smooth_factor=2,
               style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
               tooltip=folium.features.GeoJsonTooltip(
                   fields=['period_begin',
                           'period_end',
                           'name',
                           metrics,],
                   aliases=["Period Begin:",
                            'Period End:',
                            'State:',
                            metrics+":"], 
                   localize=True,
                   sticky=False,
                   labels=True,
                   style="""
                       background-color: #F0EFEF;
                       border: 2px solid black;
                       border-radius: 3px;
                       box-shadow: 3px;
                   """,
                   max_width=800,),
                    highlight_function=lambda x: {'weight':3,'fillColor':'grey'},
                   ).add_to(m)

folium_static(m)
