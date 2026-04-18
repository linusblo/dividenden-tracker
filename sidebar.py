"""
Gemeinsame Sidebar für alle Seiten.
"""
import streamlit as st
from config import PAUSCHBETRAG_DEFAULT


def render_sidebar():
    """Rendert die globalen Einstellungen in der Sidebar."""
    # Defaults initialisieren (nur beim allerersten Aufruf der App)
    if "pauschbetrag" not in st.session_state:
        st.session_state.pauschbetrag = PAUSCHBETRAG_DEFAULT
    if "sim_jahre" not in st.session_state:
        st.session_state.sim_jahre = 10
    
    with st.sidebar:
        st.markdown("### ⚙️ Einstellungen")
        
        st.markdown("**Sparerpauschbetrag**")
        st.caption("Dein Freibetrag beim Broker (Freistellungsauftrag). 1.000 € Single, 2.000 € verheiratet.")
        st.number_input(
            "Freibetrag pro Jahr (€)",
            min_value=0.0,
            step=100.0,
            key="pauschbetrag",
        )
        
        st.divider()
        st.markdown("**Simulation**")
        st.slider(
            "Zeitraum (Jahre)", 1, 30, key="sim_jahre"
        )