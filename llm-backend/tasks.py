# app/tasks.py
import logging
from pathlib import Path
from store import store  # Explicit relative import

logger = logging.getLogger(__name__)

def run_reindex_background(folder: Path):
    logger.info("Background reindex started for: %s", folder)
    try:
        count = store.build_from_folder(folder)
        logger.info("Reindex completed. Chunks: %s", count)
    except Exception as e:
        logger.exception("Reindex failed: %s", e)
