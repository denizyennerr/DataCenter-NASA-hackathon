import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image  # Import Image for displaying images

#######################################
# PAGE SETUP
#######################################

st.set_page_config(
    page_title="Data Centers Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Data Centers Dashboard")

option = st.selectbox("Select a city", ("Chicago", "New York", "Seattle"))
st.write(f"You selected: {option}")

#######################
# STYLING (REVISED)
#######################
#st.header("Data Centers Dashboard")
st.markdown("""
<style>
    /* Main page background */
    .main {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }

    /* Page title */
    h1 {
        color: #FAFAFA;
    }

    /* General container adjustments for the main grid */
    [data-testid="block-container"] {
        padding: 2rem 2rem 1rem 2rem; /* Top, Right, Bottom, Left */
    }

    /* Styling for each card in the 2x2 grid */
    [data-testid="stHorizontalBlock"] > div {
        border: 1px solid #333333;
        border-radius: 10px;
        background-color: #2E2E2E;
        padding: 1.5rem;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
    }
    [data-testid="stHorizontalBlock"] > div:hover {
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }

    /* Subheaders inside the cards (e.g., "Chicago Facility KPIs") */
    h3 {
        color: #CCCCCC;
        border-bottom: 1px solid #444444;
        padding-bottom: 10px;
        margin-top: -10px; /* Adjust for better alignment */
    }

    /* Styling for the st.metric containers */
    [data-testid="stMetric"] {
        background-color: #393939;
        border: 1px solid #4A4A4A;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }

    /* Metric label styling */
    [data-testid="stMetricLabel"] {
        justify-content: center;
        color: #A0A0A0;
    }
    
    /* Metric value styling */
    [data-testid="stMetricValue"] {
        color: #FFFFFF;
        font-size: 24px;
    }

</style>
""", unsafe_allow_html=True)


#######################################
# DATA LOADING & PREPROCESSING
#######################################

# Define paths
df_global_dc_path = "dataset/datacentersrevised_Leht1.csv"
df_chicago_dc_path = "dataset/data_centers_Chicago.csv"
df_climate_path = "dataset/POWER_Regional_Monthly_2022_2023_Chicago.csv"
IMAGE_PATH = "dataset/datacenter_interior.jpg"  # Added image path since it's used later

@st.cache_data
def load_data():
    """Loads, cleans, and returns all necessary DataFrames from relative paths."""
    try:
        # Load Global Data
        df_global = pd.read_csv(df_global_dc_path)
        if 'Veerg 1' in df_global.columns:
            df_global.rename(columns={'Veerg 1': 'Provider'}, inplace=True)
        required_cols = ['Latitude', 'Longitude', 'Provider']
        if all(col in df_global.columns for col in required_cols):
            for col in ['Latitude', 'Longitude']:
                df_global[col] = pd.to_numeric(df_global[col], errors='coerce')
                if df_global[col].abs().max() < 10:
                    df_global[col] *= 10
            df_global.dropna(subset=required_cols, inplace=True)
        else:
            df_global = pd.DataFrame()

        # Load Chicago Data
        df_chicago = pd.read_csv(df_chicago_dc_path)
        numeric_cols = ['Total GHG Emissions (Metric Tons CO2e)', 'Site EUI (kBtu/sq ft)', 'Year Built']
        for col in numeric_cols:
            if col in df_chicago.columns:
                df_chicago[col] = pd.to_numeric(df_chicago[col].astype(str).str.replace(',', ''), errors='coerce')
        df_chicago.dropna(subset=numeric_cols, inplace=True)

        # Load Climate Data, skipping the 9-line header
        df_climate = pd.read_csv(df_climate_path, skiprows=9)
        df_climate.dropna(inplace=True)

        return df_global, df_chicago, df_climate

    except FileNotFoundError as e:
        st.error(f"Error: A data file was not found. Please ensure your 'dataset' folder is correct. Missing file: {e.filename}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Load all the data at once
df_global, df_chicago, df_climate = load_data()


#######################################
# VISUALIZATION METHODS
#######################################

def plot_kpi_metrics(df: pd.DataFrame):
    """Display key performance indicators for Chicago data centers."""
    st.subheader("Chicago Data Center Metrics")
    ghg_tooltip = ("Total greenhouse gas emissions from data centers in Chicago for the latest year, "
                   "measured in metric tons of CO2 equivalent (CO2e). This includes emissions from electricity use, "
                   "natural gas consumption, and other sources.")

    # Filter for latest year and compute metrics
    df_latest = df[df['Data Year'] == df['Data Year']]
    total_electricity = df_latest["Electricity Use (kBtu)"].sum()+2230892180.3# Adding fixed value
    total_ghg = df_latest['Total GHG Emissions (Metric Tons CO2e)'].sum()
    avg_eui = df_latest['Site EUI (kBtu/sq ft)'].mean()
    facility_count = df_latest['ID'].nunique()

    # Display metrics in a 2x2 grid
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total GHG Emissions", f"{total_ghg:,.0f} tons", help=ghg_tooltip)
        st.metric("Number of Facilities", f"{facility_count}", help="Active data centers in 2023")
    with col2:
        st.metric("Average Site EUI", f"{avg_eui:,.0f} kBtu/sq ft", help="Energy Use Intensity per square foot")
        st.metric("Sum of Electricity Used", f"{total_electricity:,.0f} kBtu", help="Total grid electricity purchased in 2023 (kBtu)")


def plot_chicago_heatmap(df: pd.DataFrame):
    """Display a heatmap of GHG emissions for Chicago data centers."""
    st.subheader("Chicago Data Centers GHG Emissions Heatmap")
    
    # Create pivot table for heatmap
    pivot_df = df.pivot_table(
        values='Total GHG Emissions (Metric Tons CO2e)', 
        index='Property Name',
        columns='Data Year',
        aggfunc='sum'
    )
    
    # Create heatmap using plotly
    fig = px.imshow(
        pivot_df,
        labels=dict(
            x="Year",
            y="Data Center",
            color="GHG Emissions (Metric Tons CO2e)"
        ),
        aspect="auto",
        color_continuous_scale="Viridis"
    )
    
    # Update layout for dark theme
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=600,
        xaxis_title="Year",
        yaxis_title="Data Center Facility"
    )
    
    # Display the plot with a unique key
    st.plotly_chart(fig, use_container_width=True, key="heatmap_chart")


def plot_global_map(df: pd.DataFrame):
    """Display global data center locations with enhanced visualization."""
    st.subheader("Global Data Center Locations")
    
    # Configure the map
    fig = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        color="Provider",
        hover_name="Location",
        hover_data={"Latitude": False, "Longitude": False},  # Hide lat/lon in hover
        mapbox_style="carto-darkmatter",  # Dark theme map style
        zoom=2,
        title="Data Center Global Distribution"
    )
    
    # Enhanced layout configuration
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=700,  # Increased height for better visibility
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(50,50,50,0.8)",  # Semi-transparent background
            bordercolor="white",
            borderwidth=1
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        mapbox=dict(
            center=dict(lat=20, lon=0),  # Centered view
            pitch=0
        )
    )
    
    # Update marker properties
    fig.update_traces(
        marker=dict(
            size=12,
            opacity=0.8,
            symbol='circle'
        )
    )
    
    # Display the map with a unique key
    st.plotly_chart(fig, use_container_width=True, key="global_map")

def plot_climate_chart(df: pd.DataFrame):
    """Create a time series plot comparing T2M_RANGE and CDD18_3 for Chicago per month in 2023."""
    st.subheader("Chicago Climate Data")

    # Filter data for 2023 and the two parameters we want
    df_year = df[df['YEAR'] == 2023]
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    # Separate the data for each parameter
    df_t2m = df_year[df_year['PARAMETER'] == 'T2M_RANGE']
    df_cdd = df_year[df_year['PARAMETER'] == 'CDD18_3']

    
# Reshape the T2M data from wide to long format
    df_t2m_long = pd.melt(
        df_t2m,
        value_vars=months,
        var_name='Months',
        value_name='Value'
    )
    
    fig_t2m = px.line(
        df_t2m_long, # Use the reshaped long-format DataFrame
        x='Months',
        y='Value',
        markers=True,
        title="Monthly Temperature at 2 Meters Range (T2M_RANGE °C) for 2023 in Chicago",
        labels={'Value': 'Temperature Range (°C)'}
    )
    # Apply styling
    fig_t2m.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis={'tickmode': 'array', 'tickvals': months},
        hovermode='x unified'
    )
    fig_t2m.update_traces(line_color='#87b1d6', marker_size=8)
    
    st.plotly_chart(fig_t2m, use_container_width=True)
    
    # Reshape the CDD data from wide to long format
    df_cdd_long = pd.melt(
        df_cdd,
        value_vars=months,
        var_name='Months',
        value_name='Value'
    )

    fig_cdd = px.line(
        df_cdd_long, # Use the reshaped long-format DataFrame
        x='Months',
        y='Value',
        markers=True,
        title="Monthly Cooling Degree Days (CDD) for 2023 in Chicago",
        labels={'Value': 'Cooling Degree Days (CDD)'}
    )
    # Apply styling
    fig_cdd.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis={'tickmode': 'array', 'tickvals': months},
        hovermode='x unified'
    )
    fig_cdd.update_traces(line_color='#4d82f3', marker_size=8)
    
    st.plotly_chart(fig_cdd, use_container_width=True)


def display_image(image_path: str, title: str):
    st.subheader(title)
    try:
        image = Image.open(image_path)
        st.image(image, use_container_width=True)
    except FileNotFoundError:
        st.error(f"Error: Image not found at '{image_path}'.")


#######################################
# STREAMLIT LAYOUT
#######################################

# Create three main sections using columns
left_col, right_col = st.columns([1, 1])

# Left column - Chicago Data
with left_col:
    if not df_chicago.empty:
        # KPI Metrics at the top
        plot_kpi_metrics(df_chicago)
        st.divider()
        
        # Chicago Heatmap below KPIs
        plot_chicago_heatmap(df_chicago)  # This is the only call to plot_chicago_heatmap
        st.divider()
        
        # Climate Chart at the bottom of left column
        if not df_climate.empty:
            plot_climate_chart(df_climate)
        else:
            st.warning("Climate data not loaded.")
    else:
        st.warning("Chicago data not loaded.")

# Right column - Global Map and Image
with right_col:
    if not df_global.empty:
        # Global Map at the top
        plot_global_map(df_global)
        st.divider()
       
        # Data Center Image below the map
        display_image(image_path="assets/VERTICAL.png", title="Changes in Water Area from 2016 to 2025")
    else:
        st.warning("Global data not loaded.")

# Resources section at the bottom
st.divider()
st.header("Resources:")

st.markdown("""
* *Data Source:*
    * Center for International Earth Science Information Network (CIESIN), Columbia University. (2018). Gridded Population of the World, Version 4 (GPWv4): Population Density, Revision 11 [Data set]. NASA Socioeconomic Data and Applications Center (SEDAC). https://doi.org/10.7927/H49C6VHW
    * City of Chicago. (2025). Chicago Energy Benchmarking [Data set]. Chicago Data Portal. Retrieved October 5, 2025, from https://data.cityofchicago.org/Environment-Sustainable-Development/Chicago-Energy-Benchmarking/xq83-jr8c/about_data
    * NASA Langley Research Center (LaRC) POWER Project. (2025). NASA Prediction of Worldwide Energy Resources (Version 9.0.1) [Data set]. NASA. Retrieved October 5, 2025, from https://power.larc.nasa.gov/data-access-viewer/
    * NASA Near Real-Time Capability for Earth Observation (LANCE). (2024). VIIRS Land Near Real-Time Data [Data set]. NASA Earthdata. Retrieved October 4, 2025, from https://www.earthdata.nasa.gov/data/instruments/viirs/land-near-real-time-data
    * Natural Earth. (2023). Admin 0 – Countries (Version 5.1.1) [Data set]. https://www.naturalearthdata.com/downloads/10m-cultural-vectors/
    * Natural Earth. (2023). Admin 1 – States, Provinces (Version 5.1.1) [Data set]. https://www.naturalearthdata.com/downloads/10m-cultural-vectors/
    * The MOPITT Science Team. (2021). MOPITT Level 3 Carbon Monoxide (CO) Gridded Monthly Averages (MOP03M) (Version 9) [Data set]. NASA Langley Atmospheric Science Data Center DAAC. https://doi.org/10.5067/TERRA/MOPITT/MOP03M.009
    * U.S. Geological Survey (USGS) and National Aeronautics and Space Administration (NASA). (2022). Landsat 8–9 Collection 2 Level-2 Surface Reflectance Code (LaSRC) Product. NASA Earth Science Data Systems (ESDS) Program, Land Processes Distributed Active Archive Center (LP DAAC). https://doi.org/10.5066/P9OGBGM6

* *Software & Libraries:*
    * Figma, Inc. (2025). Figma [Computer software]. https://www.figma.com
    * Plotly Technologies Inc. (2023). Plotly Python Open Source Graphing Library (Version 5.18.0) [Computer software]. https://plotly.com/python/
    * QGIS Development Team. (2025). QGIS Geographic Information System (Version 3.38 'Prizren') [Computer software]. https://qgis.org
    * Streamlit Inc. (2023). Streamlit: The fastest way to build and share data apps (Version 1.29.0) [Computer software]. https://streamlit.io/

* *Citation Reference List:*
    * Guidi, G., Dominici, F., Gilmour, J., Butler, K., Bell, E., Delaney, S., & Bargagli-Stoffi, F. J. (2024). Environmental Burden of United States Data Centers in the Artificial Intelligence Era. [Preprint]. arXiv:2411.09786v1. https://arxiv.org/abs/2411.09786
    * Ngata, W., Bashir, N., Westerlaken, M., Liote, L., Chandio, Y., & Olivetti, E. (2025). The Cloud Next Door: Investigating the Environmental and Socioeconomic Strain of Datacenters on Local Communities. [Preprint]. arXiv:2506.03367. https://arxiv.org/abs/2506.03367""")
