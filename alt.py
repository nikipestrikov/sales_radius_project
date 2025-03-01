import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import plugins
from geopy.distance import geodesic
from datetime import datetime
import numpy as np

# Set page config
st.set_page_config(
    page_title="Sales Map Visualizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = None
if 'show_filtered' not in st.session_state:
    st.session_state.show_filtered = False
if 'show_all' not in st.session_state:
    st.session_state.show_all = False


@st.cache_data
def process_csv(uploaded_file):
    """Process and cache the CSV data"""
    try:
        df = pd.read_csv(uploaded_file)

        # Check if Latitude/Longitude columns exist, if not try to parse from first column
        if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
            coords = df.iloc[:, 0].str.strip('"').str.split(',', expand=True)
            df['Latitude'] = coords[0].astype(np.float32)
            df['Longitude'] = coords[1].astype(np.float32)
        else:
            # Convert to more efficient datatypes
            df['Latitude'] = df['Latitude'].astype(np.float32)
            df['Longitude'] = df['Longitude'].astype(np.float32)

        return df
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None


@st.cache_data
def filter_data_vectorized(df, center_lat, center_lon, radius):
    """Filter data points within radius using vectorized operations"""

    def calculate_distances(lat, lon):
        return geodesic((center_lat, center_lon), (lat, lon)).meters

    distances = df.apply(lambda row: calculate_distances(
        row['Latitude'], row['Longitude']), axis=1)
    return df[distances <= radius]


@st.cache_data
def limit_points(df, max_points=1000):
    """Limit the number of points to display if dataset is too large"""
    if len(df) > max_points:
        return df.sample(max_points)
    return df


def create_map(df, center_lat=None, center_lon=None, radius=None, max_points=1000):
    """Create an interactive map with clustered markers"""
    # Limit points for better performance
    df = limit_points(df, max_points)

    # Use mean coordinates if no center provided
    if center_lat is None:
        center_lat = df['Latitude'].mean()
    if center_lon is None:
        center_lon = df['Longitude'].mean()

    # Create the map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # Create a MarkerCluster for better performance
    marker_cluster = plugins.MarkerCluster().add_to(m)

    # Add points to the cluster
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=5,
            popup=f"Sale Amount: {row['COS Amount']}<br>District: {row['District(Name)']}",
            color='blue',
            fill=True,
            fill_opacity=0.6
        ).add_to(marker_cluster)

    if radius:
        # Add center point
        folium.CircleMarker(
            location=[center_lat, center_lon],
            radius=8,
            color='red',
            popup='Center Point',
            fill=True
        ).add_to(m)

        # Add radius circle
        folium.Circle(
            location=[center_lat, center_lon],
            radius=radius,
            color='red',
            fill=False
        ).add_to(m)

    # Add controls
    m.add_child(folium.plugins.MeasureControl())
    m.add_child(folium.LatLngPopup())
    m.add_child(folium.plugins.Fullscreen())

    return m


def handle_filter_submit():
    st.session_state.show_filtered = True
    st.session_state.show_all = False


def handle_show_all():
    st.session_state.show_filtered = False
    st.session_state.show_all = True


def main():
    st.title("Sales Map Visualizer")

    # File uploader widget outside cached function
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        # Process the uploaded file
        df = process_csv(uploaded_file)

        if df is not None:
            # Create two columns for the layout
            col1, col2 = st.columns([2, 1])

            with col2:
                st.subheader("Filter Options")

                # Input fields outside form for better state management
                center_lat = st.number_input(
                    "Latitude",
                    value=float(df['Latitude'].mean()),
                    format="%.6f",
                    key="center_lat"
                )
                center_lon = st.number_input(
                    "Longitude",
                    value=float(df['Longitude'].mean()),
                    format="%.6f",
                    key="center_lon"
                )
                radius = st.number_input(
                    "Radius (meters)",
                    value=1000,
                    min_value=100,
                    step=100,
                    key="radius"
                )
                max_points = st.number_input(
                    "Max points to display",
                    value=1000,
                    min_value=100,
                    max_value=5000,
                    step=100,
                    key="max_points"
                )

                # Buttons for actions
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Apply Filter", on_click=handle_filter_submit):
                        pass
                with col_btn2:
                    if st.button("Show All", on_click=handle_show_all):
                        pass

                # Display data statistics
                st.subheader("Dataset Statistics")
                st.write(f"Total records: {len(df)}")

            # Handle map display based on state
            with col1:
                st.subheader("Sales Map")

                if st.session_state.show_filtered:
                    filtered_df = filter_data_vectorized(df, center_lat, center_lon, radius)
                    st.session_state.filtered_data = filtered_df
                    st.write(f"Points within radius: {len(filtered_df)}")

                    # Download button for filtered data
                    if len(filtered_df) > 0:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        csv = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="Download filtered data as CSV",
                            data=csv,
                            file_name=f"filtered_sales_{timestamp}.csv",
                            mime="text/csv"
                        )

                    m = create_map(filtered_df, center_lat, center_lon, radius, max_points)
                    st_folium(m, width=800)

                elif st.session_state.show_all:
                    m = create_map(df, max_points=max_points)
                    st_folium(m, width=800)

                else:
                    # Initial map
                    m = create_map(df, max_points=max_points)
                    st_folium(m, width=800)


if __name__ == "__main__":
    main()
