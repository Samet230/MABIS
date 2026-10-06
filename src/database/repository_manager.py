from datetime import datetime
import json
import os
from pathlib import Path
import random
import sqlite3
import string
from typing import Any, Dict, List, Optional, Tuple

from src.utils.config import (
    DATA_DIR,
    DEFAULT_BARN_REPO_ID,
    DEFAULT_STRAY_REPO_ID,
    REPO_TYPE_PRIVATE,
    REPO_TYPE_PUBLIC,
    STORAGE_BACKEND,
    SUPABASE_KEY,
    SUPABASE_URL,
)
from src.utils.geo import CalculateHaversineDistanceMeters
from src.utils.logger import GetLogger

loggerInstance = GetLogger("RepositoryManager")

DATABASE_PATH: Path = DATA_DIR / "database" / "mabis_repositories.db"


class RepositoryManager:
    """Ayrı ahır/çiftlik depolama alanları ile ortak sokak depolarını yöneten sınıf.

    Gelecekte Supabase bulut veritabanına bağlanacak mimaride tasarlanmıştır.
    """

    def __init__(self, databasePath: Path = DATABASE_PATH) -> None:
        """Depolama yöneticisini başlatır ve şemayı hazırlar."""
        self.databasePath = Path(databasePath).resolve()
        self.databasePath.parent.mkdir(parents=True, exist_ok=True)
        self.useSupabaseBackend = bool(STORAGE_BACKEND == "supabase" and SUPABASE_URL and SUPABASE_KEY)
        self.InitializeSchema()
        self.SeedDefaultRepositories()

    def GetConnection(self) -> sqlite3.Connection:
        """Yeni bir SQLite veritabanı bağlantısı açar."""
        return sqlite3.connect(str(self.databasePath))

    def InitializeSchema(self) -> None:
        """SQLite üzerinde depo, üyelik ve yetki tablolarını oluşturur."""
        connection = self.GetConnection()
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                """
                CREATE TABLE IF NOT EXISTS repositories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    repo_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    access_code TEXT UNIQUE,
                    owner_username TEXT,
                    latitude REAL,
                    longitude REAL,
                    location_name TEXT,
                    coverage_radius_km REAL DEFAULT 25.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cursorInstance.execute(
                """
                CREATE TABLE IF NOT EXISTS repo_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id TEXT NOT NULL,
                    user_identifier TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'worker',
                    can_add INTEGER NOT NULL DEFAULT 1,
                    can_edit INTEGER NOT NULL DEFAULT 1,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (repo_id, user_identifier),
                    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
                );
                """
            )
            cursorInstance.execute("CREATE INDEX IF NOT EXISTS idx_repo_category ON repositories(category);")
            cursorInstance.execute("CREATE INDEX IF NOT EXISTS idx_repo_type ON repositories(repo_type);")
            cursorInstance.execute("CREATE INDEX IF NOT EXISTS idx_repo_access_code ON repositories(access_code);")
            cursorInstance.execute("CREATE INDEX IF NOT EXISTS idx_member_user ON repo_members(user_identifier);")
            connection.commit()
        except Exception as schemaException:
            loggerInstance.error(f"Depo şema oluşturma hatası: {schemaException}")
            raise
        finally:
            connection.close()

    def GenerateAccessCode(self, prefix: str = "AHIR") -> str:
        """Benzersiz, okunabilir 8 karakterlik depo erişim kodu üretir (Örn: AHIR-7382)."""
        allowedDigits = "23456789"
        allowedLetters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        randomNumericPart = "".join(random.choices(allowedDigits, k=4))
        randomLetterPart = "".join(random.choices(allowedLetters, k=2))
        return f"{prefix}-{randomLetterPart}{randomNumericPart}"

    def SeedDefaultRepositories(self) -> None:
        """Sistem ilk açıldığında örnek özel ahır ve bölgesel ortak sokak depolarını hazırlar."""
        try:
            # 1. Varsayılan Büyükbaş Özel Ahırı
            existingBarn = self.GetRepository(DEFAULT_BARN_REPO_ID)
            if not existingBarn:
                self.CreateRepository(
                    repoId=DEFAULT_BARN_REPO_ID,
                    repoName="Yeşil Vadi Damızlık Ahırı",
                    repoType=REPO_TYPE_PRIVATE,
                    category="cattle",
                    ownerUsername="demo_veteriner",
                    customAccessCode="AHIR-1042",
                    locationName="Ankara / Gölbaşı Çiftliği",
                    latitude=39.7915,
                    longitude=32.8085,
                )

            # 2. Bölgesel Ortak Sokak Depoları (Erişim koduna gerek olmayan havuzlar)
            defaultPublicRepos = [
                {
                    "id": "repo_stray_kadikoy",
                    "name": "Kadıköy / Moda Ortak Deposu",
                    "locationName": "İstanbul / Kadıköy",
                    "latitude": 40.9905,
                    "longitude": 29.0290,
                    "radius": 15.0,
                },
                {
                    "id": "repo_stray_besiktas",
                    "name": "Beşiktaş / Sahil Ortak Deposu",
                    "locationName": "İstanbul / Beşiktaş",
                    "latitude": 41.0422,
                    "longitude": 29.0067,
                    "radius": 15.0,
                },
                {
                    "id": "repo_stray_cankaya",
                    "name": "Çankaya / Tunalı Ortak Deposu",
                    "locationName": "Ankara / Çankaya",
                    "latitude": 39.9030,
                    "longitude": 32.8597,
                    "radius": 25.0,
                },
                {
                    "id": "repo_stray_karsiyaka",
                    "name": "Karşıyaka / Bostanlı Ortak Deposu",
                    "locationName": "İzmir / Karşıyaka",
                    "latitude": 38.4550,
                    "longitude": 27.1120,
                    "radius": 20.0,
                },
                {
                    "id": DEFAULT_STRAY_REPO_ID,
                    "name": "Genel Sokak Hayvanları Ortak Deposu",
                    "locationName": "Türkiye Genel Havuz",
                    "latitude": 39.0,
                    "longitude": 35.0,
                    "radius": 1500.0,
                },
            ]

            for publicRepoItem in defaultPublicRepos:
                if not self.GetRepository(publicRepoItem["id"]):
                    self.CreateRepository(
                        repoId=publicRepoItem["id"],
                        repoName=publicRepoItem["name"],
                        repoType=REPO_TYPE_PUBLIC,
                        category="stray",
                        ownerUsername=None,
                        customAccessCode=None,
                        locationName=publicRepoItem["locationName"],
                        latitude=publicRepoItem["latitude"],
                        longitude=publicRepoItem["longitude"],
                        coverageRadiusKm=publicRepoItem["radius"],
                    )
        except Exception as seedException:
            loggerInstance.warning(f"Varsayılan depolar tohumlanırken hata: {seedException}")

    def CreateRepository(
        self,
        repoName: str,
        repoType: str,
        category: str,
        ownerUsername: Optional[str] = None,
        customAccessCode: Optional[str] = None,
        locationName: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        coverageRadiusKm: float = 25.0,
        repoId: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Yeni bir depo (özel ahır veya ortak sokak deposu) oluşturur."""
        if not repoName or not repoName.strip():
            raise ValueError("Depo adı boş olamaz.")

        cleanName = repoName.strip()
        cleanType = repoType.strip().lower()
        cleanCategory = category.strip().lower()

        if cleanType not in (REPO_TYPE_PRIVATE, REPO_TYPE_PUBLIC):
            raise ValueError(f"Geçersiz depo tipi: {cleanType}")

        cleanRepoId = repoId or f"repo_{cleanCategory}_{int(datetime.now().timestamp())}_{random.randint(100, 999)}"

        accessCode = None
        if cleanType == REPO_TYPE_PRIVATE:
            accessCode = customAccessCode.strip().upper() if customAccessCode else self.GenerateAccessCode("AHIR")

        connection = self.GetConnection()
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                """
                INSERT INTO repositories (
                    id, name, repo_type, category, access_code, owner_username,
                    latitude, longitude, location_name, coverage_radius_km
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    cleanRepoId,
                    cleanName,
                    cleanType,
                    cleanCategory,
                    accessCode,
                    ownerUsername,
                    latitude,
                    longitude,
                    locationName,
                    coverageRadiusKm,
                ),
            )

            # Sahibi doğrudan tam yetkili üye olarak kaydet
            if ownerUsername and cleanType == REPO_TYPE_PRIVATE:
                cursorInstance.execute(
                    """
                    INSERT OR REPLACE INTO repo_members (repo_id, user_identifier, role, can_add, can_edit)
                    VALUES (?, ?, 'owner', 1, 1);
                    """,
                    (cleanRepoId, ownerUsername),
                )

            connection.commit()
            loggerInstance.info(f"Yeni depo oluşturuldu: {cleanName} ({cleanRepoId}) - Kod: {accessCode}")

            return {
                "id": cleanRepoId,
                "repoId": cleanRepoId,
                "name": cleanName,
                "repoName": cleanName,
                "repoType": cleanType,
                "category": cleanCategory,
                "accessCode": accessCode,
                "ownerUsername": ownerUsername,
                "latitude": latitude,
                "longitude": longitude,
                "locationName": locationName,
                "location": locationName,
                "coverageRadiusKm": coverageRadiusKm,
                "canAdd": True,
                "canEdit": True,
            }
        except Exception as insertException:
            loggerInstance.error(f"Depo oluşturulamadı ({cleanName}): {insertException}")
            raise
        finally:
            connection.close()

    def GetRepository(self, repoId: str) -> Optional[Dict[str, Any]]:
        """Belirtilen kimliğe sahip depoyu döndürür."""
        if not repoId:
            return None
        connection = self.GetConnection()
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                """
                SELECT id, name, repo_type, category, access_code, owner_username,
                       latitude, longitude, location_name, coverage_radius_km, created_at
                FROM repositories WHERE id = ?;
                """,
                (repoId,),
            )
            queryRow = cursorInstance.fetchone()
            if not queryRow:
                return None
            return {
                "id": queryRow[0],
                "repoId": queryRow[0],
                "name": queryRow[1],
                "repoName": queryRow[1],
                "repoType": queryRow[2],
                "category": queryRow[3],
                "accessCode": queryRow[4],
                "ownerUsername": queryRow[5],
                "latitude": queryRow[6],
                "longitude": queryRow[7],
                "locationName": queryRow[8],
                "location": queryRow[8],
                "coverageRadiusKm": queryRow[9],
                "createdAt": queryRow[10],
            }
        finally:
            connection.close()

    def GetRepositoryByAccessCode(self, accessCode: str) -> Optional[Dict[str, Any]]:
        """Erişim koduna göre özel ahır deposunu bulur."""
        if not accessCode:
            return None
        cleanCode = accessCode.strip().upper()
        connection = self.GetConnection()
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                """
                SELECT id, name, repo_type, category, access_code, owner_username,
                       latitude, longitude, location_name, coverage_radius_km, created_at
                FROM repositories WHERE access_code = ?;
                """,
                (cleanCode,),
            )
            queryRow = cursorInstance.fetchone()
            if not queryRow:
                return None
            return {
                "id": queryRow[0],
                "repoId": queryRow[0],
                "name": queryRow[1],
                "repoName": queryRow[1],
                "repoType": queryRow[2],
                "category": queryRow[3],
                "accessCode": queryRow[4],
                "ownerUsername": queryRow[5],
                "latitude": queryRow[6],
                "longitude": queryRow[7],
                "locationName": queryRow[8],
                "location": queryRow[8],
                "coverageRadiusKm": queryRow[9],
                "createdAt": queryRow[10],
            }
        finally:
            connection.close()

    def JoinRepositoryWithCode(
        self, accessCode: str, userIdentifier: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Çalışanın veya kullanıcının erişim kodu ile ahır deposuna bağlanmasını sağlar."""
        if not accessCode or not accessCode.strip():
            return False, "Lütfen geçerli bir depo erişim kodu giriniz.", None

        foundRepo = self.GetRepositoryByAccessCode(accessCode)
        if not foundRepo:
            return False, "Girilen erişim koduna ait ahır deposu bulunamadı veya kod geçersiz.", None

        cleanUser = userIdentifier.strip() if userIdentifier else "misafir_calisan"
        connection = self.GetConnection()
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                """
                INSERT OR REPLACE INTO repo_members (repo_id, user_identifier, role, can_add, can_edit)
                VALUES (?, ?, 'worker', 1, 1);
                """,
                (foundRepo["id"], cleanUser),
            )
            connection.commit()
            loggerInstance.info(f"Kullanıcı '{cleanUser}', depoya bağlandı: '{foundRepo['name']}' ({foundRepo['id']})")

            foundRepo["role"] = "worker"
            foundRepo["canAdd"] = True
            foundRepo["canEdit"] = True
            return True, f"'{foundRepo['name']}' deposuna başarıyla erişim sağlandı.", foundRepo
        except Exception as joinException:
            loggerInstance.error(f"Depoya katılma hatası: {joinException}")
            return False, f"Depoya katılırken hata oluştu: {str(joinException)}", None
        finally:
            connection.close()

    def RegenerateAccessCode(self, repoId: str, requesterUsername: str) -> Tuple[bool, str, Optional[str]]:
        """Ahır sahibi için yeni bir erişim kodu üretir."""
        repo = self.GetRepository(repoId)
        if not repo:
            return False, "Depo bulunamadı.", None

        if repo["ownerUsername"] and requesterUsername and repo["ownerUsername"] != requesterUsername:
            return False, "Yalnızca ahır sahibi erişim kodunu yenileyebilir.", None

        newCode = self.GenerateAccessCode("AHIR")
        connection = self.GetConnection()
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                "UPDATE repositories SET access_code = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (newCode, repoId),
            )
            connection.commit()
            loggerInstance.info(f"Depo erişim kodu yenilendi: ID='{repoId}', Yeni Kod='{newCode}'")
            return True, "Depo erişim kodu başarıyla yenilendi.", newCode
        except Exception as updateException:
            loggerInstance.error(f"Erişim kodu yenileme hatası: {updateException}")
            return False, f"Kod yenilenemedi: {str(updateException)}", None
        finally:
            connection.close()

    def ListPublicRepositories(
        self, userLatitude: Optional[float] = None, userLongitude: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Ortak sokak depolarını listeler ve kullanıcının konumuna göre en yakından uzağa sıralar."""
        connection = self.GetConnection()
        publicReposList: List[Dict[str, Any]] = []
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                """
                SELECT id, name, repo_type, category, owner_username,
                       latitude, longitude, location_name, coverage_radius_km
                FROM repositories
                WHERE repo_type = ?;
                """,
                (REPO_TYPE_PUBLIC,),
            )
            queryRows = cursorInstance.fetchall()

            for queryRow in queryRows:
                repoLatitude = queryRow[5]
                repoLongitude = queryRow[6]
                distanceMeters: Optional[float] = None

                if (
                    userLatitude is not None
                    and userLongitude is not None
                    and repoLatitude is not None
                    and repoLongitude is not None
                ):
                    distanceMeters = CalculateHaversineDistanceMeters(
                        userLatitude, userLongitude, float(repoLatitude), float(repoLongitude)
                    )

                publicReposList.append({
                    "id": queryRow[0],
                    "repoId": queryRow[0],
                    "name": queryRow[1],
                    "repoName": queryRow[1],
                    "repoType": queryRow[2],
                    "category": queryRow[3],
                    "ownerUsername": queryRow[4],
                    "latitude": repoLatitude,
                    "longitude": repoLongitude,
                    "locationName": queryRow[7],
                    "location": queryRow[7],
                    "coverageRadiusKm": queryRow[8],
                    "distanceMeters": round(distanceMeters, 1) if distanceMeters is not None else None,
                    "distanceKm": round(distanceMeters / 1000.0, 2) if distanceMeters is not None else None,
                    "canAdd": True,
                    "canEdit": True,
                    "requiresCode": False,
                })

            # Konum varsa en yakına göre sırala
            if userLatitude is not None and userLongitude is not None:
                publicReposList.sort(
                    key=lambda repoItem: (
                        repoItem["distanceMeters"] if repoItem["distanceMeters"] is not None else 999999999
                    )
                )
                if publicReposList:
                    publicReposList[0]["isNearest"] = True

            return publicReposList
        finally:
            connection.close()

    def ListUserRepositories(
        self,
        userIdentifier: Optional[str] = None,
        category: Optional[str] = None,
        userLatitude: Optional[float] = None,
        userLongitude: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Kullanıcının erişebildiği ahır depolarını ve ortak sokak depolarını döndürür."""
        cleanUser = userIdentifier.strip() if userIdentifier else ""
        cleanCategory = category.strip().lower() if category else None

        if cleanCategory == "stray":
            return self.ListPublicRepositories(userLatitude, userLongitude)

        connection = self.GetConnection()
        userReposList: List[Dict[str, Any]] = []
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                """
                SELECT r.id, r.name, r.repo_type, r.category, r.access_code, r.owner_username,
                       r.latitude, r.longitude, r.location_name, r.coverage_radius_km,
                       COALESCE(m.role, CASE WHEN r.owner_username = ? THEN 'owner' ELSE 'member' END) as user_role,
                       COALESCE(m.can_add, 1) as can_add,
                       COALESCE(m.can_edit, 1) as can_edit
                FROM repositories r
                LEFT JOIN repo_members m ON r.id = m.repo_id AND m.user_identifier = ?
                WHERE (r.repo_type = 'public')
                   OR (r.owner_username = ?)
                   OR (m.user_identifier = ?)
                   OR (r.id = ?);
                """,
                (cleanUser, cleanUser, cleanUser, cleanUser, DEFAULT_BARN_REPO_ID),
            )
            queryRows = cursorInstance.fetchall()

            for queryRow in queryRows:
                repoCategory = queryRow[3]
                if cleanCategory and repoCategory != cleanCategory:
                    continue

                userReposList.append({
                    "id": queryRow[0],
                    "repoId": queryRow[0],
                    "name": queryRow[1],
                    "repoName": queryRow[1],
                    "repoType": queryRow[2],
                    "category": repoCategory,
                    "accessCode": queryRow[4],
                    "ownerUsername": queryRow[5],
                    "latitude": queryRow[6],
                    "longitude": queryRow[7],
                    "locationName": queryRow[8],
                    "location": queryRow[8],
                    "coverageRadiusKm": queryRow[9],
                    "role": queryRow[10],
                    "canAdd": bool(queryRow[11]),
                    "canEdit": bool(queryRow[12]),
                    "requiresCode": bool(queryRow[2] == REPO_TYPE_PRIVATE),
                })

            return userReposList
        finally:
            connection.close()

    def CheckAccess(
        self, repoId: str, userIdentifier: Optional[str] = None, requiredPermission: str = "view"
    ) -> Tuple[bool, str]:
        """Kullanıcının belirtilen depoya erişim ve işlem yetkisini doğrular."""
        repo = self.GetRepository(repoId)
        if not repo:
            return False, "Belirtilen depo bulunamadı."

        # Ortak sokak depoları herkese açıktır
        if repo["repoType"] == REPO_TYPE_PUBLIC:
            return True, "Ortak depoya erişim izni verildi."

        # Özel ahır deposu için üyelik kontrolü
        cleanUser = userIdentifier.strip() if userIdentifier else ""
        if repo["ownerUsername"] and cleanUser and repo["ownerUsername"] == cleanUser:
            return True, "Ahır sahibi olarak tam yetki tanındı."

        connection = self.GetConnection()
        try:
            cursorInstance = connection.cursor()
            cursorInstance.execute(
                "SELECT role, can_add, can_edit FROM repo_members WHERE repo_id = ? AND user_identifier = ?;",
                (repoId, cleanUser),
            )
            membershipRow = cursorInstance.fetchone()
            if not membershipRow:
                # Varsayılan demo ahırına misafir erişimine de izin ver
                if repoId == DEFAULT_BARN_REPO_ID:
                    return True, "Varsayılan demo ahır erişimi sağlandı."
                return False, "Bu ahır deposuna erişim yetkiniz bulunmamaktadır. Lütfen ahır sahibinden 'Depo Erişim Kodu' alınız."

            canAddFlag = bool(membershipRow[1])
            canEditFlag = bool(membershipRow[2])

            if requiredPermission == "add" and not canAddFlag:
                return False, "Bu depoya yeni hayvan ekleme yetkiniz kısıtlanmıştır."
            if requiredPermission == "edit" and not canEditFlag:
                return False, "Bu depodaki hayvan bilgilerini güncelleme yetkiniz bulunmamaktadır."

            return True, "İşlem yetkisi onaylandı."
        finally:
            connection.close()


# Tekil örnek (Singleton)
repositoryManagerInstance = RepositoryManager()
