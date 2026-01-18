# frontend/dashboards.py
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Configuration style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)


# ==========================================
# GRAPHIQUES MATPLOTLIB/SEABORN
# ==========================================

def chart_students_per_module(df):
    """Graphique : Étudiants par module"""
    if df.empty:
        st.warning("Aucune donnée disponible")
        return

    # Limiter aux 20 modules avec le plus d'étudiants
    df_top = df.nlargest(20, 'nb_etudiants')

    fig, ax = plt.subplots(figsize=(12, 10))  # ← Augmenter la hauteur
    sns.barplot(data=df_top, x="nb_etudiants", y="module", palette="viridis", ax=ax)
    ax.set_title("📊 Top 20 modules avec le plus d'étudiants", fontsize=16, fontweight='bold')
    ax.set_xlabel("Nombre d'étudiants", fontsize=12)
    ax.set_ylabel("Module", fontsize=12)

    for container in ax.containers:
        ax.bar_label(container, fmt='%d', padding=3)

    plt.tight_layout()
    st.pyplot(fig)

    # Afficher le tableau complet en dessous
    with st.expander("📋 Voir tous les modules"):
        st.dataframe(df, use_container_width=True, height=400)


def chart_exams_per_professor(df):
    """Graphique : Examens par professeur"""
    if df.empty:
        st.warning("Aucune donnée disponible")
        return

    # Agréger par professeur
    df_agg = df.groupby('professeur')['nb_examens'].sum().reset_index()
    df_agg = df_agg.sort_values('nb_examens', ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df_agg, x="nb_examens", y="professeur", palette="coolwarm", ax=ax)
    ax.set_title("👨‍🏫 Nombre total d'examens par professeur", fontsize=16, fontweight='bold')
    ax.set_xlabel("Nombre d'examens", fontsize=12)
    ax.set_ylabel("Professeur", fontsize=12)

    for container in ax.containers:
        ax.bar_label(container, fmt='%d', padding=3)

    plt.tight_layout()
    st.pyplot(fig)


def chart_room_occupancy(df):
    """Graphique : Taux d'occupation des salles"""
    if df.empty:
        st.warning("Aucune donnée disponible")
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ['red' if x > 90 else 'orange' if x > 70 else 'green'
              for x in df['taux_occupation_pct']]

    bars = ax.barh(df['salle'], df['taux_occupation_pct'], color=colors, alpha=0.7)
    ax.set_xlabel("Taux d'occupation (%)", fontsize=12)
    ax.set_ylabel("Salle", fontsize=12)
    ax.set_title("🏫 Taux d'occupation des salles", fontsize=16, fontweight='bold')
    ax.axvline(x=100, color='red', linestyle='--', linewidth=2, label='Capacité max')
    ax.legend()

    for i, (bar, val) in enumerate(zip(bars, df['taux_occupation_pct'])):
        ax.text(val + 2, bar.get_y() + bar.get_height() / 2,
                f'{val:.1f}%', va='center', fontsize=10)

    plt.tight_layout()
    st.pyplot(fig)


# ==========================================
# GRAPHIQUES PLOTLY (INTERACTIFS)
# ==========================================

def plotly_exam_timeline(df):
    """Timeline interactive des examens"""
    if df.empty:
        st.warning("Aucune donnée disponible")
        return

    fig = px.timeline(
        df,
        x_start="date_exam",
        x_end=df["date_exam"] + pd.to_timedelta(df["duree_min"], unit='m'),
        y="salle",
        color="module",
        title="📅 Planning des examens par salle",
        labels={"date_exam": "Date", "salle": "Salle"},
        hover_data=["module", "surveillants", "nb_inscrits"]
    )

    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)


def plotly_students_per_department(df):
    """Graphique circulaire : Répartition des étudiants"""
    if df.empty:
        st.warning("Aucune donnée disponible")
        return

    dept_count = df.groupby('departement').size().reset_index(name='count')

    fig = px.pie(
        dept_count,
        values='count',
        names='departement',
        title="🎓 Répartition des étudiants par département",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)