import logging
import sys
from pathlib import Path
from src.utils.config import LOGS_DIR

# Loglayıcı önbelleği
LOGGER_NAME_DEFAULT: str = "ZooID"

def GetLogger(loggerName: str = LOGGER_NAME_DEFAULT) -> logging.Logger:
    """Belirtilen isimde yapılandırılmış loglayıcı örneği döndürür.

    Args:
        loggerName: Loglayıcının adı.

    Returns:
        logging.Logger: Konsol ve dosya çıktılarına sahip loglayıcı.
    """
    configuredLogger = logging.getLogger(loggerName)
    if configuredLogger.handlers:
        return configuredLogger

    configuredLogger.setLevel(logging.INFO)
    logFormatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Konsol işleyicisi (stdout)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    configuredLogger.addHandler(consoleHandler)

    # Dosya işleyicisi
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        fileHandler = logging.FileHandler(LOGS_DIR / "zooid.log", encoding="utf-8")
        fileHandler.setFormatter(logFormatter)
        configuredLogger.addHandler(fileHandler)
    except Exception as logException:
        configuredLogger.warning(f"Dosya loglayıcı başlatılamadı: {logException}")

    return configuredLogger
