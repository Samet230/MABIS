import math
from typing import Any, Dict, Final, List, Optional

EARTH_RADIUS_METERS: Final[float] = 6371000.0
DEFAULT_TERRITORY_MIN_RADIUS_METERS: Final[float] = 120.0
DEFAULT_TERRITORY_DEFAULT_RADIUS_METERS: Final[float] = 160.0


def CalculateHaversineDistanceMeters(
    latitudeOne: float, longitudeOne: float, latitudeTwo: float, longitudeTwo: float
) -> float:
    """İki GPS koordinatı arasındaki mesafeyi Haversine formülü ile metre cinsinden hesaplar."""
    phiOneRadians = math.radians(latitudeOne)
    phiTwoRadians = math.radians(latitudeTwo)
    deltaLatitudeRadians = math.radians(latitudeTwo - latitudeOne)
    deltaLongitudeRadians = math.radians(longitudeTwo - longitudeOne)

    haversineTerm = (
        math.sin(deltaLatitudeRadians / 2.0) ** 2
        + math.cos(phiOneRadians) * math.cos(phiTwoRadians) * (math.sin(deltaLongitudeRadians / 2.0) ** 2)
    )
    haversineDistanceAngle = 2.0 * math.atan2(
        math.sqrt(haversineTerm), math.sqrt(max(0.0, 1.0 - haversineTerm))
    )
    return EARTH_RADIUS_METERS * haversineDistanceAngle


def CalculateTerritoryStats(sightingsList: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sokak hayvanının görülme noktalarından ortalama merkezini (centroid) ve yaşam alanını hesaplar."""
    if not sightingsList:
        return {
            "centroid": None,
            "territoryRadiusMeters": 0.0,
            "sightingsCount": 0,
            "primaryZone": "Henüz Konum Belirtilmedi",
            "recentSightings": [],
        }

    validCoordinatesList: List[Dict[str, Any]] = []
    for sightItem in sightingsList:
        latitudeValue = sightItem.get("latitude")
        longitudeValue = sightItem.get("longitude")
        if latitudeValue is not None and longitudeValue is not None:
            try:
                validCoordinatesList.append({
                    "lat": float(latitudeValue),
                    "lon": float(longitudeValue),
                    "name": str(sightItem.get("locationName", "")).strip(),
                    "time": str(sightItem.get("timestamp", "")),
                    "confidence": float(sightItem.get("confidence", 0.0)),
                })
            except (ValueError, TypeError):
                continue

    if not validCoordinatesList:
        return {
            "centroid": None,
            "territoryRadiusMeters": 0.0,
            "sightingsCount": len(sightingsList),
            "primaryZone": "Konum Koordinatı Yok",
            "recentSightings": sightingsList[-5:],
        }

    # Aritmetik ortalama merkez (Centroid)
    averageLatitude = sum(pointItem["lat"] for pointItem in validCoordinatesList) / len(validCoordinatesList)
    averageLongitude = sum(pointItem["lon"] for pointItem in validCoordinatesList) / len(validCoordinatesList)

    distancesFromCentroidList = [
        CalculateHaversineDistanceMeters(averageLatitude, averageLongitude, pointItem["lat"], pointItem["lon"])
        for pointItem in validCoordinatesList
    ]

    maxRadiusFound = max(distancesFromCentroidList) if distancesFromCentroidList else 0.0
    if len(validCoordinatesList) > 1:
        estimatedTerritoryRadius = max(
            DEFAULT_TERRITORY_MIN_RADIUS_METERS, round(maxRadiusFound * 1.15, 1)
        )
    else:
        estimatedTerritoryRadius = DEFAULT_TERRITORY_DEFAULT_RADIUS_METERS

    zoneNamesList = [pointItem["name"] for pointItem in validCoordinatesList if pointItem["name"]]
    if zoneNamesList:
        primaryZone = max(set(zoneNamesList), key=zoneNamesList.count)
    else:
        primaryZone = f"{round(averageLatitude, 4)}, {round(averageLongitude, 4)}"

    return {
        "centroid": {
            "latitude": round(averageLatitude, 6),
            "longitude": round(averageLongitude, 6),
        },
        "territoryRadiusMeters": round(estimatedTerritoryRadius, 1),
        "sightingsCount": len(validCoordinatesList),
        "primaryZone": primaryZone,
        "recentSightings": sightingsList[-10:],
    }
