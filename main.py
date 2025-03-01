import pandas as pd
import folium
from folium import plugins
from geopy.distance import geodesic
import tkinter as tk
from tkinter import ttk
import webbrowser
import os
from datetime import datetime


import pandas as pd
import folium
from folium import plugins
from geopy.distance import geodesic
import tkinter as tk
from tkinter import ttk, messagebox, filedialog  # Added messagebox and filedialog
import webbrowser
import os
from datetime import datetime


class SalesMapApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Map Filter")

        # Ask user to select the CSV file first
        self.select_file()

        if hasattr(self, 'df'):  # Only proceed if data was loaded successfully
            # Calculate initial center
            self.center_lat = self.df['Latitude'].mean()
            self.center_lon = self.df['Longitude'].mean()

            # Create initial map
            self.create_base_map()

            # Set up the GUI
            self.setup_gui()
        else:
            self.root.quit()

    def select_file(self):
        """Let user select the CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select your CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.df = pd.read_csv(file_path)

                # Check if we need to parse coordinates
                if 'Latitude' not in self.df.columns or 'Longitude' not in self.df.columns:
                    # Attempt to split coordinates from first column
                    coords = self.df.iloc[:, 0].str.strip('"').str.split(',', expand=True)
                    self.df['Latitude'] = coords[0].astype(float)
                    self.df['Longitude'] = coords[1].astype(float)

                # Verify required columns exist
                required_columns = ['Latitude', 'Longitude', 'COS Amount', 'District(Name)']
                missing_columns = [col for col in required_columns if col not in self.df.columns]

                if missing_columns:
                    raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file:\n{str(e)}")
                return
        else:
            messagebox.showerror("Error", "No file selected. Application will close.")
            return

    def create_base_map(self):
        """Create and save the initial map with all points"""
        m = folium.Map(location=[self.center_lat, self.center_lon],
                       zoom_start=10,
                       tiles='OpenStreetMap')

        # Add markers for all points
        for idx, row in self.df.iterrows():
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=5,
                popup=f"Sale Amount: {row['COS Amount']}<br>District: {row['District(Name)']}",
                color='blue',
                fill=True,
                fill_opacity=0.6
            ).add_to(m)

        # Add click event functionality to show coordinates
        m.add_child(folium.LatLngPopup())

        # Add a measure tool
        m.add_child(folium.plugins.MeasureControl())

        # Save the map
        self.base_map_path = "all_sales_map.html"
        m.save(self.base_map_path)

    def setup_gui(self):
        # Create and pack widgets
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Labels and entries for coordinates and radius
        ttk.Label(frame, text="Latitude:").grid(row=0, column=0, sticky=tk.W)
        self.lat_var = tk.StringVar(value=str(self.center_lat))
        self.lat_entry = ttk.Entry(frame, textvariable=self.lat_var)
        self.lat_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Longitude:").grid(row=1, column=0, sticky=tk.W)
        self.lon_var = tk.StringVar(value=str(self.center_lon))
        self.lon_entry = ttk.Entry(frame, textvariable=self.lon_var)
        self.lon_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Radius (meters):").grid(row=2, column=0, sticky=tk.W)
        self.radius_var = tk.StringVar(value="1000")
        self.radius_entry = ttk.Entry(frame, textvariable=self.radius_var)
        self.radius_entry.grid(row=2, column=1, padx=5, pady=5)

        # Buttons
        ttk.Button(frame, text="Show All Sales",
                   command=self.show_base_map).grid(row=3, column=0, pady=10)

        ttk.Button(frame, text="Filter Sales",
                   command=self.filter_sales).grid(row=3, column=1, pady=10)

    def filter_sales(self):
        """Filter sales and create new map based on inputs"""
        try:
            center_lat = float(self.lat_var.get())
            center_lon = float(self.lon_var.get())
            radius_meters = float(self.radius_var.get())

            # Filter the data
            center_point = (center_lat, center_lon)
            filtered_rows = []

            for idx, row in self.df.iterrows():
                point = (row['Latitude'], row['Longitude'])
                distance = geodesic(center_point, point).meters
                if distance <= radius_meters:
                    filtered_rows.append(row)

            filtered_df = pd.DataFrame(filtered_rows)

            if len(filtered_df) > 0:
                # Create new map with filtered results
                m_filtered = folium.Map(location=[center_lat, center_lon],
                                        zoom_start=13)

                # Add center point
                folium.CircleMarker(
                    location=[center_lat, center_lon],
                    radius=8,
                    color='red',
                    popup='Center Point',
                    fill=True
                ).add_to(m_filtered)

                # Add radius circle
                folium.Circle(
                    location=[center_lat, center_lon],
                    radius=radius_meters,
                    color='red',
                    fill=False
                ).add_to(m_filtered)

                # Add filtered points
                for idx, row in filtered_df.iterrows():
                    folium.CircleMarker(
                        location=[row['Latitude'], row['Longitude']],
                        radius=5,
                        popup=f"Sale Amount: {row['COS Amount']}<br>District: {row['District(Name)']}",
                        color='blue',
                        fill=True
                    ).add_to(m_filtered)

                # Save filtered results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                map_filename = f"filtered_map_{timestamp}.html"
                csv_filename = f"filtered_sales_{timestamp}.csv"

                m_filtered.save(map_filename)
                filtered_df.to_csv(csv_filename, index=False)

                # Open the map in browser
                webbrowser.open(f'file://{os.path.abspath(map_filename)}')

                # Show success message
                tk.messagebox.showinfo(
                    "Success",
                    f"Found {len(filtered_df)} sales within radius.\n"
                    f"Results saved to {csv_filename}\n"
                    f"Map saved to {map_filename}"
                )
            else:
                tk.messagebox.showinfo("No Results", "No sales found within the specified radius")

        except ValueError as e:
            tk.messagebox.showerror("Error", "Please enter valid numbers for latitude, longitude, and radius")
        except Exception as e:
            tk.messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def show_base_map(self):
        """Open the base map in the default web browser"""
        webbrowser.open(f'file://{os.path.abspath(self.base_map_path)}')


def main():
    root = tk.Tk()
    app = SalesMapApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()

