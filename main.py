import tkinter as tk
from tkinter import messagebox
import requests
import os
import networkx as nx
import math
import webbrowser
import tempfile
import threading
from geopy.distance import geodesic
import folium
from folium.plugins import MarkerCluster, AntPath, Fullscreen
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import customtkinter as ctk


# Set appearance mode and default color theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AdvancedPathfinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced 3D Postal Code Pathfinder")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1E1E1E")
        
        self.api_key = "7c3f4be1896c4bcaa483defd4a3c4f6e"  # Geoapify API key
        self.locations = []
        self.paths = []
        self.current_path = []
        self.animation_running = False
        self.animation_speed = 50  # milliseconds
        
        # Available algorithms
        self.algorithms = {
            "Shortest Path (TSP)": self.find_shortest_path,
            "Euler Path": self.find_euler_path,
            "A* Path": self.find_astar_path,
            "Dijkstra's Path": self.find_dijkstra_path,
            "Minimum Spanning Tree": self.find_mst_path
        }
        
        # Airplane as the only transport mode
        self.transport_mode = "airplane"
        self.airplane_speed = 800  # km/h for commercial airplane
        
        self.setup_ui()
        self.create_3d_plot()
        
    def setup_ui(self):
        # Create main frames
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create header with title and logo
        self.header_frame = ctk.CTkFrame(self.main_frame, height=60)
        self.header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Title with animation effect
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="Advanced 3D Postal Code Pathfinder",
            font=("Roboto", 24, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Content area (split into left and right panes)
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel (input controls)
        self.left_panel = ctk.CTkFrame(self.content_frame, width=400)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        # Right panel (visualization)
        self.right_panel = ctk.CTkFrame(self.content_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Setup left panel components
        self.setup_input_panel()
        
        # Setup right panel components
        self.setup_visualization_panel()
        
        # Status bar
        self.status_frame = ctk.CTkFrame(self.main_frame, height=30)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            textvariable=self.status_var,
            anchor="w"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
        self.progress_bar.set(0)
        
    def setup_input_panel(self):
        # Input section
        self.input_frame = ctk.CTkFrame(self.left_panel)
        self.input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Location entry
        ctk.CTkLabel(self.input_frame, text="Postal Code:").pack(anchor=tk.W, padx=5, pady=2)
        self.postal_code_entry = ctk.CTkEntry(self.input_frame, width=380)
        self.postal_code_entry.pack(fill=tk.X, padx=5, pady=5)
        
        ctk.CTkLabel(self.input_frame, text="Location Name:").pack(anchor=tk.W, padx=5, pady=2)
        self.location_name_entry = ctk.CTkEntry(self.input_frame, width=380)
        self.location_name_entry.pack(fill=tk.X, padx=5, pady=5)
        
        # Add location button
        self.add_btn = ctk.CTkButton(
            self.input_frame, 
            text="Add Location",
            command=self.add_location
        )
        self.add_btn.pack(fill=tk.X, padx=5, pady=10)
        
        # Locations list
        self.locations_frame = ctk.CTkFrame(self.left_panel)
        self.locations_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.locations_frame, text="Added Locations:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.locations_list = tk.Listbox(
            self.locations_frame,
            bg="#2B2B2B",
            fg="#FFFFFF",
            selectbackground="#3B8ED0",
            selectforeground="#FFFFFF",
            font=("Roboto", 10),
            height=10
        )
        self.locations_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons for managing locations
        self.list_buttons_frame = ctk.CTkFrame(self.locations_frame)
        self.list_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.remove_btn = ctk.CTkButton(
            self.list_buttons_frame,
            text="Remove Selected",
            command=self.remove_location
        )
        self.remove_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.clear_btn = ctk.CTkButton(
            self.list_buttons_frame,
            text="Clear All",
            command=self.clear_all
        )
        self.clear_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # Algorithm selection
        self.algorithm_frame = ctk.CTkFrame(self.left_panel)
        self.algorithm_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ctk.CTkLabel(self.algorithm_frame, text="Path Finding Algorithm:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.algorithm_var = tk.StringVar()
        self.algorithm_var.set(list(self.algorithms.keys())[0])
        self.algorithm_dropdown = ctk.CTkOptionMenu(
            self.algorithm_frame,
            variable=self.algorithm_var,
            values=list(self.algorithms.keys())
        )
        self.algorithm_dropdown.pack(fill=tk.X, padx=5, pady=5)
        
        # Transport mode info (airplane only)
        ctk.CTkLabel(self.algorithm_frame, text="Transport Mode: Airplane (800 km/h)", font=("Roboto", 12)).pack(anchor=tk.W, padx=5, pady=10)
        
        # Calculate button
        self.calculate_btn = ctk.CTkButton(
            self.algorithm_frame,
            text="Calculate Path",
            command=self.calculate_path,
            height=40,
            font=("Roboto", 14, "bold")
        )
        self.calculate_btn.pack(fill=tk.X, padx=5, pady=10)
        
        # Animation control
        self.animation_frame = ctk.CTkFrame(self.left_panel)
        self.animation_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ctk.CTkLabel(self.animation_frame, text="Animation Speed:").pack(anchor=tk.W, padx=5, pady=2)
        
        self.speed_slider = ctk.CTkSlider(
            self.animation_frame,
            from_=10,
            to=200,
            command=self.update_animation_speed
        )
        self.speed_slider.set(self.animation_speed)
        self.speed_slider.pack(fill=tk.X, padx=5, pady=5)
        
        self.animation_buttons_frame = ctk.CTkFrame(self.animation_frame)
        self.animation_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.play_btn = ctk.CTkButton(
            self.animation_buttons_frame,
            text="Play Animation",
            command=self.start_animation
        )
        self.play_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.stop_btn = ctk.CTkButton(
            self.animation_buttons_frame,
            text="Stop Animation",
            command=self.stop_animation
        )
        self.stop_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
    def setup_visualization_panel(self):
        # Tab view for different visualizations
        self.tab_view = ctk.CTkTabview(self.right_panel)
        self.tab_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.tab_view.add("3D Visualization")
        self.tab_view.add("Map View")
        self.tab_view.add("Directions")
        self.tab_view.add("Statistics")
        
        # 3D Visualization tab
        self.visualization_frame = ctk.CTkFrame(self.tab_view.tab("3D Visualization"))
        self.visualization_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Map View tab
        self.map_frame = ctk.CTkFrame(self.tab_view.tab("Map View"))
        self.map_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.map_view_label = ctk.CTkLabel(self.map_frame, text="Map will be displayed here")
        self.map_view_label.pack(padx=10, pady=10)
        
        self.open_map_btn = ctk.CTkButton(
            self.map_frame,
            text="Open Map in Browser",
            command=self.open_map_in_browser
        )
        self.open_map_btn.pack(pady=10)
        
        # Directions tab
        self.directions_frame = ctk.CTkFrame(self.tab_view.tab("Directions"))
        self.directions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.directions_text = tk.Text(
            self.directions_frame,
            bg="#2B2B2B",
            fg="#FFFFFF",
            font=("Roboto", 10),
            wrap=tk.WORD
        )
        self.directions_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Statistics tab
        self.stats_frame = ctk.CTkFrame(self.tab_view.tab("Statistics"))
        self.stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.stats_canvas = tk.Canvas(
            self.stats_frame,
            bg="#2B2B2B",
            highlightthickness=0
        )
        self.stats_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def create_3d_plot(self):
        """Create an interactive 3D plot for visualization"""
        # Create a figure for the 3D plot
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor='#2B2B2B')
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#2B2B2B')
        
        # Style the plot
        self.ax.set_xlabel('Longitude', color='white')
        self.ax.set_ylabel('Latitude', color='white')
        self.ax.set_zlabel('Elevation', color='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.zaxis.label.set_color('white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.tick_params(axis='z', colors='white')
        
        # Set title
        self.ax.set_title('3D Path Visualization', color='white')
        
        # For grid
        self.ax.grid(True, alpha=0.3)
        
        # Create the canvas for drawing the plot
        self.canvas = FigureCanvasTkAgg(self.fig, self.visualization_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def add_location(self):
        """Add a location to the list"""
        postal_code = self.postal_code_entry.get().strip()
        location_name = self.location_name_entry.get().strip()
        
        if not postal_code:
            self.show_error("Error", "Please enter a postal code")
            return
        
        # Default name if not provided
        if not location_name:
            location_name = f"Location {len(self.locations) + 1}"
        
        # Get coordinates from API
        try:
            self.status_var.set("Fetching coordinates...")
            self.progress_bar.set(0.3)
            self.root.update()
            
            coordinates = self.get_coordinates(postal_code)
            
            self.progress_bar.set(0.6)
            self.root.update()
            
            if not coordinates:
                self.show_error("Error", f"Could not find coordinates for postal code: {postal_code}")
                self.status_var.set("Ready")
                self.progress_bar.set(0)
                return
            
            # Add elevation data for 3D visualization (simulated)
            elevation = self.get_elevation(coordinates[0], coordinates[1])
            
            location_info = {
                "name": location_name,
                "postal_code": postal_code,
                "lat": coordinates[0],
                "lng": coordinates[1],
                "elevation": elevation
            }
            
            self.locations.append(location_info)
            self.locations_list.insert(tk.END, f"{location_name} ({postal_code})")
            
            # Update 3D plot
            self.update_3d_plot()
            
            # Clear entries
            self.postal_code_entry.delete(0, tk.END)
            self.location_name_entry.delete(0, tk.END)
            self.status_var.set(f"Added location: {location_name}")
            self.progress_bar.set(1)
            
            # Reset progress bar after a delay
            self.root.after(1000, lambda: self.progress_bar.set(0))
            
        except Exception as e:
            self.show_error("Error", f"Error adding location: {str(e)}")
            self.status_var.set("Error occurred")
            self.progress_bar.set(0)
            
    def get_coordinates(self, postal_code):
        """Get coordinates from postal code using Geoapify API"""
        url = "https://api.geoapify.com/v1/geocode/search"
        params = {
            "text": postal_code,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data["features"] and len(data["features"]) > 0:
                    feature = data["features"][0]
                    lng, lat = feature["geometry"]["coordinates"]
                    return (lat, lng)
            
            return None
        except Exception as e:
            self.show_error("API Error", f"Error connecting to Geoapify API: {str(e)}")
            return None
            
    def get_elevation(self, lat, lng):
        """Get or simulate elevation data"""
        # In a real application, you would call an elevation API
        # For this example, we'll simulate elevation data
        base_elevation = 100  # Base elevation in meters
        random_factor = random.uniform(-50, 50)  # Add some randomness
        
        # Use location coordinates to create some variation
        lat_factor = (lat % 1) * 100
        lng_factor = (lng % 1) * 100
        
        elevation = base_elevation + random_factor + lat_factor + lng_factor
        return max(0, elevation)  # Ensure elevation is not negative
        
    def remove_location(self):
        """Remove selected location"""
        selected = self.locations_list.curselection()
        if not selected:
            return
            
        index = selected[0]
        self.locations.pop(index)
        self.locations_list.delete(index)
        
        # Update 3D plot
        self.update_3d_plot()
        self.status_var.set("Location removed")
        
    def clear_all(self):
        """Clear all locations"""
        self.locations = []
        self.locations_list.delete(0, tk.END)
        
        # Clear the 3D plot
        self.update_3d_plot()
        self.status_var.set("All locations cleared")
        
    def update_3d_plot(self):
        """Update the 3D plot with current locations"""
        self.ax.clear()
        
        # Style the plot
        self.ax.set_facecolor('#2B2B2B')
        self.ax.set_xlabel('Longitude', color='white')
        self.ax.set_ylabel('Latitude', color='white')
        self.ax.set_zlabel('Elevation (m)', color='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.zaxis.label.set_color('white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.tick_params(axis='z', colors='white')
        
        if not self.locations:
            self.ax.set_title('No locations added yet', color='white')
            self.canvas.draw()
            return
            
        # Add points for each location
        xs = [loc["lng"] for loc in self.locations]
        ys = [loc["lat"] for loc in self.locations]
        zs = [loc["elevation"] for loc in self.locations]
        
        # Plot the points
        self.ax.scatter(xs, ys, zs, color='yellow', s=100, marker='o', edgecolor='black')
        
        # Add labels for each point
        for i, loc in enumerate(self.locations):
            self.ax.text(loc["lng"], loc["lat"], loc["elevation"], f"{i+1}. {loc['name']}", color='white')
            
        # If we have a path, draw it
        if hasattr(self, 'current_path') and self.current_path:
            path_xs = [self.locations[i]["lng"] for i in self.current_path]
            path_ys = [self.locations[i]["lat"] for i in self.current_path]
            path_zs = [self.locations[i]["elevation"] for i in self.current_path]
            
            self.ax.plot(path_xs, path_ys, path_zs, 'r-', linewidth=2, alpha=0.7)
            
        # Set the title
        self.ax.set_title('3D Path Visualization', color='white')
        
        # Update the limits to fit all points
        if xs:
            self.ax.set_xlim(min(xs) - 0.01, max(xs) + 0.01)
            self.ax.set_ylim(min(ys) - 0.01, max(ys) + 0.01)
            self.ax.set_zlim(min(zs) - 10, max(zs) + 10)
            
        # Redraw the canvas
        self.canvas.draw()
        
    def calculate_path(self):
        """Calculate path based on selected algorithm"""
        if len(self.locations) < 2:
            self.show_error("Error", "Please add at least two locations")
            return
            
        # Get the selected algorithm
        algorithm_name = self.algorithm_var.get()
        algorithm_func = self.algorithms[algorithm_name]
        
        # Run the algorithm
        self.status_var.set(f"Calculating {algorithm_name}...")
        self.progress_bar.set(0.2)
        self.root.update()
        
        try:
            # Run algorithm in a separate thread
            thread = threading.Thread(target=self.run_algorithm, args=(algorithm_func,))
            thread.start()
            
        except Exception as e:
            self.show_error("Error", f"Error calculating path: {str(e)}")
            self.status_var.set("Error occurred")
            self.progress_bar.set(0)
            
    def run_algorithm(self, algorithm_func):
        """Run the selected algorithm in a separate thread"""
        try:
            algorithm_func()
            
            # Update the UI
            self.root.after(0, lambda: self.progress_bar.set(1))
            self.root.after(0, lambda: self.status_var.set("Path calculated successfully"))
            
            # Reset progress bar after a delay
            self.root.after(1000, lambda: self.progress_bar.set(0))
            
        except Exception as e:
            error_msg = str(e)  # Capture the error message
            self.root.after(0, lambda: self.show_error("Algorithm Error", f"Error in algorithm: {error_msg}"))
            self.root.after(0, lambda: self.status_var.set("Error in algorithm"))
            self.root.after(0, lambda: self.progress_bar.set(0))
            
    def find_shortest_path(self):
        """Find shortest path using TSP algorithm"""
        # Create a graph
        G = nx.Graph()
        
        # Add nodes
        for i, loc in enumerate(self.locations):
            G.add_node(i, pos=(loc["lat"], loc["lng"]), name=loc["name"])
        
        # Add edges with distances
        for i in range(len(self.locations)):
            for j in range(i+1, len(self.locations)):
                loc1 = self.locations[i]
                loc2 = self.locations[j]
                dist = geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers
                G.add_edge(i, j, weight=dist)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.4))
        
        # Solve TSP
        path = self.solve_tsp(G)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.7))
        
        # Update the current path
        self.current_path = path
        
        # Update the visualization
        self.root.after(0, self.update_3d_plot)
        self.root.after(0, self.update_map_view)
        self.root.after(0, self.update_directions)
        self.root.after(0, self.update_statistics)
            
    def find_euler_path(self):
        """Find Euler path"""
        # Create a graph
        G = nx.Graph()
        
        # Add nodes
        for i, loc in enumerate(self.locations):
            G.add_node(i, pos=(loc["lat"], loc["lng"]), name=loc["name"])
        
        # Add edges with distances
        for i in range(len(self.locations)):
            for j in range(i+1, len(self.locations)):
                loc1 = self.locations[i]
                loc2 = self.locations[j]
                dist = geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers
                G.add_edge(i, j, weight=dist)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.4))
        
        # Check if Euler path exists
        odd_degree_nodes = [n for n, d in G.degree() if d % 2 == 1]
        
        if len(odd_degree_nodes) > 2:
            self.root.after(0, lambda: self.show_info("Information", 
                           "This graph does not have an Euler path. Adding necessary edges to make it possible."))
            # Add edges to make the graph Eulerian
            self.make_graph_eulerian(G)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.6))
        
        try:
            # Find Euler path
            if len(odd_degree_nodes) == 0:  # Euler circuit
                path = list(nx.eulerian_circuit(G))
                path = [u for u, v in path]
            else:  # Euler path
                path = list(nx.eulerian_path(G))
                path = [u for u, v in path]
            
            # Update the current path
            self.current_path = path
            
            # Update the visualization
            self.root.after(0, self.update_3d_plot)
            self.root.after(0, self.update_map_view)
            self.root.after(0, self.update_directions)
            self.root.after(0, self.update_statistics)
            
        except nx.NetworkXError:
            self.root.after(0, lambda: self.show_error("Error", "Could not find an Euler path."))
            self.root.after(0, lambda: self.status_var.set("Error finding Euler path"))
            
    def find_astar_path(self):
        """Find path using A* algorithm"""
        if len(self.locations) < 2:
            self.root.after(0, lambda: self.show_error("Error", "Please add at least two locations"))
            return
            
        # Create a graph
        G = nx.Graph()
        
        # Add nodes
        for i, loc in enumerate(self.locations):
            G.add_node(i, pos=(loc["lat"], loc["lng"]), name=loc["name"])
        
        # Add edges with distances
        for i in range(len(self.locations)):
            for j in range(i+1, len(self.locations)):
                loc1 = self.locations[i]
                loc2 = self.locations[j]
                dist = geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers
                G.add_edge(i, j, weight=dist)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.4))
        
        # Use A* to find the shortest path between all pairs of locations
        path = [0]  # Start with the first location
        current = 0
        unvisited = set(range(1, len(self.locations)))
        
        while unvisited:
            # Use A* to find the nearest unvisited location
            min_cost = float('inf')
            next_node = None
            
            for node in unvisited:
                # Calculate the A* heuristic (distance + estimated remaining distance)
                try:
                    cost = nx.astar_path_length(G, current, node, weight='weight')
                    if cost < min_cost:
                        min_cost = cost
                        next_node = node
                except Exception:
                    continue
            
            if next_node is None:
                # If no path found, just pick the first unvisited
                next_node = list(unvisited)[0]
            
            path.append(next_node)
            current = next_node
            unvisited.remove(next_node)
        
        # Return to start to complete the tour
        path.append(0)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.7))
        
        # Update the current path
        self.current_path = path
        
        # Update the visualization
        self.root.after(0, self.update_3d_plot)
        self.root.after(0, self.update_map_view)
        self.root.after(0, self.update_directions)
        self.root.after(0, self.update_statistics)
        
    def find_dijkstra_path(self):
        """Find path using Dijkstra's algorithm"""
        if len(self.locations) < 2:
            self.root.after(0, lambda: self.show_error("Error", "Please add at least two locations"))
            return
            
        # Create a graph
        G = nx.Graph()
        
        # Add nodes
        for i, loc in enumerate(self.locations):
            G.add_node(i, pos=(loc["lat"], loc["lng"]), name=loc["name"])
        
        # Add edges with distances
        for i in range(len(self.locations)):
            for j in range(i+1, len(self.locations)):
                loc1 = self.locations[i]
                loc2 = self.locations[j]
                dist = geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers
                G.add_edge(i, j, weight=dist)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.4))
        
        # Use Dijkstra to find the shortest path between all pairs of locations
        path = [0]  # Start with the first location
        current = 0
        unvisited = set(range(1, len(self.locations)))
        
        while unvisited:
            # Use Dijkstra to find the nearest unvisited location
            min_distance = float('inf')
            next_node = None
            
            for node in unvisited:
                try:
                    distance = nx.dijkstra_path_length(G, current, node, weight='weight')
                    if distance < min_distance:
                        min_distance = distance
                        next_node = node
                except Exception:
                    continue
            
            if next_node is None:
                # If no path found, just pick the first unvisited
                next_node = list(unvisited)[0]
            
            path.append(next_node)
            current = next_node
            unvisited.remove(next_node)
        
        # Return to start to complete the tour
        path.append(0)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.7))
        
        # Update the current path
        self.current_path = path
        
        # Update the visualization
        self.root.after(0, self.update_3d_plot)
        self.root.after(0, self.update_map_view)
        self.root.after(0, self.update_directions)
        self.root.after(0, self.update_statistics)
    
    def find_mst_path(self):
        """Find minimum spanning tree path"""
        if len(self.locations) < 2:
            self.root.after(0, lambda: self.show_error("Error", "Please add at least two locations"))
            return
            
        # Create a graph
        G = nx.Graph()
        
        # Add nodes
        for i, loc in enumerate(self.locations):
            G.add_node(i, pos=(loc["lat"], loc["lng"]), name=loc["name"])
        
        # Add edges with distances
        for i in range(len(self.locations)):
            for j in range(i+1, len(self.locations)):
                loc1 = self.locations[i]
                loc2 = self.locations[j]
                dist = geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers
                G.add_edge(i, j, weight=dist)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.4))
        
        # Find minimum spanning tree
        mst = nx.minimum_spanning_tree(G, weight='weight')
        
        # Get a DFS traversal of the MST
        path = list(nx.dfs_preorder_nodes(mst, source=0))
        
        # Return to start to complete the tour
        path.append(0)
        
        # Update progress
        self.root.after(0, lambda: self.progress_bar.set(0.7))
        
        # Update the current path
        self.current_path = path
        
        # Update the visualization
        self.root.after(0, self.update_3d_plot)
        self.root.after(0, self.update_map_view)
        self.root.after(0, self.update_directions)
        self.root.after(0, self.update_statistics)
        
    def solve_tsp(self, G):
        """Solve the Traveling Salesman Problem using a greedy algorithm"""
        start_node = 0  # Start from the first node
        path = [start_node]
        unvisited = set(G.nodes())
        unvisited.remove(start_node)
        
        while unvisited:
            current = path[-1]
            next_node = min(unvisited, key=lambda x: G[current][x]['weight'])
            path.append(next_node)
            unvisited.remove(next_node)
        
        # Complete the tour by returning to the start node
        path.append(start_node)
        return path
    
    def make_graph_eulerian(self, G):
        """Make graph Eulerian by adding minimum weight edges between odd degree nodes"""
        odd_degree_nodes = [n for n, d in G.degree() if d % 2 == 1]
        
        if len(odd_degree_nodes) % 2 != 0:
            # This shouldn't happen in an undirected graph
            return
        
        # Find minimum weight matching
        matching_edges = []
        while odd_degree_nodes:
            u = odd_degree_nodes.pop(0)
            min_dist = float('inf')
            min_v = None
            
            for v in odd_degree_nodes:
                dist = G[u][v]['weight'] if G.has_edge(u, v) else float('inf')
                if dist < min_dist:
                    min_dist = dist
                    min_v = v
            
            if min_v is None:
                # If no edge exists, connect to the first available node
                min_v = odd_degree_nodes[0]
                
            odd_degree_nodes.remove(min_v)
            matching_edges.append((u, min_v))
        
        # Add duplicate edges for the matching
        for u, v in matching_edges:
            if G.has_edge(u, v):
                weight = G[u][v]['weight']
            else:
                # Calculate weight if edge doesn't exist
                pos_u = G.nodes[u]['pos']
                pos_v = G.nodes[v]['pos']
                weight = geodesic(pos_u, pos_v).kilometers
                G.add_edge(u, v, weight=weight)
    
    def update_map_view(self):
        """Update the map view with the current path"""
        if not self.current_path or len(self.current_path) < 2:
            return
            
        # Create a map centered on the first location
        center_lat = self.locations[0]["lat"]
        center_lng = self.locations[0]["lng"]
        map_obj = folium.Map(location=[center_lat, center_lng], zoom_start=10)
        
        # Add Fullscreen control
        Fullscreen().add_to(map_obj)
        
        # Add markers for each location
        marker_cluster = MarkerCluster().add_to(map_obj)
        
        for i, loc in enumerate(self.locations):
            # Different icon for start/end
            if i == self.current_path[0]:
                icon = folium.Icon(color='green', icon='flag')
            elif i == self.current_path[-1]:
                icon = folium.Icon(color='red', icon='flag-checkered')
            else:
                icon = folium.Icon(color='blue', icon='info-sign')
                
            popup_text = f"""
            <div style="font-family: Arial; min-width: 200px;">
                <h4>{loc['name']}</h4>
                <b>Postal Code:</b> {loc['postal_code']}<br>
                <b>Coordinates:</b> {loc['lat']:.6f}, {loc['lng']:.6f}<br>
                <b>Elevation:</b> {loc['elevation']:.2f} m
            </div>
            """
            
            folium.Marker(
                [loc["lat"], loc["lng"]], 
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{i+1}. {loc['name']}",
                icon=icon
            ).add_to(marker_cluster)
        
        # Add colored path
        path_points = [(self.locations[i]["lat"], self.locations[i]["lng"]) for i in self.current_path]
        
        # Use AntPath for animated path display
        AntPath(
            path_points,
            color="blue",
            weight=4,
            opacity=0.8,
            dash_array=[10, 20],
        ).add_to(map_obj)
        
        # Add distance markers
        total_distance = 0
        for i in range(len(self.current_path) - 1):
            idx1 = self.current_path[i]
            idx2 = self.current_path[i + 1]
            loc1 = self.locations[idx1]
            loc2 = self.locations[idx2]
            dist = geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers
            total_distance += dist
            
            # Add midpoint marker with distance
            mid_lat = (loc1["lat"] + loc2["lat"]) / 2
            mid_lng = (loc1["lng"] + loc2["lng"]) / 2
            
            folium.Marker(
                [mid_lat, mid_lng],
                tooltip=f"Distance: {dist:.2f} km",
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size: 10pt;
                        font-weight: bold;
                        color: white;
                        background-color: rgba(0, 0, 255, 0.7);
                        border-radius: 5px;
                        padding: 2px 5px;
                        width: fit-content;
                        text-align: center;">
                        {dist:.2f} km
                    </div>
                    """
                )
            ).add_to(map_obj)
        
        # Save the map to a temporary file
        temp_map_file = os.path.join(tempfile.gettempdir(), "advanced_pathfinder_map.html")
        map_obj.save(temp_map_file)
        
        # Update the map view label
        self.map_view_label.configure(text=f"Map created with {len(self.locations)} locations. Total distance: {total_distance:.2f} km")
        
        # Store the map file path
        self.current_map_file = temp_map_file
        
    def open_map_in_browser(self):
        """Open the current map in the default web browser"""
        if hasattr(self, 'current_map_file'):
            webbrowser.open(f"file://{self.current_map_file}")
        else:
            self.show_info("Info", "No map available. Calculate a path first.")
    
    def update_directions(self):
        """Update the directions tab with turn-by-turn directions"""
        if not self.current_path or len(self.current_path) < 2:
            return
            
        # Clear previous directions
        self.directions_text.delete(1.0, tk.END)
        
        # Get transport mode
        transport_mode = self.transport_var.get()
        
        # Header
        self.directions_text.insert(tk.END, "TURN-BY-TURN DIRECTIONS\n", "header")
        self.directions_text.insert(tk.END, f"Transport Mode: {transport_mode}\n\n", "subheader")
        
        # Calculate total distance and estimated time
        total_distance = 0
        total_time = 0
        
        # Speed estimates in km/h for different transport modes
        speeds = {
            "driving-car": 60,
            "driving-hgv": 45,
            "cycling-regular": 15,
            "cycling-road": 20,
            "cycling-mountain": 12,
            "cycling-electric": 25,
            "foot-walking": 5,
            "foot-hiking": 3
        }
        
        speed = speeds.get(transport_mode, 50)  # Default to 50 km/h if not found
        
        # Step by step directions
        self.directions_text.insert(tk.END, "ROUTE OVERVIEW:\n", "section")
        
        for i in range(len(self.current_path) - 1):
            idx1 = self.current_path[i]
            idx2 = self.current_path[i + 1]
            loc1 = self.locations[idx1]
            loc2 = self.locations[idx2]
            
            # Calculate distance
            dist = geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers
            total_distance += dist
            
            # Calculate time (hours) based on speed
            time_hrs = dist / speed
            total_time += time_hrs
            
            # Format time as HH:MM
            time_mins = int(time_hrs * 60)
            time_str = f"{time_mins // 60}h {time_mins % 60}m"
            
            # Calculate bearing for direction
            bearing = self.calculate_bearing(loc1["lat"], loc1["lng"], loc2["lat"], loc2["lng"])
            direction = self.bearing_to_direction(bearing)
            
            # Step details
            step_text = f"{i+1}. From {loc1['name']} to {loc2['name']}\n"
            step_text += f"   Direction: {direction} ({bearing:.1f}°)\n"
            step_text += f"   Distance: {dist:.2f} km\n"
            step_text += f"   Estimated Time: {time_str}\n\n"
            
            self.directions_text.insert(tk.END, step_text)
        
        # Summary
        summary_text = "\nSUMMARY:\n"
        summary_text += f"Total Distance: {total_distance:.2f} km\n"
        
        # Format total time
        total_mins = int(total_time * 60)
        hrs = total_mins // 60
        mins = total_mins % 60
        
        if hrs > 0:
            summary_text += f"Total Estimated Time: {hrs}h {mins}m\n"
        else:
            summary_text += f"Total Estimated Time: {mins}m\n"
            
        self.directions_text.insert(tk.END, summary_text, "summary")
        
        # Apply text styling
        self.directions_text.tag_configure("header", font=("Arial", 14, "bold"))
        self.directions_text.tag_configure("subheader", font=("Arial", 12, "italic"))
        self.directions_text.tag_configure("section", font=("Arial", 12, "bold"))
        self.directions_text.tag_configure("summary", font=("Arial", 12, "bold"))
        
    def update_statistics(self):
        """Update the statistics tab with path analysis"""
        if not self.current_path or len(self.current_path) < 2:
            return
            
        # Clear previous stats
        self.stats_canvas.delete("all")
        
        # Calculate various metrics
        distances = []
        elevations = []
        for i in range(len(self.current_path) - 1):
            idx1 = self.current_path[i]
            idx2 = self.current_path[i + 1]
            loc1 = self.locations[idx1]
            loc2 = self.locations[idx2]
            
            # Distance
            dist = geodesic((loc1["lat"], loc1["lng"]), (loc2["lat"], loc2["lng"])).kilometers
            distances.append(dist)
            
            # Elevation change
            elev_change = loc2["elevation"] - loc1["elevation"]
            elevations.append(elev_change)
        
        # Create statistics layout
        width = self.stats_canvas.winfo_width()
        height = self.stats_canvas.winfo_height()
        
        if width < 10 or height < 10:  # Canvas not yet properly sized
            self.root.after(100, self.update_statistics)  # Try again later
            return
            
        # Set background
        self.stats_canvas.create_rectangle(0, 0, width, height, fill="#2B2B2B", outline="")
        
        # Title
        self.stats_canvas.create_text(width/2, 30, text="Path Statistics", fill="white", font=("Arial", 18, "bold"))
        
        # Distance section
        y_pos = 80
        self.stats_canvas.create_text(width/2, y_pos, text="Distance Analysis", fill="#00BFFF", font=("Arial", 14, "bold"))
        
        y_pos += 30
        total_distance = sum(distances)
        avg_distance = total_distance / len(distances)
        max_distance = max(distances)
        min_distance = min(distances)
        
        stats_text = f"Total Distance: {total_distance:.2f} km\n"
        stats_text += f"Average Segment: {avg_distance:.2f} km\n"
        stats_text += f"Longest Segment: {max_distance:.2f} km\n"
        stats_text += f"Shortest Segment: {min_distance:.2f} km"
        
        self.stats_canvas.create_text(width/2, y_pos, text=stats_text, fill="white", font=("Arial", 12), justify=tk.CENTER)
        
        # Elevation section
        y_pos += 100
        self.stats_canvas.create_text(width/2, y_pos, text="Elevation Analysis", fill="#00BFFF", font=("Arial", 14, "bold"))
        
        y_pos += 30
        total_ascent = sum([e for e in elevations if e > 0])
        total_descent = abs(sum([e for e in elevations if e < 0]))
        net_elevation = sum(elevations)
        
        elev_text = f"Total Ascent: {total_ascent:.2f} m\n"
        elev_text += f"Total Descent: {total_descent:.2f} m\n"
        elev_text += f"Net Elevation Change: {net_elevation:.2f} m"
        
        self.stats_canvas.create_text(width/2, y_pos, text=elev_text, fill="white", font=("Arial", 12), justify=tk.CENTER)
        
        # Time section
        y_pos += 100
        self.stats_canvas.create_text(width/2, y_pos, text="Time Estimates", fill="#00BFFF", font=("Arial", 14, "bold"))
        
        y_pos += 30
        transport_mode = self.transport_var.get()
        
        # Speed estimates in km/h for different transport modes
        speeds = {
            "driving-car": 60,
            "driving-hgv": 45,
            "cycling-regular": 15,
            "cycling-road": 20,
            "cycling-mountain": 12,
            "cycling-electric": 25,
            "foot-walking": 5,
            "foot-hiking": 3
        }
        
        speed = speeds.get(transport_mode, 50)
        time_hrs = total_distance / speed
        
        # Format time as hours and minutes
        time_mins = int(time_hrs * 60)
        hrs = time_mins // 60
        mins = time_mins % 60
        
        time_text = f"Transport Mode: {transport_mode}\n"
        time_text += f"Average Speed: {speed} km/h\n"
        
        if hrs > 0:
            time_text += f"Estimated Travel Time: {hrs}h {mins}m"
        else:
            time_text += f"Estimated Travel Time: {mins}m"
            
        self.stats_canvas.create_text(width/2, y_pos, text=time_text, fill="white", font=("Arial", 12), justify=tk.CENTER)
        
        # Draw mini chart - distance distribution
        if width > 400:
            chart_width = width * 0.8
            chart_height = 60
            chart_x = (width - chart_width) / 2
            chart_y = height - chart_height - 40
            
            # Draw chart background
            self.stats_canvas.create_rectangle(chart_x, chart_y, chart_x + chart_width, chart_y + chart_height, 
                                            fill="#1E1E1E", outline="#AAAAAA")
            
            # Draw bars for each segment
            if distances:
                max_val = max(distances)
                bar_width = chart_width / len(distances)
                
                for i, dist in enumerate(distances):
                    bar_height = (dist / max_val) * chart_height
                    bar_x = chart_x + i * bar_width
                    bar_y = chart_y + chart_height - bar_height
                    
                    # Color based on distance relative to average
                    if dist > avg_distance:
                        color = "#FF6B6B"  # Red for above average
                    else:
                        color = "#4ECDC4"  # Teal for below average
                    
                    self.stats_canvas.create_rectangle(bar_x, bar_y, bar_x + bar_width - 1, chart_y + chart_height, 
                                                    fill=color, outline="")
            
            # Chart title
            self.stats_canvas.create_text(width/2, chart_y - 15, text="Distance Distribution by Segment", 
                                       fill="white", font=("Arial", 10))
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate the bearing between two points"""
        # Convert to radians
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)
        
        # Calculate bearing
        y = math.sin(lon2 - lon1) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
        bearing = math.degrees(math.atan2(y, x))
        
        # Normalize to 0-360
        return (bearing + 360) % 360
    
    def bearing_to_direction(self, bearing):
        """Convert bearing in degrees to cardinal direction"""
        directions = ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest", "North"]
        index = round(bearing / 45)
        return directions[index]
    
    def start_animation(self):
        """Start path animation"""
        if not self.current_path or len(self.current_path) < 2:
            self.show_info("Info", "No path available. Calculate a path first.")
            return
            
        if self.animation_running:
            return
            
        self.animation_running = True
        self.animation_step = 0
        self.animate_path()
        
    def stop_animation(self):
        """Stop path animation"""
        self.animation_running = False
        
        # Reset 3D plot to show full path
        self.update_3d_plot()
        
    def animate_path(self):
        """Animate the path step by step"""
        if not self.animation_running:
            return
            
        # Clear the plot
        self.ax.clear()
        
        # Style the plot
        self.ax.set_facecolor('#2B2B2B')
        self.ax.set_xlabel('Longitude', color='white')
        self.ax.set_ylabel('Latitude', color='white')
        self.ax.set_zlabel('Elevation (m)', color='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.zaxis.label.set_color('white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.tick_params(axis='z', colors='white')
        
        # Add points for each location
        xs = [loc["lng"] for loc in self.locations]
        ys = [loc["lat"] for loc in self.locations]
        zs = [loc["elevation"] for loc in self.locations]
        
        # Plot all points in lighter color
        self.ax.scatter(xs, ys, zs, color='gray', s=50, marker='o', alpha=0.5)
        
        # Calculate current animation portion
        if self.animation_step <= len(self.current_path) - 1:
            # Animate up to current step
            path_indices = self.current_path[:self.animation_step+1]
        else:
            # Animation complete, show full path
            path_indices = self.current_path
            
        # Draw animated path
        path_xs = [self.locations[i]["lng"] for i in path_indices]
        path_ys = [self.locations[i]["lat"] for i in path_indices]
        path_zs = [self.locations[i]["elevation"] for i in path_indices]
        
        # Plot the current path segment
        self.ax.plot(path_xs, path_ys, path_zs, 'r-', linewidth=3, alpha=1.0)
        
        # Highlight the current point
        if self.animation_step < len(self.current_path):
            current_idx = self.current_path[self.animation_step]
            current_loc = self.locations[current_idx]
            self.ax.scatter([current_loc["lng"]], [current_loc["lat"]], [current_loc["elevation"]], 
                          color='yellow', s=150, marker='o', edgecolor='black')
            
            # Add label for current point
            self.ax.text(current_loc["lng"], current_loc["lat"], current_loc["elevation"], 
                       f"{self.animation_step+1}. {current_loc['name']}", color='yellow', fontsize=12)
                       
            # Update title with current step info
            if self.animation_step < len(self.current_path) - 1:
                next_idx = self.current_path[self.animation_step + 1]
                next_loc = self.locations[next_idx]
                dist = geodesic((current_loc["lat"], current_loc["lng"]), 
                               (next_loc["lat"], next_loc["lng"])).kilometers
                               
                self.ax.set_title(f"Moving from {current_loc['name']} to {next_loc['name']} ({dist:.2f} km)", 
                                color='white')
            else:
                self.ax.set_title(f"Reached final destination: {current_loc['name']}", color='white')
                
        # Set the limits to fit all points
        if xs:
            self.ax.set_xlim(min(xs) - 0.01, max(xs) + 0.01)
            self.ax.set_ylim(min(ys) - 0.01, max(ys) + 0.01)
            self.ax.set_zlim(min(zs) - 10, max(zs) + 10)
            
        # Redraw the canvas
        self.canvas.draw()
        
        # Increment animation step
        if self.animation_running:
            self.animation_step += 1
            if self.animation_step > len(self.current_path):
                # Reset animation
                self.animation_step = 0
            
            # Schedule next animation step
            self.root.after(self.animation_speed * 10, self.animate_path)
    
    def update_animation_speed(self, value):
        """Update animation speed from slider"""
        self.animation_speed = int(value)
    
    def show_error(self, title, message):
        """Show error message"""
        messagebox.showerror(title, message)
        
    def show_info(self, title, message):
        """Show info message"""
        messagebox.showinfo(title, message)

def main():
    # Check for required libraries and install if not present
    import importlib.util
    if importlib.util.find_spec("customtkinter") is None:
        import subprocess
        import sys
        
        print("Installing required libraries...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "folium", "networkx", "geopy", "matplotlib", "pillow", "numpy"])
        
        # Restart application after installation
        print("Libraries installed. Restarting application...")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    # Create root window
    root = ctk.CTk()
    _ = AdvancedPathfinder(root)
    root.mainloop()

if __name__ == "__main__":
    main()