"""
Zentrale Konfiguration und Konstanten.
"""
from pathlib import Path

# Datenbank
DB_PFAD = Path("portfolio.db")

# Steuer-Konstanten
STEUER_DEUTSCHLAND = 0.26375   # Abgeltungssteuer + Soli
US_QUELLENSTEUER = 0.15        # US-Quellensteuer auf Dividenden
PAUSCHBETRAG_DEFAULT = 1000.0  # Sparerpauschbetrag pro Jahr

# Sparraten-Intervalle (in Wochen)
INTERVALL_OPTIONEN = {
    1: "wöchentlich",
    2: "zweiwöchentlich",
    4: "monatlich",
}

# Farben (für Charts und Design)
FARBE_PRIMAER = "#2E86AB"     # Blau
FARBE_SEKUNDAER = "#06A77D"   # Grün
FARBE_WARNUNG = "#F18F01"     # Orange
FARBE_NEGATIV = "#C73E1D"     # Rot
FARBE_NEUTRAL = "#6C757D"     # Grau