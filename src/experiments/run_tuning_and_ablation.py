from pathlib import Path
import time
from typing import Dict

from src.data.benchmark_generator import BiometricBenchmarkGenerator
from src.data.split_data import DatasetSplitter
from src.experiments.ablation import AblationExperiment
from src.experiments.parameter_tuning import ParameterTuner
from src.utils.config import FIGURES_DIR, SPLITS_DIR, TABLES_DIR, VALID_SPECIES
from src.utils.logger import GetLogger

loggerInstance = GetLogger("ExperimentRunner")


def RunFullTuningAndAblationPipeline() -> Dict[str, Dict]:
    """1. Benchmark Veri Seti Üretir, 2. Train/Test Bölümler, 3. Parametre İnce Ayarı Yapar, 4. Ablation Çalıştırır."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    overallExecutionSummary: Dict[str, Dict] = {}

    # Adım 1: Benchmark Veri Setini Üret
    print("\n========================================================")
    print("  ADIM 1: ÇOK KOŞULLU BİYOMETRİK BENCHMARK VERİSİ HAZIRLANIYOR")
    print("========================================================")
    generator = BiometricBenchmarkGenerator()
    generationStats = generator.GenerateBenchmarkDataset(
        animalsPerSpecies=10,
        imagesPerAnimal=6,
    )
    print(
        f"[TAMAMLANDI] {generationStats['totalAnimals']} birey, "
        f"{generationStats['totalImages']} görüntü data/raw altına yerleştirildi."
    )

    # Adım 2: Kapalı-Küme Bölümlemeleri Oluştur
    print("\n========================================================")
    print("  ADIM 2: KAPALI-KÜME (CLOSED-SET) %75 GALERİ - %25 TEST AYRIMI")
    print("========================================================")
    splitter = DatasetSplitter()
    speciesSplits: Dict[str, Path] = {}

    for speciesName in VALID_SPECIES:
        generatedPaths = splitter.GenerateMultiSeedSplits(
            speciesName=speciesName,
            seedList=(42, 100, 2024),
            trainRatio=0.75,
        )
        speciesSplits[speciesName] = generatedPaths[0]  # Seed 42 varsayılan
        print(f"[TAMAMLANDI] '{speciesName}' için 3 tohumlu ayrım dosyaları üretildi.")

    # Adım 3: Hiperparametre İnce Ayarı (Grid Search)
    print("\n========================================================")
    print("  ADIM 3: SİSTEMATİK HİPERPARAMETRE İNCE AYARI (GRID SEARCH)")
    print("========================================================")
    tuner = ParameterTuner()
    bestConfigurations: Dict[str, Dict] = {}

    for speciesName in VALID_SPECIES:
        splitMetadata = DatasetSplitter.LoadSplit(speciesSplits[speciesName])
        tuningOutput = tuner.RunGridSearch(splitMetadata=splitMetadata)
        bestConfig = tuningOutput["bestConfiguration"]
        bestConfigurations[speciesName] = bestConfig

        print(
            f"\n>>> '{speciesName.upper()}' İçin En İyi Konfigürasyon: "
            f"{bestConfig['configName']} (Rank-1: %{bestConfig['rank1Accuracy'] * 100.0:.2f}, "
            f"F1: {bestConfig['f1Macro']:.4f}, Süre: {bestConfig['durationSeconds']}s)"
        )

    # Adım 4: Yöntem Karşılaştırmalı Ablation Deneyleri
    print("\n========================================================")
    print("  ADIM 4: YÖNTEM KARŞILAŞTIRMA (ABLATION STUDY) DENEYLERİ")
    print("========================================================")
    ablationEngine = AblationExperiment()
    ablationSummaryPerSpecies: Dict[str, Dict] = {}

    for speciesName in VALID_SPECIES:
        splitMetadata = DatasetSplitter.LoadSplit(speciesSplits[speciesName])
        outputPlotName = f"ablation_comparison_{speciesName}.png"
        ablationResults = ablationEngine.RunAblationOnSplit(
            splitMetadata=splitMetadata,
            outputPlotName=outputPlotName,
        )
        ablationSummaryPerSpecies[speciesName] = ablationResults

        print(f"\n>>> '{speciesName.upper()}' Ablation Sonuçları:")
        for methodName, methodStats in ablationResults.items():
            print(
                f"   - {methodName:<12}: Rank-1 = %{methodStats['rank1Accuracy'] * 100.0:.2f} | "
                f"F1 = {methodStats['f1Macro']:.4f} | Süre = {methodStats['durationSeconds']}s"
            )

    print("\n========================================================")
    print("  TÜM DENEYLER VE OPTİMİZASYONLAR BAŞARIYLA TAMAMLANDI!")
    print(f"  Grafikler : results/figures/")
    print(f"  Tablolar  : results/tables/")
    print("========================================================\n")

    overallExecutionSummary = {
        "generation": generationStats,
        "bestConfigurations": bestConfigurations,
        "ablationSummary": ablationSummaryPerSpecies,
    }
    return overallExecutionSummary


if __name__ == "__main__":
    RunFullTuningAndAblationPipeline()
