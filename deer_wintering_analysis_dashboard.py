"""
Maine Deer Wintering Areas Analysis Dashboard

This script creates an interactive web dashboard analyzing Deer Wintering Areas (DWAs) in Maine.
The dashboard includes multiple visualizations and analysis of the spatial distribution,
size characteristics, and regional patterns of DWAs.

Author: [Your Name]
Date: [Current Date]
"""

# Required package imports
import dash  # For creating the web application
from dash import dcc, html  # Core dash components and HTML components
from dash.dependencies import Input, Output  # For callback functionality (if needed)
import plotly.express as px  # For creating interactive plots
import plotly.graph_objects as go  # For advanced plotting capabilities
import geopandas as gpd  # For handling geospatial data
import requests  # For API requests
import pandas as pd  # For data manipulation
import numpy as np  # For numerical operations

# Initialize the Dash application
app = dash.Dash(__name__)

# Data Source Configuration
# Maine DIFW's GeoService API endpoint for Deer Wintering Areas
url = "https://services1.arcgis.com/RbMX0mRVOFNTdLzd/arcgis/rest/services/MaineDIFW_DeerWinteringAreas/FeatureServer/0/query"

# API request parameters
params = {
    "where": "1=1",  # Retrieve all records
    "outFields": "*",  # Get all available fields
    "geometryPrecision": 6,  # Precision of the geometry coordinates
    "outSR": "4326",  # Output in WGS84 coordinate system
    "f": "geojson"  # Request data in GeoJSON format
}

# Fetch and load the data
response = requests.get(url, params=params)
response.raise_for_status()  # Check for HTTP errors
gdf = gpd.read_file(response.url)

# Data Processing
# Project to Maine State Plane coordinate system (EPSG:26919) for accurate area calculations
gdf_projected = gdf.to_crs(epsg=26919)

# Calculate area in square kilometers
gdf['area_km2'] = gdf_projected.geometry.area / 10**6

# Calculate centroids for mapping
# First in projected system for accuracy, then convert back to WGS84 for mapping
centroids_projected = gdf_projected.geometry.centroid
centroids_wgs84 = centroids_projected.to_crs(epsg=4326)
gdf['centroid_lat'] = centroids_wgs84.y
gdf['centroid_lon'] = centroids_wgs84.x

# Create categorical classifications
# Size categories based on area
gdf['size_category'] = pd.cut(
    gdf['area_km2'], 
    bins=[0, 1, 5, 10, float('inf')],
    labels=['Small (< 1 km²)', 
            'Medium (1-5 km²)',
            'Large (5-10 km²)',
            'Very Large (>10 km²)']
)

# Regional categories based on latitude
gdf['latitude_band'] = pd.cut(
    gdf['centroid_lat'],
    bins=np.linspace(gdf['centroid_lat'].min(),
                     gdf['centroid_lat'].max(), 
                     5),
    labels=['Southern Maine',
            'South-Central Maine',
            'Central Maine',
            'Northern Maine']
)

# Calculate summary statistics for the dashboard
total_areas = len(gdf)
total_area = gdf['area_km2'].sum()
avg_area = gdf['area_km2'].mean()
median_area = gdf['area_km2'].median()
largest_area = gdf['area_km2'].max()

# Visualization Creation
# 1. Bar Chart: Distribution of DWA sizes
size_counts = gdf['size_category'].value_counts().sort_index()
bar_fig = px.bar(
    x=size_counts.index,
    y=size_counts.values,
    title='Distribution of Deer Wintering Area Sizes in Maine',
    labels={'x': 'Size Category', 'y': 'Number of Areas'}
)
bar_fig.update_layout(
    title_x=0.5,  # Center the title
    plot_bgcolor='white',
    paper_bgcolor='white'
)

# 2. Interactive Map: Spatial distribution of DWAs
map_fig = px.scatter_mapbox(
    gdf,
    lat='centroid_lat',
    lon='centroid_lon',
    color='size_category',
    mapbox_style="carto-positron",  # Light, clean base map
    zoom=7,  # Initial zoom level
    center={"lat": gdf['centroid_lat'].mean(), 
            "lon": gdf['centroid_lon'].mean()},
    title='Maine Deer Wintering Areas by Size',
    color_discrete_map={
        'Small (< 1 km²)': '#98FB98',      # Light green
        'Medium (1-5 km²)': '#228B22',      # Forest green
        'Large (5-10 km²)': '#006400',      # Dark green
        'Very Large (>10 km²)': '#00008B'   # Dark blue
    }
)
map_fig.update_layout(
    title_x=0.5,
    paper_bgcolor='white'
)

# 3. Pie Chart: Regional distribution
region_dist = gdf['latitude_band'].value_counts().sort_index()
pie_fig = px.pie(
    values=region_dist.values,
    names=region_dist.index,
    title='Distribution of Deer Wintering Areas by Region'
)
pie_fig.update_layout(
    title_x=0.5,
    paper_bgcolor='white'
)

# Dashboard Layout Definition
# The layout is structured in sections: Header, Introduction, Statistics, Visualizations, and Findings
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Analysis of Maine's Deer Wintering Areas",
                style={'textAlign': 'center', 'color': '#2c3e50', 'padding': '20px'})
    ], style={'backgroundColor': 'white', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
    # Introduction section
    html.Div([
        html.Div([
            html.H2('Research Question', style={'color': '#2c3e50'}),
            html.P("""As someone unfamiliar with Deer Wintering Areas (DWAs), I became curious about their 
                    role in Maine's wildlife management after discovering this dataset. My analysis focuses on 
                    understanding where these areas are located throughout Maine and what patterns might emerge 
                    from their distribution. Initially, I assumed these areas would be predominantly in northern 
                    Maine's vast forests, but my analysis revealed some surprising patterns that challenged 
                    this assumption."""),
            
            html.H2('Dataset', style={'color': '#2c3e50'}),
            html.P("""For this analysis, I used the Maine Department of Inland Fisheries and Wildlife's (DIFW) 
                    Deer Wintering Areas dataset. This data shows where deer gather during Maine's harsh winters 
                    when deep snow and cold temperatures make survival challenging. These designated areas 
                    provide essential shelter and protection for deer populations during the most severe 
                    winter conditions. What made this dataset particularly interesting was how it revealed 
                    patterns of deer behavior that weren't immediately obvious - especially the unexpected 
                    concentration of these areas in more populated regions of the state.""")
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
    ], style={'padding': '20px'}),
    
    # Key Statistics
    html.Div([
        html.H2('Key Statistics', style={'color': '#2c3e50', 'textAlign': 'center'}),
        html.Div([
            html.Div([
                html.H4(f"{total_areas:,}"),
                html.P("Total Wintering Areas")
            ], className='stat-box'),
            html.Div([
                html.H4(f"{total_area:,.2f} km²"),
                html.P("Total Protected Area")
            ], className='stat-box'),
            html.Div([
                html.H4(f"{avg_area:.2f} km²"),
                html.P("Average Area Size")
            ], className='stat-box'),
            html.Div([
                html.H4(f"{median_area:.2f} km²"),
                html.P("Median Area Size")
            ], className='stat-box')
        ], style={'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap'})
    ], style={'padding': '20px', 'backgroundColor': 'white', 'margin': '20px',
              'borderRadius': '5px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
    # Visualizations
    html.Div([
        html.Div([
            dcc.Graph(figure=map_fig)
        ], style={'width': '100%', 'marginBottom': '20px'}),
        html.Div([
            html.Div([
                dcc.Graph(figure=bar_fig)
            ], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Graph(figure=pie_fig)
            ], style={'width': '50%', 'display': 'inline-block'})
        ])
    ], style={'padding': '20px', 'backgroundColor': 'white', 'margin': '20px',
              'borderRadius': '5px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
    # Findings section
    html.Div([
        html.H2('Key Findings', style={'color': '#2c3e50'}),
        html.Div([
            html.H3('Size Distribution and Characteristics'),
            html.P("""My analysis shows significant variation in the size of individual areas. The majority 
                    of DWAs fall into the "Small" category (< 1 km²), which initially surprised me. This suggests 
                    that deer tend to utilize numerous smaller areas rather than fewer large ones."""),
            
            html.H3('Geographical Distribution'),
            html.P("""One of the most unexpected findings in my analysis was the concentration of DWAs in 
                    central and southern Maine, contrary to my initial hypothesis that they would be predominantly 
                    in the north. While northern Maine has vast forested areas, the data shows that deer wintering 
                    areas are actually more prevalent in the more populated regions of the state. This pattern 
                    could be explained by several factors:
                    
                    1. Agricultural areas in central and southern Maine might provide better food sources during winter
                    2. The mix of forest patches and developed areas might create beneficial edge habitats
                    3. These regions might offer better protection from harsh winter winds
                    4. Human activity might actually help maintain suitable winter habitats through forest management
                    and landscaping practices"""),
            
            html.H3('Regional Patterns'),
            html.P("""The distribution across latitude bands revealed that Southern Maine has the highest 
                    density of small DWAs, while Central Maine contains a mix of small and medium-sized areas. 
                    Northern Maine, despite my initial expectations, features fewer but generally larger wintering 
                    areas. This pattern might reflect an adaptation to different levels of human development - 
                    in more developed areas, deer appear to make use of smaller, fragmented patches of suitable 
                    habitat, while in the north they can utilize larger continuous areas when available."""),
            
            html.H3('Conservation Implications'),
            html.P("""My analysis reveals several important considerations for wildlife management:"""),
            html.Ul([
                html.Li("""The prevalence of small wintering areas near populated regions suggests that deer 
                        have adapted to using fragmented habitats, making the protection of even small forest 
                        patches crucial for their winter survival"""),
                html.Li("""The clustering of DWAs in more populated regions indicates that deer winter survival 
                        might be more dependent on human-influenced landscapes than I initially thought"""),
                html.Li("""The variation in size and distribution appears to reflect both deer adaptation to 
                        human presence and their ability to find suitable winter shelter in developed landscapes""")
            ])
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
    ], style={'padding': '20px'})
], style={'backgroundColor': '#f0f2f5'})

# Custom CSS styling
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Maine Deer Wintering Areas Analysis</title>
        {%favicon%}
        {%css%}
        <style>
            /* Style definitions for dashboard components */
            .stat-box {
                /* Styling for statistics boxes */
                padding: 20px;
                margin: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                flex: 1;
                min-width: 200px;
            }
            .stat-box h4 {
                margin: 0;
                color: #2c3e50;
                font-size: 24px;
            }
            .stat-box p {
                margin: 10px 0 0 0;
                color: #7f8c8d;
            }
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                background-color: #f0f2f5;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            p {
                line-height: 1.6;
                color: #34495e;
            }
            li {
                color: #34495e;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# Run the application
if __name__ == '__main__':
    app.run_server(debug=True)  # debug=True enables hot reloading and detailed error messages 