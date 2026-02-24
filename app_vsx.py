import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuration de la page
st.set_page_config(page_title="Suivi VSX - Taux de Retour", layout="wide")

# --- GESTION DES DONNÉES (Base de données locale en CSV) ---
DB_FILE = "data_vsx_suivi.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        # Structure initiale basée sur ton plan d'action
        return pd.DataFrame(columns=[
            "Semaine", "Nouveaux_Cas_J0", "Retours_J7", 
            "RDV_Doc_Med", "Screening_Psy", "Risque_Contactees", "Rappels_HP"
        ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

df = load_data()

# --- BARRE LATÉRALE (NAVIGATION) ---
st.sidebar.title("🩺 Menu VSX")
page = st.sidebar.radio("Aller vers :", ["Tableau de Bord", "Saisie des Données", "Axe Médical", "Axe Psy/HP"])

# --- PAGE 1 : SAISIE DES DONNÉES ---
if page == "Saisie des Données":
    st.header("📥 Saisie des indicateurs hebdomadaires")
    
    with st.form("form_data"):
        col1, col2 = st.columns(2)
        with col1:
            semaine = st.selectbox("Semaine", ["Semaine 1", "Semaine 2", "Semaine 3", "Semaine 4"])
            n_cas = st.number_input("Nouveaux Cas J0 (N-1)", min_value=0, step=1)
            retours = st.number_input("Patientes revenues à J7", min_value=0, step=1)
        with col2:
            med_rdv = st.number_input("Fiches avec RDV bien documenté", min_value=0, step=1)
            psy_screen = st.number_input("Dossiers avec screening Psy", min_value=0, step=1)
            psy_contact = st.number_input("Patientes à risque contactées", min_value=0, step=1)
            hp_rappel = st.number_input("Patientes rappelées par HP", min_value=0, step=1)
        
        submitted = st.form_submit_button("Enregistrer les données")
        
        if submitted:
            # Mise à jour ou ajout de la ligne
            new_row = {
                "Semaine": semaine, "Nouveaux_Cas_J0": n_cas, "Retours_J7": retours,
                "RDV_Doc_Med": med_rdv, "Screening_Psy": psy_screen, 
                "Risque_Contactees": psy_contact, "Rappels_HP": hp_rappel
            }
            df = df[df.Semaine != semaine] # Évite les doublons
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success(f"Données de la {semaine} enregistrées !")

    st.write("---")
    st.subheader("Données brutes")
    st.dataframe(df)

# --- PAGE 2 : TABLEAU DE BORD (GLOBAL) ---
elif page == "Tableau de Bord":
    st.header("📊 Tableau de Bord de Performance VSX")
    
    if df.empty:
        st.warning("Aucune donnée disponible. Allez dans 'Saisie des Données'.")
    else:
        # Calculs
        df['Taux_Retour'] = (df['Retours_J7'] / df['Nouveaux_Cas_J0'] * 100).fillna(0)
        latest_rate = df['Taux_Retour'].iloc[-1]
        
        # Indicateurs clés (KPI)
        m1, m2, m3 = st.columns(3)
        m1.metric("Taux de Retour Actuel", f"{latest_rate:.1f}%", delta=f"{latest_rate - 52:.1f}% vs Baseline")
        
        target = 70
        status = "🔴 Alerte" if latest_rate < 60 else "🟠 Moyen" if latest_rate < 70 else "🟢 Objectif Atteint"
        m2.metric("Statut Performance", status)
        m3.metric("Baseline Initiale", "52%")

        # Graphique de tendance
        st.subheader("Évolution du Taux de Retour (%)")
        fig = px.line(df, x="Semaine", y="Taux_Retour", markers=True, 
                      range_y=[0, 100], title="Cible : 70%")
        fig.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="Objectif")
        st.plotly_chart(fig, use_container_width=True)

# --- PAGES AXES SPÉCIFIQUES ---
else:
    st.header(f"🔍 Analyse : {page}")
    if not df.empty:
        if "Médical" in page:
            df['%_RDV'] = (df['RDV_Doc_Med'] / df['Nouveaux_Cas_J0'] * 100).fillna(0)
            st.write("Indicateur : % fiches avec rendez-vous documenté correctement")
            st.bar_chart(df.set_index("Semaine")['%_RDV'])
        else:
            df['%_Psy'] = (df['Screening_Psy'] / df['Nouveaux_Cas_J0'] * 100).fillna(0)
            df['%_HP'] = (df['Rappels_HP'] / df['Nouveaux_Cas_J0'] * 100).fillna(0)
            st.write("Performance Screening Psychosocial et Rappels HP")
            st.line_chart(df.set_index("Semaine")[['%_Psy', '%_HP']])

# Export Excel
st.sidebar.write("---")
if st.sidebar.button("Exporter vers Excel"):
    df.to_excel("Export_VSX.xlsx", index=False)
    st.sidebar.success("Fichier 'Export_VSX.xlsx' créé !")