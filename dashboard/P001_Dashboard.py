import pandas as pd 
import numpy as np 
import streamlit as st
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import geopandas

st.set_page_config(layout = 'wide')

@st.cache_data
def get_data( path ):
    data = pd.read_csv(path)
    data = data.loc[:, ~data.columns.str.contains('^Unnamed')]

    return data

@st.cache_data
def get_geofile(url):
    geofile = geopandas.read_file( url )

    return geofile

##############################################################################################################################
def create_dashboard(data, geofile):
    c01, c02, c03 = st.columns((1,1, 1))
    with c01: 
        f_attributes = st.multiselect( 'Enter Columns', data.columns)
    with c02:
        f_zipcode = st.multiselect('Enter Zipcode', data['ZIPCODE'].unique())
    
    st.markdown('---')

    st.title('Resume')
    number_houses = np.count_nonzero(data['ID'])
    invested = sum(data['PRICE'])
    revenue = sum(data['SELLING_PRICE'])
    ss_revenue = sum(data['SS_SELLING_PRICE'])
    profit = sum(data['EXPECTED_PROFIT'])
    ss_profit = sum(data['SS_EXPECTED_PROFIT'])
    min_price = int( data['PRICE'].min() )
    max_price = int( data['PRICE'].max() )
    avg_price = int( data['PRICE'].mean() )
    df3 = data[['ZIPCODE', 'ZIPCODE_PRICE_M2']].groupby('ZIPCODE').mean().reset_index()
    df3['ZIPCODE_PRICE_M2'] = round(df3['ZIPCODE_PRICE_M2'], 2)

    if f_zipcode != []:
        number_houses = np.count_nonzero(data['ID'].loc[data['ZIPCODE'].isin(f_zipcode)])
        invested = sum(data['PRICE'].loc[data['ZIPCODE'].isin(f_zipcode)])
        revenue = sum(data['SELLING_PRICE'].loc[data['ZIPCODE'].isin(f_zipcode)])
        ss_revenue = sum(data['SS_SELLING_PRICE'].loc[data['ZIPCODE'].isin(f_zipcode)])
        profit = sum(data['EXPECTED_PROFIT'].loc[data['ZIPCODE'].isin(f_zipcode)])
        ss_profit = sum(data['SS_EXPECTED_PROFIT'].loc[data['ZIPCODE'].isin(f_zipcode)])
        min_price = int( data['PRICE'].loc[data['ZIPCODE'].isin(f_zipcode)].min() )
        max_price = int( data['PRICE'].loc[data['ZIPCODE'].isin(f_zipcode)].max() )
        avg_price = int( data['PRICE'].loc[data['ZIPCODE'].isin(f_zipcode)].mean() )
        df3 = df3.loc[df3['ZIPCODE'].isin(f_zipcode)]

    else:
        number_houses = np.count_nonzero(data['ID'])
        invested = sum(data['PRICE'])
        revenue = sum(data['SELLING_PRICE'])
        ss_revenue = sum(data['SS_SELLING_PRICE'])
        profit = sum(data['EXPECTED_PROFIT'])
        ss_profit = sum(data['SS_EXPECTED_PROFIT'])
        profit = sum(data['EXPECTED_PROFIT'])
        ss_profit = sum(data['SS_EXPECTED_PROFIT'])
        min_price = int( data['PRICE'].min() )
        max_price = int( data['PRICE'].max() )
        avg_price = int( data['PRICE'].mean() )
        df3 = df3[['ZIPCODE', 'ZIPCODE_PRICE_M2']]


    with c03:
        f_price = st.slider('Histogram Buying Price Slider', min_price, max_price, avg_price)
    
    c1, c2, c3 = st.columns((1,1,1))
    c1.subheader(f'Number of Houses: \n {number_houses}')
    c2.subheader(f'Total Invested: \n US$ {invested:,.2f}')
    c3.subheader(f'Revenue: \n US$ {revenue:,.2f}')

    c4, c5, c6 = st.columns((1,1,1))
    c4.subheader(f'Summer-Spring Revenue: \n US$ {ss_revenue:,.2f}')
    c5.subheader(f'Profit: \n US$ {profit:,.2f}')
    c6.subheader(f'Summer-Spring Profit: \n US$ {ss_profit:,.2f}')

    st.markdown('---')

    ## ---------- Overview ---------- ##

    st.title('Overview')

    if ( f_zipcode != [] ) & ( f_attributes != [] ):
        data = data.loc[ data['ZIPCODE'].isin(f_zipcode) , f_attributes ]

    elif ( f_zipcode != [] ) & ( f_attributes == [] ):
        data = data.loc[ data['ZIPCODE'].isin( f_zipcode) , : ]
            
    elif ( f_zipcode == [] ) & ( f_attributes != [] ):
        data = data.loc[: , f_attributes ]

    else:
        data = data.copy()

    st.dataframe(data)

    st.markdown('---')

    ## ---------- Histograma ---------- ##
    c7, c07, c8 = st.columns((1,0.2,1))

    df_histogram = data.loc[ (data['PRICE'] <= f_price) ]

    #data plot
    fig = px.histogram(df_histogram, x='PRICE', nbins=50)
    fig.update_layout(yaxis_title= '# PROPERTIES')

    with c7:
        st.header('Buying Price Distribution')
        st.plotly_chart(fig, use_container_width=True)

    ## ---------- Descriptive Statistic ---------- ##

    num_attributes = data.select_dtypes(include = ['int64', 'float64'])
    media = pd.DataFrame( num_attributes.apply(np.mean ))
    mediana = pd.DataFrame(num_attributes.apply(np.median))
    std = pd.DataFrame(num_attributes.apply(np.std))
    max_ = pd.DataFrame(num_attributes.apply(np.max))
    min_ = pd.DataFrame(num_attributes.apply(np.min))

    df1 = pd.concat([min_, max_, media, mediana, std], axis = 1).reset_index()

    df1.columns = ['ATTRIBUTES','MIN', 'MAX', 'MEAN', 'MEDIAN','STD']

    c8.header('Descriptive Analysis')
    c8.dataframe(df1, height = 450)

    st.markdown('---')

    ## ---------- Maps ---------- ##
    c9, c11 = st.columns((1, 1))

    ## ----- Portfolio Density ----- ##

    c9.header('Portfolio Density')

    density_map = folium.Map(location = [data['LAT'].mean(),
                                        data['LONG'].mean()],
                                        default_zoom_start = 15)

    marker_cluster = MarkerCluster().add_to(density_map)

    for name, row in data.iterrows():
        folium.Marker( [row['LAT'], row['LONG']],
                    popup='Sold US${0} on: {1}. Features: {2} m2, {3} bedrooms, {4} bathrooms, year built: {5}'.format( round(row['PRICE'], 2),
                                                                    row['DATE'],
                                                                    round(row['M2_LIVING'], 2),
                                                                    row['BEDROOMS'],
                                                                    row['BATHROOMS'],
                                                                    row['YR_BUILT'] )).add_to(marker_cluster)
        
    with c9:
        folium_static(density_map)

    ## ----- Price Density ----- ##

    c11.header('Price Density')

    df2 = data[['PRICE', 'ZIPCODE']].groupby('ZIPCODE').mean().reset_index()
    df2.columns = ['ZIP', 'PRICE']

    geofile = geofile[ geofile['ZIP'].isin( df2['ZIP'].tolist() ) ]

    region_price_map = folium.Map( location = [data['LAT'].mean(), data['LONG'].mean()],
                                default_zoom_start = 15)

    folium.Choropleth( data = df2,
                                geo_data = geofile,
                                columns=['ZIP', 'PRICE'],
                                key_on='feature.properties.ZIP',
                                fill_color='YlOrRd',
                                fill_opacity = 0.7,
                                line_opacity = 0.2,
                                legend_name='AVG PRICE').add_to(region_price_map)

    with c11:
        folium_static(region_price_map)

    st.markdown('---')

    ## ---------- Zipcode Price/M2 ---------- ##

    st.header('Price/M2 by Zipcode')

    fig = px.bar(df3, y='ZIPCODE_PRICE_M2', x='ZIPCODE',  text_auto='.2f',text="ZIPCODE_PRICE_M2", 
                labels={'ZIPCODE_PRICE_M2':'PRICE/M2(US$)'})
    fig.update_layout(xaxis = {'type' : 'category'})
    st.plotly_chart(fig, use_container_width=True)

    ############################################################################################
    st.markdown('---')
    st.markdown('---')
    st.markdown('---')

    st.title('Contact Information')

    st.write('')
    st.markdown('This dashboard was built as the final deliverable of **House Rocket Insights Project** by **Matheus Vasconcelos**.')
    st.markdown('Check the code for this project on [Github](https://github.com/matheusjohan1/P001_House_Rocket_Insights).')
    st.markdown('Check my Portfolio on: [Portfolio](xxxx)')
    st.markdown('Reach Out: [LinkedIn](https://www.linkedin.com/in/matheusjohan1/)')
    
    return None

if __name__ == '__main__':
    # ETL 

    ## Data Extraction ## 

    # Get Data
    path = 'data/selling_list.csv'
    url = 'https://opendata.arcgis.com/datasets/83fc2e72903343aabff6de8cb445b81c_2.geojson'

    data = get_data(path)
    geofile = get_geofile(url)
 
    ## Transformation ##

    create_dashboard(data, geofile)
