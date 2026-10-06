import io
import cv2
import numpy as np
import pytest

from src.web.app import app


@pytest.fixture
def testClient():
    """Flask test istemcisi fixture'ı."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def CreateDummyEncodedJpg(width: int = 250, height: int = 250) -> io.BytesIO:
    """Bellek içi sentetik test JPG görseli üretir."""
    syntheticImage = np.random.randint(60, 200, (height, width, 3), dtype=np.uint8)
    cv2.circle(syntheticImage, (width // 2, height // 2), 40, (255, 255, 255), thickness=-1)
    cv2.rectangle(syntheticImage, (20, 20), (width - 20, height - 20), (0, 0, 0), thickness=3)

    encodeSuccess, bufferArray = cv2.imencode(".jpg", syntheticImage)
    assert encodeSuccess is True
    return io.BytesIO(bufferArray.tobytes())


def test_index_route(testClient):
    """Ana sayfanın (telefon arayüzünün) 200 OK ile dönmesi doğrulanır."""
    response = testClient.get("/")
    assert response.status_code == 200
    assert b"ZooID" in response.data
    assert b"smartphone-wrapper" in response.data


def test_api_quality_check(testClient):
    """Görüntü kalite kontrol uç noktasının doğru tanı üretmesi test edilir."""
    imageBytesIo = CreateDummyEncodedJpg()
    response = testClient.post(
        "/api/quality_check",
        data={"image": (imageBytesIo, "test.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    jsonData = response.get_json()
    assert jsonData["success"] is True
    assert "isPassed" in jsonData
    assert "metrics" in jsonData


def test_api_register_and_identify_with_passport(testClient):
    """Hayvan pasaport bilgileri (aşı, doğum, durum) ile kayıt ve 1:N tanıma akışı test edilir."""
    # 1. Önce kayıtları temizle
    clearRes = testClient.post("/api/clear")
    assert clearRes.status_code == 200

    # 2. Pasaport detayları ile kayıt yap
    imageBytesIo = CreateDummyEncodedJpg()
    registerRes = testClient.post(
        "/api/register",
        data={
            "animalId": "TR-06-TEST-001",
            "animalName": "Sarıkız",
            "category": "cattle",
            "healthStatus": "lost",  # Kayıp olarak işaretle
            "birthDate": "2023-05",
            "vaccinations": "Kuduz (2025), Şap (2026)",
            "distinctiveFeatures": "Alnında beyaz yıldız",
            "temperament": "Uysal ve sakin",
            "favoriteFood": "Yonca",
            "image": (imageBytesIo, "cattle.jpg"),
            "bypassQuality": "true",
        },
        content_type="multipart/form-data",
    )
    assert registerRes.status_code == 200
    regData = registerRes.get_json()
    assert regData["success"] is True
    assert regData["animalId"] == "TR-06-TEST-001"
    assert regData["animalName"] == "Sarıkız"
    assert regData["healthStatus"] == "lost"

    # 3. Detay uç noktasını çağır (GET /api/animals/<id>)
    detailRes = testClient.get("/api/animals/TR-06-TEST-001")
    assert detailRes.status_code == 200
    detailData = detailRes.get_json()
    assert detailData["success"] is True
    animalObj = detailData["animal"]
    assert animalObj["animalName"] == "Sarıkız"
    assert animalObj["vaccinations"] == "Kuduz (2025), Şap (2026)"
    assert animalObj["healthStatus"] == "lost"

    # 4. Pasaport güncelleme (POST /api/animals/<id>/update)
    updateRes = testClient.post(
        "/api/animals/TR-06-TEST-001/update",
        json={
            "healthStatus": "healthy",  # Bulundu, sağlıklıya çevir
            "animalName": "Sarıkız Sultan",
        },
    )
    assert updateRes.status_code == 200
    updateData = updateRes.get_json()
    assert updateData["success"] is True
    assert updateData["animal"]["healthStatus"] == "healthy"
    assert updateData["animal"]["animalName"] == "Sarıkız Sultan"

    # 5. Arama yap ve eşleşen pasaportun döndüğünü doğrula
    searchBytesIo = CreateDummyEncodedJpg()
    identifyRes = testClient.post(
        "/api/identify",
        data={
            "category": "cattle",
            "image": (searchBytesIo, "query.jpg"),
            "bypassQuality": "true",
        },
        content_type="multipart/form-data",
    )
    assert identifyRes.status_code == 200
    identifyData = identifyRes.get_json()
    assert identifyData["success"] is True
    assert "queryRoi" in identifyData

    # 6. Hayvanı sil (DELETE /api/animals/<id>)
    deleteRes = testClient.delete("/api/animals/TR-06-TEST-001")
    assert deleteRes.status_code == 200
    deleteData = deleteRes.get_json()
    assert deleteData["success"] is True

    # 7. Silindikten sonra liste boş olmalı
    listRes = testClient.get("/api/animals")
    assert listRes.status_code == 200
    assert listRes.get_json()["count"] == 0


def test_cross_species_rejection_in_endpoints(testClient):
    """Büyükbaş kategorisinde köpek burnu yüklendiğinde kayıt ve aramanın 422 ile reddedilmesi test edilir."""
    # Köpek burnu görseli oluştur (açık fon üzerinde merkezde koyu ped)
    dogImage = np.ones((300, 300, 3), dtype=np.uint8) * 180
    trianglePoints = np.array([[150, 90], [90, 180], [210, 180]], np.int32)
    cv2.fillPoly(dogImage, [trianglePoints], (25, 25, 25))
    cv2.circle(dogImage, (120, 160), 12, (10, 10, 10), -1)
    cv2.circle(dogImage, (180, 160), 12, (10, 10, 10), -1)

    encodeSuccess, bufferArray = cv2.imencode(".jpg", dogImage)
    assert encodeSuccess is True
    dogBytes = io.BytesIO(bufferArray.tobytes())

    # 1. Büyükbaş kategorisine köpek kaydı denenmesi -> 422 Reddedilmeli
    registerRes = testClient.post(
        "/api/register",
        data={
            "animalId": "ILLEGAL-DOG-001",
            "animalName": "Karabaş",
            "category": "cattle",  # Büyükbaş seçildi!
            "image": (dogBytes, "dog_nose.jpg"),
            "bypassQuality": "true",  # bypassQuality olsa bile tür kontrolü atlanamaz!
        },
        content_type="multipart/form-data",
    )
    assert registerRes.status_code == 422
    regJson = registerRes.get_json()
    assert regJson["success"] is False
    assert regJson["speciesMismatch"] is True
    assert regJson["detectedSpecies"] == "dog"
    assert "köpek" in regJson["message"].lower()

    # 2. Büyükbaş kategorisinde köpek ile arama denenmesi -> 422 Reddedilmeli
    searchDogBytes = io.BytesIO(bufferArray.tobytes())
    identifyRes = testClient.post(
        "/api/identify",
        data={
            "category": "cattle",
            "image": (searchDogBytes, "dog_nose.jpg"),
            "bypassQuality": "true",
        },
        content_type="multipart/form-data",
    )
    assert identifyRes.status_code == 422
    idJson = identifyRes.get_json()
    assert idJson["success"] is False
    assert idJson["speciesMismatch"] is True
    assert idJson["detectedSpecies"] == "dog"
    assert "köpek" in idJson["message"].lower()


def test_cross_species_rejection_cattle_in_stray_endpoints(testClient):
    """Sokak hayvanları kategorisinde büyükbaş sığır burnu yüklendiğinde 422 ile reddedilmesi test edilir."""
    cattleImage = np.ones((300, 400, 3), dtype=np.uint8) * 140
    cv2.ellipse(cattleImage, (120, 180), (35, 20), 0, 0, 360, (20, 20, 20), thickness=-1)
    cv2.ellipse(cattleImage, (280, 180), (35, 20), 0, 0, 360, (20, 20, 20), thickness=-1)
    noise = np.random.randint(-15, 15, (300, 400, 3), dtype=np.int16)
    noisyCattle = np.clip(cattleImage.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    encodeSuccess, bufferArray = cv2.imencode(".jpg", noisyCattle)
    assert encodeSuccess is True
    cattleBytes = io.BytesIO(bufferArray.tobytes())

    # 1. Sokak Hayvanı (Köpek) seçiliyken sığır kaydı -> 422 Reddedilmeli
    registerDogRes = testClient.post(
        "/api/register",
        data={
            "animalId": "ILLEGAL-CATTLE-001",
            "animalName": "Tosun",
            "category": "stray",
            "subType": "dog",
            "image": (cattleBytes, "cattle_muzzle.jpg"),
            "bypassQuality": "true",
        },
        content_type="multipart/form-data",
    )
    assert registerDogRes.status_code == 422
    regData = registerDogRes.get_json()
    assert regData["success"] is False
    assert regData["speciesMismatch"] is True
    assert regData["detectedSpecies"] == "cattle"
    assert "büyükbaş" in regData["message"].lower()

    # 2. Sokak Hayvanı (Kedi) seçiliyken sığır araması -> 422 Reddedilmeli
    searchCattleBytes = io.BytesIO(bufferArray.tobytes())
    identifyCatRes = testClient.post(
        "/api/identify",
        data={
            "category": "stray",
            "subType": "cat",
            "image": (searchCattleBytes, "cattle_muzzle.jpg"),
            "bypassQuality": "true",
        },
        content_type="multipart/form-data",
    )
    assert identifyCatRes.status_code == 422
    idData = identifyCatRes.get_json()
    assert idData["success"] is False
    assert idData["speciesMismatch"] is True
    assert idData["detectedSpecies"] == "cattle"
    assert "büyükbaş" in idData["message"].lower()


def test_stray_animal_geolocation_and_territory_mapping(testClient):
    """Sokak hayvanının konum koordinatları ile kaydı, tespiti, mesafe ve bölge haritası analizi test edilir."""
    # 1. Belleği temizle
    clearRes = testClient.post("/api/clear")
    assert clearRes.status_code == 200

    # 2. Köpek görseli oluştur (açık fon + merkezde burun)
    dogImage = np.ones((300, 300, 3), dtype=np.uint8) * 180
    trianglePoints = np.array([[150, 90], [90, 180], [210, 180]], np.int32)
    cv2.fillPoly(dogImage, [trianglePoints], (25, 25, 25))
    cv2.circle(dogImage, (120, 160), 12, (10, 10, 10), -1)
    cv2.circle(dogImage, (180, 160), 12, (10, 10, 10), -1)

    encodeSuccess, bufferArray = cv2.imencode(".jpg", dogImage)
    assert encodeSuccess is True
    dogBytes = io.BytesIO(bufferArray.tobytes())

    # 3. Sokak köpeğini Kadıköy Moda Parkı koordinatları ile kaydet
    modaLat = 40.9833
    modaLon = 29.0255
    registerRes = testClient.post(
        "/api/register",
        data={
            "animalId": "STRAY-DOG-001",
            "animalName": "Karabaş",
            "category": "stray",
            "subType": "dog",
            "breed": "Kangal Melezi",
            "healthStatus": "healthy",
            "latitude": str(modaLat),
            "longitude": str(modaLon),
            "locationName": "Kadıköy Moda Parkı",
            "locationAccuracy": "10.0",
            "image": (dogBytes, "stray_dog.jpg"),
            "bypassQuality": "true",
        },
        content_type="multipart/form-data",
    )
    assert registerRes.status_code == 200
    regJson = registerRes.get_json()
    assert regJson["success"] is True
    assert "sightings" in regJson
    assert len(regJson["sightings"]) == 1
    assert regJson["sightings"][0]["locationName"] == "Kadıköy Moda Parkı"
    assert "territory" in regJson
    assert regJson["territory"]["centroid"] is not None
    assert regJson["territory"]["centroid"]["latitude"] == modaLat

    # 4. Hayvanı başka bir noktadan (Kadıköy Rıhtım: 40.9910, 29.0230) kamerayla arat/tespit et
    rihtimLat = 40.9910
    rihtimLon = 29.0230
    searchDogBytes = io.BytesIO(bufferArray.tobytes())
    identifyRes = testClient.post(
        "/api/identify",
        data={
            "category": "stray",
            "subType": "dog",
            "latitude": str(rihtimLat),
            "longitude": str(rihtimLon),
            "locationName": "Kadıköy Rıhtım Meydanı",
            "locationAccuracy": "12.0",
            "image": (searchDogBytes, "query_dog.jpg"),
            "bypassQuality": "true",
        },
        content_type="multipart/form-data",
    )
    assert identifyRes.status_code == 200
    idJson = identifyRes.get_json()
    assert idJson["success"] is True
    assert idJson["isMatch"] is True
    assert idJson["matchedAnimalId"] == "STRAY-DOG-001"
    assert "territory" in idJson
    territoryData = idJson["territory"]
    assert territoryData["sightingsCount"] == 2
    assert territoryData["distanceToCentroidMeters"] is not None
    assert territoryData["distanceToLatestMeters"] is not None
    assert territoryData["distanceToCentroidMeters"] > 0.0

    # 5. Görülme geçmişi GET uç noktası doğrula
    sightingsGetRes = testClient.get("/api/animals/STRAY-DOG-001/sightings")
    assert sightingsGetRes.status_code == 200
    sightingsData = sightingsGetRes.get_json()
    assert sightingsData["success"] is True
    assert len(sightingsData["sightings"]) == 2

    # 6. Manuel görülme bildirimi POST doğrula
    sahilLat = 40.9812
    sahilLon = 29.0280
    reportRes = testClient.post(
        "/api/animals/STRAY-DOG-001/sightings",
        json={
            "latitude": sahilLat,
            "longitude": sahilLon,
            "locationName": "Moda Sahili",
            "accuracy": 8.0,
            "type": "report",
        },
    )
    assert reportRes.status_code == 200
    reportJson = reportRes.get_json()
    assert reportJson["success"] is True
    assert reportJson["territory"]["sightingsCount"] == 3

    # 7. Mahalle genel sokak haritası GET /api/stray_map uç noktasını test et
    strayMapRes = testClient.get("/api/stray_map")
    assert strayMapRes.status_code == 200
    strayMapJson = strayMapRes.get_json()
    assert strayMapJson["success"] is True
    assert strayMapJson["count"] == 1
    assert strayMapJson["animals"][0]["animalId"] == "STRAY-DOG-001"
    assert strayMapJson["animals"][0]["territory"]["sightingsCount"] == 3



