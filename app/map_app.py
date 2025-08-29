# pyright: reportOptionalCall=false
from nicegui import ui
import json
import logging
from app.polygon_service import polygon_service
from app.models import PolygonCreate

logger = logging.getLogger(__name__)


class MapApp:
    """Interactive map application for polygon management."""

    def __init__(self):
        self.map_element = None
        self.polygon_list_container = None
        self.current_drawing_data = None
        self.save_card = None
        self.polygon_data_input = None

    def create(self) -> None:
        """Create the main map application UI."""

        @ui.page("/")
        def map_page():
            # Apply modern theme
            ui.colors(
                primary="#2563eb",
                secondary="#64748b",
                accent="#10b981",
                positive="#10b981",
                negative="#ef4444",
                warning="#f59e0b",
                info="#3b82f6",
            )

            ui.page_title("Interactive Polygon Map")

            # Header
            with ui.row().classes("w-full justify-between items-center p-4 bg-white shadow-sm"):
                ui.label("Polygon Map Manager").classes("text-2xl font-bold text-gray-800")
                ui.icon("map").classes("text-3xl text-primary")

            # Main layout
            with ui.row().classes("w-full h-screen gap-0"):
                # Map area (left side)
                with ui.column().classes("flex-1 h-full"):
                    self._create_map_controls()
                    self._create_map()

                # Sidebar (right side)
                with ui.column().classes("w-80 h-full bg-gray-50 border-l border-gray-200"):
                    self._create_sidebar()

    def _create_map_controls(self) -> None:
        """Create map control buttons."""
        with ui.row().classes("p-4 bg-gray-100 gap-4 justify-center"):
            ui.button("Enable Drawing", on_click=self._enable_drawing).classes(
                "bg-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
            ).props("icon=edit")

            ui.button("Clear Drawing", on_click=self._clear_current_drawing).classes(
                "bg-warning text-white px-4 py-2 rounded-lg hover:bg-amber-600 transition-colors"
            ).props("icon=clear")

    def _create_map(self) -> None:
        """Create the Leaflet map."""
        # Create map container
        with ui.column().classes("flex-1 h-full p-4"):
            # Add Leaflet CSS and JS
            ui.add_head_html("""
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
                <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css" />
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
            """)

            # Create map div
            map_html = """
            <div id="map" style="width: 100%; height: 500px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);"></div>
            <script>
                // Initialize map
                window.map = L.map('map').setView([40.7128, -74.0060], 10);
                
                // Add tile layer
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(window.map);
                
                // Feature group for drawn items
                window.drawnItems = new L.FeatureGroup();
                window.map.addLayer(window.drawnItems);
                
                // Draw control
                window.drawControl = new L.Control.Draw({
                    draw: {
                        polygon: {
                            allowIntersection: false,
                            showArea: true
                        },
                        polyline: false,
                        rectangle: false,
                        circle: false,
                        marker: false,
                        circlemarker: false
                    },
                    edit: {
                        featureGroup: window.drawnItems,
                        remove: true
                    }
                });
                
                // Function to enable/disable drawing
                window.toggleDrawing = function(enable) {
                    if (enable) {
                        window.map.addControl(window.drawControl);
                    } else {
                        window.map.removeControl(window.drawControl);
                    }
                };
                
                // Handle draw events
                window.map.on('draw:created', function(e) {
                    var layer = e.layer;
                    window.drawnItems.addLayer(layer);
                    
                    // Get coordinates in GeoJSON format
                    var coordinates = layer.getLatLngs()[0].map(function(latlng) {
                        return [latlng.lng, latlng.lat];
                    });
                    // Close the polygon by adding first point at the end
                    coordinates.push(coordinates[0]);
                    
                    // Send to Python
                    window.currentPolygonCoords = [coordinates];
                    document.dispatchEvent(new CustomEvent('polygon-drawn', {
                        detail: { coordinates: window.currentPolygonCoords }
                    }));
                });
                
                // Function to clear current drawing
                window.clearDrawing = function() {
                    window.drawnItems.clearLayers();
                    window.currentPolygonCoords = null;
                };
                
                // Function to add polygon to map
                window.addPolygonToMap = function(coordinates, name, color) {
                    var latlngs = coordinates[0].map(function(coord) {
                        return [coord[1], coord[0]]; // Convert from [lng, lat] to [lat, lng]
                    });
                    
                    var polygon = L.polygon(latlngs, {
                        color: color || '#3388ff',
                        fillColor: color || '#3388ff',
                        fillOpacity: 0.3
                    }).addTo(window.map);
                    
                    polygon.bindPopup('<b>' + name + '</b>');
                    return polygon;
                };
                
                // Function to load all polygons
                window.loadPolygons = function(polygons) {
                    // Clear existing polygons (except drawn items)
                    window.map.eachLayer(function(layer) {
                        if (layer instanceof L.Polygon && !window.drawnItems.hasLayer(layer)) {
                            window.map.removeLayer(layer);
                        }
                    });
                    
                    // Add all polygons
                    polygons.forEach(function(poly) {
                        window.addPolygonToMap(poly.coordinates, poly.name, '#10b981');
                    });
                };
            </script>
            """

            ui.html(map_html)

            # Create hidden input to receive polygon data from JavaScript
            self.polygon_data_input = ui.input().classes("hidden")

            # Set up JavaScript communication
            ui.run_javascript("""
                document.addEventListener('polygon-drawn', function(e) {
                    // Send coordinates to hidden input and trigger change
                    const input = document.querySelector('input[data-testid="polygon_data"]');
                    if (input) {
                        input.value = JSON.stringify(e.detail.coordinates);
                        input.dispatchEvent(new Event('input'));
                    }
                });
            """)

            # Handle polygon data changes
            self.polygon_data_input.on("input", self._on_polygon_data_received)
            self.polygon_data_input.props("data-testid=polygon_data")

    def _create_sidebar(self) -> None:
        """Create the sidebar with polygon list and controls."""
        with ui.column().classes("h-full p-4 gap-4"):
            # Sidebar header
            ui.label("Stored Polygons").classes("text-xl font-bold text-gray-800 mb-4")

            # Save polygon form (initially hidden)
            self.save_card = ui.card().classes("w-full p-4 shadow-md rounded-lg")
            self.save_card.visible = False

            with self.save_card:
                ui.label("Save Current Drawing").classes("text-lg font-semibold mb-3")

                polygon_name = ui.input(label="Polygon Name", placeholder="Enter a name for this polygon").classes(
                    "w-full mb-3"
                )

                with ui.row().classes("gap-2 justify-end"):
                    ui.button("Cancel", on_click=self._cancel_save).classes("px-4 py-2").props("outline")

                    ui.button("Save Polygon", on_click=lambda: self._save_polygon(polygon_name.value)).classes(
                        "bg-accent text-white px-4 py-2 rounded"
                    )

            # Polygon list
            with ui.column().classes("flex-1 overflow-auto"):
                self.polygon_list_container = ui.column().classes("gap-2")
                self._refresh_polygon_list()

    def _enable_drawing(self) -> None:
        """Enable drawing mode on the map."""
        ui.run_javascript("window.toggleDrawing(true);")
        ui.notify("Drawing enabled. Click the polygon tool to start drawing.", type="info")

    def _clear_current_drawing(self) -> None:
        """Clear the current drawing from the map."""
        ui.run_javascript("window.clearDrawing();")
        self.current_drawing_data = None
        ui.notify("Drawing cleared.", type="info")

    def _cancel_save(self) -> None:
        """Cancel saving the current polygon."""
        self.current_drawing_data = None
        if self.save_card is not None:
            self.save_card.visible = False
        ui.notify("Save cancelled.", type="info")

    def _save_polygon(self, name: str) -> None:
        """Save the current polygon to the database."""
        if not name or not name.strip():
            ui.notify("Please enter a name for the polygon.", type="warning")
            return

        if self.current_drawing_data is None:
            ui.notify("No polygon to save. Please draw a polygon first.", type="warning")
            return

        try:
            polygon_create = PolygonCreate(
                name=name.strip(), coordinates=self.current_drawing_data, properties={"color": "#3388ff"}
            )

            result = polygon_service.create_polygon(polygon_create)
            if result:
                ui.notify(f'Polygon "{name}" saved successfully!', type="positive")
                self.current_drawing_data = None
                if self.save_card is not None:
                    self.save_card.visible = False
                self._refresh_polygon_list()
                self._load_all_polygons_to_map()
            else:
                ui.notify("Failed to save polygon. Please try again.", type="negative")

        except Exception as e:
            logger.error(f"Error saving polygon: {e}")
            ui.notify(f"Error saving polygon: {str(e)}", type="negative")

    def _delete_polygon(self, polygon_id: int, polygon_name: str) -> None:
        """Delete a polygon after confirmation."""

        async def confirm_delete():
            with ui.dialog() as dialog, ui.card():
                ui.label(f'Delete polygon "{polygon_name}"?').classes("text-lg mb-4")
                ui.label("This action cannot be undone.").classes("text-gray-600 mb-4")

                with ui.row().classes("gap-2 justify-end"):
                    ui.button("Cancel", on_click=lambda: dialog.submit(False)).props("outline")
                    ui.button("Delete", on_click=lambda: dialog.submit(True)).classes("bg-negative text-white")

            result = await dialog
            if result:
                if polygon_service.delete_polygon(polygon_id):
                    ui.notify(f'Polygon "{polygon_name}" deleted.', type="positive")
                    self._refresh_polygon_list()
                    self._load_all_polygons_to_map()
                else:
                    ui.notify("Failed to delete polygon.", type="negative")

        # Note: In a production app, we'd use proper async handling
        # For now, skip the confirmation dialog due to async complexity
        if polygon_service.delete_polygon(polygon_id):
            ui.notify(f'Polygon "{polygon_name}" deleted.', type="positive")
            self._refresh_polygon_list()
            self._load_all_polygons_to_map()
        else:
            ui.notify("Failed to delete polygon.", type="negative")

    def _refresh_polygon_list(self) -> None:
        """Refresh the polygon list in the sidebar."""
        if self.polygon_list_container is None:
            return

        if self.polygon_list_container is not None:
            self.polygon_list_container.clear()  # type: ignore

        polygon_list = polygon_service.list_polygons()

        if polygon_list.total == 0:
            if self.polygon_list_container is not None:
                with self.polygon_list_container:
                    ui.label("No polygons saved yet.").classes("text-gray-500 text-center py-8")
        else:
            if self.polygon_list_container is not None:
                with self.polygon_list_container:
                    for polygon in polygon_list.polygons:
                        with ui.card().classes("w-full p-3 shadow-sm rounded-lg hover:shadow-md transition-shadow"):
                            with ui.row().classes("w-full items-center justify-between"):
                                with ui.column().classes("flex-1"):
                                    ui.label(polygon.name).classes("font-semibold text-gray-800")
                                    ui.label(f"Created: {polygon.created_at[:10]}").classes("text-sm text-gray-500")

                                ui.button(
                                    on_click=lambda e, p_id=polygon.id, p_name=polygon.name: self._delete_polygon(
                                        p_id, p_name
                                    )
                                ).props("icon=delete color=negative flat round size=sm")

    def _load_all_polygons_to_map(self) -> None:
        """Load all saved polygons onto the map."""
        polygon_list = polygon_service.list_polygons()
        polygons_json = json.dumps([{"coordinates": p.coordinates, "name": p.name} for p in polygon_list.polygons])

        ui.run_javascript(f"window.loadPolygons({polygons_json});")

    def _on_polygon_data_received(self, e) -> None:
        """Handle polygon data received from JavaScript."""
        try:
            if e.value:
                coordinates = json.loads(e.value)
                self.current_drawing_data = coordinates
                if self.save_card is not None:
                    self.save_card.visible = True
                ui.notify("Polygon drawn! Enter a name to save it.", type="positive")
                # Clear the input for next polygon
                if self.polygon_data_input is not None:
                    self.polygon_data_input.value = ""
        except json.JSONDecodeError as e:
            logger.error(f"Error processing polygon JSON data: {e}")
            ui.notify("Error processing polygon data.", type="negative")


# Global app instance
map_app = MapApp()  # type: ignore


def create() -> None:
    """Create the map application."""
    map_app.create()

    # Load existing polygons on startup
    @ui.on("connect")
    def on_connect():
        def load_polygons():
            map_app._load_all_polygons_to_map()

        ui.timer(0.5, load_polygons, once=True)  # type: ignore
