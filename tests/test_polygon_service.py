import pytest
from app.polygon_service import polygon_service
from app.models import PolygonCreate, PolygonUpdate
from app.database import reset_db


@pytest.fixture
def clean_db():
    """Reset database before each test."""
    reset_db()
    yield
    reset_db()


class TestPolygonService:
    """Test cases for polygon service operations."""

    def test_create_polygon_success(self, clean_db):
        """Test successful polygon creation."""
        polygon_data = PolygonCreate(
            name="Test Polygon",
            coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
            properties={"color": "blue"},
        )

        result = polygon_service.create_polygon(polygon_data)

        assert result is not None
        assert result.name == "Test Polygon"
        assert result.coordinates == [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]]
        assert result.properties == {"color": "blue"}
        assert result.id > 0

    def test_create_polygon_single_character_name(self, clean_db):
        """Test polygon creation with minimal valid name."""
        polygon_data = PolygonCreate(
            name="A", coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]], properties={}
        )

        result = polygon_service.create_polygon(polygon_data)
        assert result is not None
        assert result.name == "A"

    def test_create_polygon_complex_coordinates(self, clean_db):
        """Test polygon creation with complex coordinate structure."""
        complex_coords = [
            [[-74.0059, 40.7128], [-74.0050, 40.7130], [-74.0040, 40.7125], [-74.0045, 40.7120], [-74.0059, 40.7128]]
        ]

        polygon_data = PolygonCreate(
            name="Complex Polygon", coordinates=complex_coords, properties={"area": 1250.5, "type": "park"}
        )

        result = polygon_service.create_polygon(polygon_data)

        assert result is not None
        assert result.name == "Complex Polygon"
        assert result.coordinates == complex_coords
        assert result.properties["area"] == 1250.5
        assert result.properties["type"] == "park"

    def test_get_polygon_exists(self, clean_db):
        """Test getting an existing polygon."""
        # Create polygon first
        polygon_data = PolygonCreate(
            name="Findable Polygon",
            coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]],
            properties={"test": True},
        )
        created = polygon_service.create_polygon(polygon_data)
        assert created is not None

        # Now get it
        result = polygon_service.get_polygon(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Findable Polygon"

    def test_get_polygon_not_exists(self, clean_db):
        """Test getting a non-existent polygon."""
        result = polygon_service.get_polygon(999)
        assert result is None

    def test_list_polygons_empty(self, clean_db):
        """Test listing polygons when none exist."""
        result = polygon_service.list_polygons()

        assert result.total == 0
        assert result.polygons == []

    def test_list_polygons_multiple(self, clean_db):
        """Test listing multiple polygons."""
        # Create multiple polygons
        polygon1 = PolygonCreate(
            name="First Polygon", coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]], properties={}
        )
        polygon2 = PolygonCreate(
            name="Second Polygon", coordinates=[[[2.0, 2.0], [3.0, 2.0], [3.0, 3.0], [2.0, 2.0]]], properties={}
        )

        created1 = polygon_service.create_polygon(polygon1)
        created2 = polygon_service.create_polygon(polygon2)

        assert created1 is not None
        assert created2 is not None

        # List polygons
        result = polygon_service.list_polygons()

        assert result.total == 2
        assert len(result.polygons) == 2

        # Should be ordered by created_at desc (newest first)
        names = [p.name for p in result.polygons]
        assert "Second Polygon" in names
        assert "First Polygon" in names

    def test_update_polygon_name(self, clean_db):
        """Test updating polygon name."""
        # Create polygon
        polygon_data = PolygonCreate(
            name="Original Name", coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]], properties={}
        )
        created = polygon_service.create_polygon(polygon_data)
        assert created is not None

        # Update name
        update_data = PolygonUpdate(name="Updated Name")
        result = polygon_service.update_polygon(created.id, update_data)

        assert result is not None
        assert result.name == "Updated Name"
        assert result.coordinates == created.coordinates  # Should remain unchanged
        assert result.updated_at is not None

    def test_update_polygon_coordinates(self, clean_db):
        """Test updating polygon coordinates."""
        # Create polygon
        original_coords = [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]
        polygon_data = PolygonCreate(name="Test Polygon", coordinates=original_coords, properties={})
        created = polygon_service.create_polygon(polygon_data)
        assert created is not None

        # Update coordinates
        new_coords = [[[2.0, 2.0], [3.0, 2.0], [3.0, 3.0], [2.0, 2.0]]]
        update_data = PolygonUpdate(coordinates=new_coords)
        result = polygon_service.update_polygon(created.id, update_data)

        assert result is not None
        assert result.coordinates == new_coords
        assert result.name == "Test Polygon"  # Should remain unchanged

    def test_update_polygon_properties(self, clean_db):
        """Test updating polygon properties."""
        # Create polygon
        polygon_data = PolygonCreate(
            name="Test Polygon",
            coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]],
            properties={"color": "blue"},
        )
        created = polygon_service.create_polygon(polygon_data)
        assert created is not None

        # Update properties
        new_properties = {"color": "red", "area": 500.0}
        update_data = PolygonUpdate(properties=new_properties)
        result = polygon_service.update_polygon(created.id, update_data)

        assert result is not None
        assert result.properties == new_properties
        assert result.name == "Test Polygon"

    def test_update_polygon_not_exists(self, clean_db):
        """Test updating a non-existent polygon."""
        update_data = PolygonUpdate(name="New Name")
        result = polygon_service.update_polygon(999, update_data)

        assert result is None

    def test_update_polygon_all_fields(self, clean_db):
        """Test updating all polygon fields at once."""
        # Create polygon
        polygon_data = PolygonCreate(
            name="Original", coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]], properties={"old": True}
        )
        created = polygon_service.create_polygon(polygon_data)
        assert created is not None

        # Update all fields
        new_coords = [[[5.0, 5.0], [6.0, 5.0], [6.0, 6.0], [5.0, 5.0]]]
        update_data = PolygonUpdate(name="Updated", coordinates=new_coords, properties={"new": True, "color": "green"})
        result = polygon_service.update_polygon(created.id, update_data)

        assert result is not None
        assert result.name == "Updated"
        assert result.coordinates == new_coords
        assert result.properties == {"new": True, "color": "green"}

    def test_delete_polygon_exists(self, clean_db):
        """Test deleting an existing polygon."""
        # Create polygon
        polygon_data = PolygonCreate(
            name="To Delete", coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]], properties={}
        )
        created = polygon_service.create_polygon(polygon_data)
        assert created is not None

        # Delete polygon
        result = polygon_service.delete_polygon(created.id)
        assert result is True

        # Verify it's gone
        get_result = polygon_service.get_polygon(created.id)
        assert get_result is None

    def test_delete_polygon_not_exists(self, clean_db):
        """Test deleting a non-existent polygon."""
        result = polygon_service.delete_polygon(999)
        assert result is False

    def test_polygon_exists_true(self, clean_db):
        """Test polygon_exists returns True for existing polygon."""
        # Create polygon
        polygon_data = PolygonCreate(
            name="Existing", coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]], properties={}
        )
        created = polygon_service.create_polygon(polygon_data)
        assert created is not None

        result = polygon_service.polygon_exists(created.id)
        assert result is True

    def test_polygon_exists_false(self, clean_db):
        """Test polygon_exists returns False for non-existent polygon."""
        result = polygon_service.polygon_exists(999)
        assert result is False

    def test_polygon_lifecycle(self, clean_db):
        """Test complete polygon lifecycle: create, read, update, delete."""
        # Create
        polygon_data = PolygonCreate(
            name="Lifecycle Test",
            coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]],
            properties={"stage": "created"},
        )
        created = polygon_service.create_polygon(polygon_data)
        assert created is not None
        assert created.name == "Lifecycle Test"

        # Read
        read_result = polygon_service.get_polygon(created.id)
        assert read_result is not None
        assert read_result.id == created.id

        # Update
        update_data = PolygonUpdate(name="Updated Lifecycle", properties={"stage": "updated"})
        updated = polygon_service.update_polygon(created.id, update_data)
        assert updated is not None
        assert updated.name == "Updated Lifecycle"
        assert updated.properties["stage"] == "updated"

        # Delete
        delete_result = polygon_service.delete_polygon(created.id)
        assert delete_result is True

        # Verify deletion
        final_result = polygon_service.get_polygon(created.id)
        assert final_result is None
