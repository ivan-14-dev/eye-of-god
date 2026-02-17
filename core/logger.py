#!/usr/bin/env python3
"""
Eye of God - Logging Module
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "eye_of_god", level: int = logging.INFO) -> logging.Logger:
    """
    Configurer un logger avec fichier et console
    
    Args:
        name: Nom du logger
        level: Niveau de logging (default: INFO)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Éviter les doublons
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Dossier logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Fichier handler
    log_file = log_dir / f"eye_of_god_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Logger par défaut
logger = setup_logger()
