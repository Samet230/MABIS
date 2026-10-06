-- ==============================================================================
-- ZooID (MABIS) — Supabase / PostgreSQL Veritabanı ve Güvenlik Şeması (RLS)
-- ==============================================================================
-- Bu dosya, sistemin gelecekte Supabase bulut veritabanına bağlanabilmesi için
-- gerekli tüm DDL tablolarını, indeksleri, fonksiyonları ve Row Level Security
-- (RLS) güvenlik politikalarını tanımlar.

-- 1. UUID Uzantısı
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 2. DEPOLAMA ALANLARI / REPOLAR TABLOSU (REPOSITORIES)
-- ==============================================================================
-- Büyükbaş için özel ahır depoları ('private') ve sokak hayvanları için ortak depolar ('public')
CREATE TABLE IF NOT EXISTS repositories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    repo_type TEXT NOT NULL CHECK (repo_type IN ('private', 'public')),
    category TEXT NOT NULL CHECK (category IN ('cattle', 'stray')),
    access_code TEXT UNIQUE, -- Özel ahırlar için erişim kodu (Örn: 'AHIR-1042'), ortak depolarda NULL
    owner_username TEXT,     -- Ahır sahibi kullanıcının kimliği
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location_name TEXT,
    coverage_radius_km DOUBLE PRECISION DEFAULT 25.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_repositories_category ON repositories(category);
CREATE INDEX IF NOT EXISTS idx_repositories_type ON repositories(repo_type);
CREATE INDEX IF NOT EXISTS idx_repositories_access_code ON repositories(access_code);
CREATE INDEX IF NOT EXISTS idx_repositories_owner ON repositories(owner_username);

-- ==============================================================================
-- 3. DEPO ÜYELİKLERİ VE ERİŞİM HAKLARI (REPO_MEMBERS)
-- ==============================================================================
-- Çalışanların erişim koduyla ahıra katılması ve ekleme/değiştirme yetkileri
CREATE TABLE IF NOT EXISTS repo_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id TEXT NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    user_identifier TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'worker' CHECK (role IN ('owner', 'worker', 'member')),
    can_add BOOLEAN NOT NULL DEFAULT TRUE,
    can_edit BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (repo_id, user_identifier)
);

CREATE INDEX IF NOT EXISTS idx_repo_members_user ON repo_members(user_identifier);
CREATE INDEX IF NOT EXISTS idx_repo_members_repo ON repo_members(repo_id);

-- ==============================================================================
-- 4. HAYVAN BİYOMETRİK KAYITLARI (ANIMALS)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS animals (
    id TEXT PRIMARY KEY, -- animalId (Örn: 'TR-06-89412' veya '990000012345678')
    repo_id TEXT NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('cattle', 'stray')),
    species TEXT NOT NULL CHECK (species IN ('cattle', 'dog', 'cat')),
    breed TEXT,
    gender TEXT DEFAULT 'Belirtilmedi',
    neutered TEXT DEFAULT 'Belirtilmedi',
    birth_date TEXT,
    vaccinations TEXT,
    distinctive_features TEXT,
    temperament TEXT,
    favorite_food TEXT,
    health_status TEXT NOT NULL DEFAULT 'healthy' CHECK (health_status IN ('healthy', 'sick', 'lost')),
    feature_bytes BYTEA,
    feature_shape TEXT,
    feature_dtype TEXT,
    roi_url TEXT,
    thumbnail_url TEXT,
    keypoint_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_animals_repo_id ON animals(repo_id);
CREATE INDEX IF NOT EXISTS idx_animals_species ON animals(species);
CREATE INDEX IF NOT EXISTS idx_animals_category ON animals(category);
CREATE INDEX IF NOT EXISTS idx_animals_health_status ON animals(health_status);

-- ==============================================================================
-- 5. SAHA TESPİTLERİ VE GÖRÜLME GEÇMİŞİ (ANIMAL_SIGHTINGS)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS animal_sightings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    animal_id TEXT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    repo_id TEXT NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    accuracy DOUBLE PRECISION DEFAULT 15.0,
    location_name TEXT,
    sighting_type TEXT DEFAULT 'sighting',
    confidence DOUBLE PRECISION DEFAULT 100.0,
    sighted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_animal_sightings_animal_id ON animal_sightings(animal_id);
CREATE INDEX IF NOT EXISTS idx_animal_sightings_repo_id ON animal_sightings(repo_id);

-- ==============================================================================
-- 6. ERİŞİM KODU İLE DEPOYA KATILMA VERİTABANI FONKSİYONU
-- ==============================================================================
CREATE OR REPLACE FUNCTION join_repository_with_code(
    target_access_code TEXT,
    current_username TEXT
)
RETURNS TABLE (
    success BOOLEAN,
    message TEXT,
    repo_id TEXT,
    repo_name TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    found_repo RECORD;
BEGIN
    SELECT * INTO found_repo
    FROM repositories
    WHERE access_code = UPPER(TRIM(target_access_code))
      AND repo_type = 'private';

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Geçersiz veya süresi dolmuş depo erişim kodu.'::TEXT, NULL::TEXT, NULL::TEXT;
        RETURN;
    END IF;

    -- Üyeliği ekle veya güncelle
    INSERT INTO repo_members (repo_id, user_identifier, role, can_add, can_edit)
    VALUES (found_repo.id, current_username, 'worker', TRUE, TRUE)
    ON CONFLICT (repo_id, user_identifier)
    DO UPDATE SET can_add = TRUE, can_edit = TRUE;

    RETURN QUERY SELECT TRUE, 'Depoya başarıyla bağlanıldı.'::TEXT, found_repo.id::TEXT, found_repo.name::TEXT;
END;
$$;

-- ==============================================================================
-- 7. SUPABASE ROW LEVEL SECURITY (RLS) POLİTİKALARI
-- ==============================================================================
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE repo_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE animals ENABLE ROW LEVEL SECURITY;
ALTER TABLE animal_sightings ENABLE ROW LEVEL SECURITY;

-- Ortak depolar herkese açık, özel depolar sadece sahibi veya yetkili çalışanına açık
CREATE POLICY "Public repositories are viewable by everyone"
    ON repositories FOR SELECT
    USING (repo_type = 'public' OR owner_username = auth.jwt() ->> 'email' OR EXISTS (
        SELECT 1 FROM repo_members WHERE repo_members.repo_id = repositories.id AND repo_members.user_identifier = auth.jwt() ->> 'email'
    ));

-- Hayvan kayıtları: Ortak depodakiler herkese, özel depodakiler sadece yetkililere
CREATE POLICY "Animals are viewable by authorized members"
    ON animals FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM repositories r
        WHERE r.id = animals.repo_id
          AND (r.repo_type = 'public' OR r.owner_username = auth.jwt() ->> 'email' OR EXISTS (
              SELECT 1 FROM repo_members m WHERE m.repo_id = r.id AND m.user_identifier = auth.jwt() ->> 'email'
          ))
    ));

CREATE POLICY "Animals are insertable by authorized members"
    ON animals FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM repositories r
        WHERE r.id = animals.repo_id
          AND (r.repo_type = 'public' OR r.owner_username = auth.jwt() ->> 'email' OR EXISTS (
              SELECT 1 FROM repo_members m WHERE m.repo_id = r.id AND m.user_identifier = auth.jwt() ->> 'email' AND m.can_add = TRUE
          ))
    ));

CREATE POLICY "Animals are updatable by authorized members"
    ON animals FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM repositories r
        WHERE r.id = animals.repo_id
          AND (r.repo_type = 'public' OR r.owner_username = auth.jwt() ->> 'email' OR EXISTS (
              SELECT 1 FROM repo_members m WHERE m.repo_id = r.id AND m.user_identifier = auth.jwt() ->> 'email' AND m.can_edit = TRUE
          ))
    ));
