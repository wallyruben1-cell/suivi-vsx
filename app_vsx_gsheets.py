import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Suivi VSX - Cloud Edition", layout="wide")

st.title("🩺 Système de Suivi VSX (Google Sheets)")

# --- CONNEXION À GOOGLE SHEETS ---
# Note : L'URL de votre Google Sheet devra être configurée dans Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl="10m") # Cache de 10 minutes

# Chargement initial
df = load_data()

# --- BARRE LATÉRALE ---
page = st.sidebar.radio("Navigation", ["Tableau de Bord", "Saisie des Données"])

# --- PAGE SAISIE ---
if page == "Saisie des Données":
    st.header("📥 Saisie hebdomadaire")
    
    with st.form("form_vsx"):
        semaine = st.selectbox("Semaine de suivi", ["Semaine 1", "Semaine 2", "Semaine 3", "Semaine 4"])
        c1, c2 = st.columns(2)
        with c1:
            n_cas = st.number_input("Nouveaux Cas J0", min_value=0)
            retours = st.number_input("Retours à J7", min_value=0)
        with c2:
            med = st.number_input("RDV Médical Doc.", min_value=0)
            psy = st.number_input("Screening Psychosocial", min_value=0)
            
        submit = st.form_submit_button("Envoyer vers Google Sheets")
        
        if submit:
            # Création de la nouvelle ligne
            new_data = pd.DataFrame([{
                "Semaine": semaine,
                "Nouveaux_Cas_J0": n_cas,
                "Retours_J7": retours,
                "RDV_Doc_Med": med,
                "Screening_Psy": psy
            }])
            
            # Mise à jour (on ajoute à la suite ou on remplace)
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Données synchronisées avec Google Sheets !")
            st.balloons()

# --- PAGE DASHBOARD ---
else:
    if df.empty or len(df) == 0:
        st.info("En attente de données...")
    else:
        # Calcul du taux de retour
        df['Taux_Retour'] = (df['Retours_J7'] / df['Nouveaux_Cas_J0'] * 100).fillna(0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Taux de retour moyen", f"{df['Taux_Retour'].mean():.1f}%")
        with col2:
            st.write("Dernière mise à jour effectuée.")

        fig = px.bar(df, x="Semaine", y="Taux_Retour", color="Taux_Retour",
                     color_continuous_scale=['red', 'orange', 'green'],
                     range_y=[0, 100], title="Performance Hebdomadaire")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Données enregistrées")
        st.table(df)