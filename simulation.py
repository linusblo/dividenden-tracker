"""
Simulations-Engine für die Portfolio-Projektion.
"""
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from config import STEUER_DEUTSCHLAND, US_QUELLENSTEUER
from marktdaten import hole_aktien_daten, hole_dividenden_historie, in_euro, von_euro
from dividenden import erkenne_rhythmus


def simuliere_portfolio(positionen_df, jahre, pauschbetrag_jahr):
    """
    Simuliert das Portfolio Woche für Woche über X Jahre.
    Gibt (events_df, end_status) zurück.
    """
    heute = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ende = heute + relativedelta(years=jahre)
    
    positionen_status = {}
    for _, pos in positionen_df.iterrows():
        daten = hole_aktien_daten(pos["ticker"])
        if daten is None or daten["kurs"] == 0:
            continue
        
        historie = hole_dividenden_historie(pos["ticker"])
        rhythmus = erkenne_rhythmus(historie) if historie is not None else None
        
        if rhythmus is None or historie is None or historie.empty:
            naechste_dividende = None
            letzte_div_pro_aktie = 0
        else:
            letztes_div_datum = historie.index[-1].to_pydatetime().replace(tzinfo=None)
            letzte_div_pro_aktie = float(historie.iloc[-1])
            naechste_dividende = letztes_div_datum + relativedelta(months=rhythmus)
            while naechste_dividende < heute:
                naechste_dividende += relativedelta(months=rhythmus)
        
        positionen_status[pos["id"]] = {
            "ticker": pos["ticker"],
            "name": daten["name"],
            "waehrung": daten["waehrung"],
            "kurs": daten["kurs"],
            "bestand": float(pos["stueckzahl"]),
            "sparrate_eur": float(pos["sparrate_betrag"]),
            "sparrate_intervall_wochen": int(pos["sparrate_intervall"]),
            "reinvest": bool(pos["reinvest_dividende"]),
            "letzte_sparrate": heute,
            "naechste_dividende": naechste_dividende,
            "dividende_pro_aktie": letzte_div_pro_aktie,
            "rhythmus_monate": rhythmus,
            "ist_usa": daten["waehrung"] == "USD",
        }
    
    pauschbetrag_rest = {heute.year: pauschbetrag_jahr}
    events = []
    aktuelle_zeit = heute
    
    while aktuelle_zeit <= ende:
        jahr = aktuelle_zeit.year
        if jahr not in pauschbetrag_rest:
            pauschbetrag_rest[jahr] = pauschbetrag_jahr
        
        for pos_id, status in positionen_status.items():
            # --- SPARRATE ---
            if status["sparrate_eur"] > 0:
                wochen_seit_letzter = (aktuelle_zeit - status["letzte_sparrate"]).days / 7
                if wochen_seit_letzter >= status["sparrate_intervall_wochen"]:
                    sparrate_original = von_euro(status["sparrate_eur"], status["waehrung"])
                    if sparrate_original and status["kurs"] > 0:
                        neue_aktien = sparrate_original / status["kurs"]
                        status["bestand"] += neue_aktien
                        status["letzte_sparrate"] = aktuelle_zeit
                        events.append({
                            "Datum": aktuelle_zeit,
                            "Ticker": status["ticker"],
                            "Typ": "Sparrate",
                            "Betrag_EUR": status["sparrate_eur"],
                            "Brutto_EUR": 0.0,
                            "Quellensteuer_EUR": 0.0,
                            "Deutsche_Steuer_EUR": 0.0,
                            "Netto_EUR": 0.0,
                            "Neue_Aktien": neue_aktien,
                            "Bestand_danach": status["bestand"],
                        })
            
            # --- DIVIDENDE ---
            if status["naechste_dividende"] and aktuelle_zeit >= status["naechste_dividende"]:
                brutto_gesamt = status["bestand"] * status["dividende_pro_aktie"]
                brutto_eur = in_euro(brutto_gesamt, status["waehrung"]) or 0
                
                quellensteuer_eur = brutto_eur * US_QUELLENSTEUER if status["ist_usa"] else 0
                
                rest = pauschbetrag_rest.get(jahr, 0)
                if brutto_eur <= rest:
                    pauschbetrag_rest[jahr] = rest - brutto_eur
                    deutsche_steuer_eur = 0
                else:
                    pauschbetrag_rest[jahr] = 0
                    zu_besteuern = brutto_eur - rest
                    deutsche_steuer_voll = zu_besteuern * STEUER_DEUTSCHLAND
                    if status["ist_usa"] and brutto_eur > 0:
                        anrechenbar = (zu_besteuern / brutto_eur) * quellensteuer_eur
                        deutsche_steuer_eur = max(0, deutsche_steuer_voll - anrechenbar)
                    else:
                        deutsche_steuer_eur = deutsche_steuer_voll
                
                netto_eur = brutto_eur - quellensteuer_eur - deutsche_steuer_eur
                
                if status["reinvest"]:
                    netto_original = von_euro(netto_eur, status["waehrung"]) or 0
                    neue_aktien_div = netto_original / status["kurs"] if status["kurs"] > 0 else 0
                    status["bestand"] += neue_aktien_div
                    typ = "Dividende (reinvestiert)"
                else:
                    neue_aktien_div = 0
                    typ = "Dividende (Cash)"
                
                events.append({
                    "Datum": status["naechste_dividende"],
                    "Ticker": status["ticker"],
                    "Typ": typ,
                    "Betrag_EUR": 0.0,
                    "Brutto_EUR": brutto_eur,
                    "Quellensteuer_EUR": quellensteuer_eur,
                    "Deutsche_Steuer_EUR": deutsche_steuer_eur,
                    "Netto_EUR": netto_eur,
                    "Neue_Aktien": neue_aktien_div,
                    "Bestand_danach": status["bestand"],
                })
                
                status["naechste_dividende"] += relativedelta(months=status["rhythmus_monate"])
        
        aktuelle_zeit += timedelta(weeks=1)
    
    spalten = ["Datum", "Ticker", "Typ", "Betrag_EUR", "Brutto_EUR",
               "Quellensteuer_EUR", "Deutsche_Steuer_EUR", "Netto_EUR",
               "Neue_Aktien", "Bestand_danach"]
    if not events:
        return pd.DataFrame(columns=spalten), positionen_status
    return pd.DataFrame(events), positionen_status