import io
import cv2
import numpy as np
import pytest

from src.database.repository_manager import (
    DEFAULT_BARN_REPO_ID,
    DEFAULT_STRAY_REPO_ID,
    REPO_TYPE_PRIVATE,
    REPO_TYPE_PUBLIC,
    RepositoryManager,
    repositoryManagerInstance,
)
from src.web.app import app


@pytest.fixture
def webTestClient():
    """Web test istemcisi fixture'ı."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def CreateTestDummyJpg(width: int = 240, height: int = 240) -> io.BytesIO:
    """Sentetik test görseli üretir."""
    syntheticImage = np.random.randint(70, 210, (height, width, 3), dtype=np.uint8)
    cv2.circle(syntheticImage, (width // 2, height // 2), 35, (255, 255, 255), thickness=-1)
    encodeSuccess, bufferArray = cv2.imencode(".jpg", syntheticImage)
    assert encodeSuccess is True
    return io.BytesIO(bufferArray.tobytes())


def test_private_barn_creation_and_access_code():
    """Özel ahır deposu oluşturma ve benzersiz erişim kodu üretimi test edilir."""
    manager = RepositoryManager()
    createdRepo = manager.CreateRepository(
        repoName="Anadolu Besi Çiftliği",
        repoType=REPO_TYPE_PRIVATE,
        category="cattle",
        ownerUsername="ciftlik_sahibi_kemal",
        locationName="Konya / Karatay",
    )

    assert createdRepo["name"] == "Anadolu Besi Çiftliği"
    assert createdRepo["repoType"] == "private"
    assert createdRepo["accessCode"] is not None
    assert createdRepo["accessCode"].startswith("AHIR-")
    assert createdRepo["ownerUsername"] == "ciftlik_sahibi_kemal"

    # Sahip doğrudan tam yetkili olmalı
    hasAccess, _ = manager.CheckAccess(createdRepo["id"], "ciftlik_sahibi_kemal", "add")
    assert hasAccess is True


def test_worker_join_repository_with_code():
    """Çalışanın erişim kodu girerek ahır deposuna bağlanması test edilir."""
    manager = RepositoryManager()
    barn = manager.CreateRepository(
        repoName="Toros Yaylası Çiftliği",
        repoType=REPO_TYPE_PRIVATE,
        category="cattle",
        ownerUsername="mehmet_aga",
    )
    accessCode = barn["accessCode"]

    # Yetkisiz çalışan önce erişememeli
    hasAccessBefore, _ = manager.CheckAccess(barn["id"], "calisan_hasan", "view")
    assert hasAccessBefore is False

    # Kod ile bağlanma
    isJoined, message, joinedRepo = manager.JoinRepositoryWithCode(accessCode, "calisan_hasan")
    assert isJoined is True
    assert joinedRepo["id"] == barn["id"]
    assert joinedRepo["role"] == "worker"
    assert joinedRepo["canAdd"] is True
    assert joinedRepo["canEdit"] is True

    # Artık ekleme ve düzenleme yetkisine sahip olmalı
    hasAccessView, _ = manager.CheckAccess(barn["id"], "calisan_hasan", "view")
    hasAccessAdd, _ = manager.CheckAccess(barn["id"], "calisan_hasan", "add")
    hasAccessEdit, _ = manager.CheckAccess(barn["id"], "calisan_hasan", "edit")
    assert hasAccessView is True
    assert hasAccessAdd is True
    assert hasAccessEdit is True

    # Yanlış kodla giriş reddedilmeli
    isFailed, _, _ = manager.JoinRepositoryWithCode("HATALI-9999", "yabanci_kisi")
    assert isFailed is False


def test_regenerate_barn_access_code():
    """Ahır sahibinin erişim kodunu yenileyebilmesi, yabancının yenileyememesi test edilir."""
    manager = RepositoryManager()
    barn = manager.CreateRepository(
        repoName="Ege Damızlık",
        repoType=REPO_TYPE_PRIVATE,
        category="cattle",
        ownerUsername="sahip_fatma",
    )
    oldCode = barn["accessCode"]

    # Başkası yenileyemez
    isDenied, _, _ = manager.RegenerateAccessCode(barn["id"], "baska_kullanici")
    assert isDenied is False

    # Sahibi yenileyebilir
    isSuccess, _, newCode = manager.RegenerateAccessCode(barn["id"], "sahip_fatma")
    assert isSuccess is True
    assert newCode != oldCode
    assert newCode.startswith("AHIR-")


def test_public_stray_repositories_proximity_sorting():
    """Sokak hayvanları için ortak depoların kodsuz listelenmesi ve lokasyona göre sıralanması test edilir."""
    manager = RepositoryManager()
    # Kadıköy koordinatları (40.9905, 29.0290)
    userLatitude = 40.9910
    userLongitude = 29.0285

    publicRepos = manager.ListPublicRepositories(userLatitude, userLongitude)
    assert len(publicRepos) >= 4
    # En yakın depo Kadıköy / Moda Ortak Deposu olmalıdır
    nearest = publicRepos[0]
    assert "Kadıköy" in nearest["name"]
    assert nearest["isNearest"] is True
    assert nearest["requiresCode"] is False
    assert nearest["distanceMeters"] is not None
    assert nearest["distanceMeters"] < 1000.0  # 1 km'den yakın


def test_api_repository_endpoints_flow(webTestClient):
    """Web API uç noktalarında depo oluşturma, katılma ve hayvan izolasyonu akışı test edilir."""
    # 1. Ahır deposu oluştur (POST /api/repositories/create)
    createRes = webTestClient.post(
        "/api/repositories/create",
        json={"name": "Kafkas Süt Çiftliği", "category": "cattle", "locationName": "Kars"},
        headers={"X-User-Id": "ciftlik_sahibi_selim"},
    )
    assert createRes.status_code == 200
    createData = createRes.get_json()
    assert createData["success"] is True
    repoInfo = createData["repository"]
    repoId = repoInfo["id"]
    accessCode = repoInfo["accessCode"]

    # 2. Çalışan bu koda katılır (POST /api/repositories/join)
    joinRes = webTestClient.post(
        "/api/repositories/join",
        json={"accessCode": accessCode},
        headers={"X-User-Id": "calisan_murat"},
    )
    assert joinRes.status_code == 200
    joinData = joinRes.get_json()
    assert joinData["success"] is True
    assert joinData["repository"]["id"] == repoId

    # 3. Yetkili çalışan bu depoya bir sığır kaydeder (POST /api/register)
    imageBytes = CreateTestDummyJpg()
    regRes = webTestClient.post(
        "/api/register",
        data={
            "animalId": "TR-36-KARS-001",
            "animalName": "Zümrüt",
            "category": "cattle",
            "repoId": repoId,
            "bypassQuality": "true",
            "image": (imageBytes, "cow.jpg"),
        },
        headers={"X-User-Id": "calisan_murat"},
        content_type="multipart/form-data",
    )
    assert regRes.status_code == 200
    regData = regRes.get_json()
    assert regData["success"] is True
    assert regData["repoId"] == repoId

    # 4. Bu depodaki hayvanları listele (GET /api/animals?repoId=...)
    listRes = webTestClient.get(
        f"/api/animals?repoId={repoId}",
        headers={"X-User-Id": "calisan_murat"},
    )
    assert listRes.status_code == 200
    listData = listRes.get_json()
    assert listData["success"] is True
    assert listData["count"] == 1
    assert listData["animals"][0]["animalId"] == "TR-36-KARS-001"

    # 5. Yetkisiz yabancı kullanıcı bu özel depodaki hayvanları göremez (403 dönmeli)
    unauthorizedListRes = webTestClient.get(
        f"/api/animals?repoId={repoId}",
        headers={"X-User-Id": "yabanci_kullanici_ali"},
    )
    assert unauthorizedListRes.status_code == 403

    # 6. Ortak sokak depoları listesini al (GET /api/repositories?category=stray)
    strayReposRes = webTestClient.get("/api/repositories?category=stray&latitude=40.99&longitude=29.02")
    assert strayReposRes.status_code == 200
    strayReposData = strayReposRes.get_json()
    assert strayReposData["success"] is True
    assert strayReposData["repoType"] == "public"
    assert strayReposData["requiresCode"] is False
    assert len(strayReposData["repositories"]) >= 3
