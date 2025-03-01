import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import plugins
from geopy.distance import geodesic
from datetime import datetime
import os


def load_data():
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            # Check if Latitude/Longitude columns exist, if not try to parse from first column
            if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
                coords = df.iloc[:, 0].str.strip('"').str.split(',', expand=True)
                df['Latitude'] = coords[0].astype(float)
                df['Longitude'] = coords[1].astype(float)

            return df
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            return None
    return None


def create_map(df, center_lat=None, center_lon=None, radius=None):
    # Use mean coordinates if no center provided
    if center_lat is None:
        center_lat = df['Latitude'].mean()
    if center_lon is None:
        center_lon = df['Longitude'].mean()

    # Create the map
    m = folium.Map(location=[center_lat, center_lon],
                   zoom_start=12,
                   tiles='OpenStreetMap')

    # Add all points
    for idx, row in df.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=5,
            popup=f"Sale Amount: {row['COS Amount']}<br>District: {row['District(Name)']}",
            color='blue',
            fill=True,
            fill_opacity=0.6
        ).add_to(m)

    # If radius is provided, add circle and center marker
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

    # Add measurement tools
    m.add_child(folium.plugins.MeasureControl())
    m.add_child(folium.LatLngPopup())

    return m


def filter_data(df, center_lat, center_lon, radius):
    center_point = (center_lat, center_lon)
    filtered_rows = []

    for idx, row in df.iterrows():
        point = (row['Latitude'], row['Longitude'])
        distance = geodesic(center_point, point).meters
        if distance <= radius:
            filtered_rows.append(row)

    return pd.DataFrame(filtered_rows)


def main():
    st.title("Sales Map Visualizer")

    # Load data
    df = load_data()

    if df is not None:
        # Create two columns for the layout
        col1, col2 = st.columns([2, 1])

        with col2:
            st.subheader("Filter Options")
            # Input fields
            center_lat = st.number_input("Latitude",
                                         value=float(df['Latitude'].mean()),
                                         format="%.6f")
            center_lon = st.number_input("Longitude",
                                         value=float(df['Longitude'].mean()),
                                         format="%.6f")
            radius = st.number_input("Radius (meters)",
                                     value=1000,
                                     min_value=100,
                                     step=100)

            filter_button = st.button("Apply Filter")
            show_all = st.button("Show All Points")

            if filter_button:
                filtered_df = filter_data(df, center_lat, center_lon, radius)
                st.write(f"Found {len(filtered_df)} sales within radius")

                # Create download buttons for filtered data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # CSV download
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download filtered data as CSV",
                    data=csv,
                    file_name=f"filtered_sales_{timestamp}.csv",
                    mime="text/csv"
                )

                # Display the filtered map
                with col1:
                    st.subheader("Sales Map")
                    m = create_map(filtered_df, center_lat, center_lon, radius)
                    st_folium(m, width=800)

            elif show_all:
                with col1:
                    st.subheader("Sales Map")
                    m = create_map(df)
                    st_folium(m, width=800)

        # Show initial map if no button is pressed
        if not filter_button and not show_all:
            with col1:
                st.subheader("Sales Map")
                m = create_map(df)
                st_folium(m, width=800)


if __name__ == "__main__":
    main()
