"""
Dividenden-Logik: Rhythmus-Erkennung und Projektionen.
"""
from datetime import datetime
from dateutil.relativedelta import relativedelta

from marktdaten import hole_dividenden_historie


def erkenne_rhythmus(dividenden_historie):
    """Erkennt den Zahlungsrhythmus aus der Historie (1, 3, 6, 12 Monate)."""
    if dividenden_historie is None or len(dividenden_historie) < 2:
        return None
    letzte = dividenden_historie.tail(8)
    abstaende = [(letzte.index[i] - letzte.index[i-1]).days for i in range(1, len(letzte))]
    if not abstaende:
        return None
    durchschnitt = sum(abstaende) / len(abstaende)
    if durchschnitt < 45:
        return 1
    elif durchschnitt < 135:
        return 3
    elif durchschnitt < 270:
        return 6
    else:
        return 12


def rhythmus_text(monate):
    """Wandelt Monatszahl in lesbaren Text um."""
    return {1: "monatlich", 3: "quartalsweise", 6: "halbjährlich", 12: "jährlich"}.get(monate, "unbekannt")


def projiziere_dividenden(ticker, stueckzahl, monate_voraus=12):
    """Projiziert Dividendenzahlungen in die Zukunft."""
    historie = hole_dividenden_historie(ticker)
    if historie is None or historie.empty:
        return []
    rhythmus = erkenne_rhythmus(historie)
    if rhythmus is None:
        return []
    letztes_datum = historie.index[-1].to_pydatetime().replace(tzinfo=None)
    letzte_dividende_pro_aktie = float(historie.iloc[-1])
    heute = datetime.now()
    ende = heute + relativedelta(months=monate_voraus)
    projektionen = []
    naechstes_datum = letztes_datum + relativedelta(months=rhythmus)
    while naechstes_datum <= ende:
        if naechstes_datum >= heute:
            projektionen.append({
                "datum": naechstes_datum,
                "pro_aktie": letzte_dividende_pro_aktie,
                "gesamt": stueckzahl * letzte_dividende_pro_aktie,
            })
        naechstes_datum += relativedelta(months=rhythmus)
    return projektionen