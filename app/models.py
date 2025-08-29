from sqlmodel import SQLModel, Field, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any


# Persistent models (stored in database)
class Polygon(SQLModel, table=True):
    """
    Represents a drawn polygon on the map with its geometric data and metadata.
    """

    __tablename__ = "polygons"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, description="User-assigned name for the polygon")
    coordinates: List[List[List[float]]] = Field(
        sa_column=Column(JSON), description="GeoJSON-style coordinates array for polygon geometry"
    )
    properties: Dict[str, Any] = Field(
        default={}, sa_column=Column(JSON), description="Additional properties for the polygon (style, metadata, etc.)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()


# Non-persistent schemas (for validation, forms, API requests/responses)
class PolygonCreate(SQLModel, table=False):
    """Schema for creating a new polygon."""

    name: str = Field(max_length=255, min_length=1, description="Name for the polygon")
    coordinates: List[List[List[float]]] = Field(
        min_items=1, description="GeoJSON-style coordinates array for polygon geometry"
    )
    properties: Dict[str, Any] = Field(default={}, description="Additional properties for the polygon")


class PolygonUpdate(SQLModel, table=False):
    """Schema for updating an existing polygon."""

    name: Optional[str] = Field(default=None, max_length=255, min_length=1, description="Updated name for the polygon")
    coordinates: Optional[List[List[List[float]]]] = Field(
        default=None, min_items=1, description="Updated coordinates for the polygon"
    )
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Updated properties for the polygon")


class PolygonResponse(SQLModel, table=False):
    """Schema for polygon API responses."""

    id: int
    name: str
    coordinates: List[List[List[float]]]
    properties: Dict[str, Any]
    created_at: str  # ISO format datetime string
    updated_at: Optional[str] = None  # ISO format datetime string

    @classmethod
    def from_polygon(cls, polygon: Polygon) -> "PolygonResponse":
        """Create a PolygonResponse from a Polygon model instance."""
        return cls(
            id=polygon.id if polygon.id is not None else 0,
            name=polygon.name,
            coordinates=polygon.coordinates,
            properties=polygon.properties,
            created_at=polygon.created_at.isoformat(),
            updated_at=polygon.updated_at.isoformat() if polygon.updated_at else None,
        )


class PolygonListResponse(SQLModel, table=False):
    """Schema for listing multiple polygons."""

    polygons: List[PolygonResponse]
    total: int
