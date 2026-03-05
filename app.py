import streamlit as st
import json
import numpy as np
from src.visualize_environment import visualize

st.title("Multi-Agent Recovery, Organization, Network Navigation Engine")
# Layout selection
file = st.sidebar.selectbox("Seleziona Layout Mappa", ["A", "B"])
config_file = f"layouts\\{file}.json"

with open(config_file, "r") as f:
    data = json.load(f)

# Sidebar parameters
st.sidebar.header("Parametri Agenti")
vis_range = st.sidebar.slider("Raggio Visibilità", 1, 3, 2)
comm_range = st.sidebar.slider("Raggio Comunicazione", 1, 2, 1)
init_battery = st.sidebar.slider("Batteria Iniziale", 10, 500, 100)

# Simulation parameters
st.sidebar.header("Parametri Simulazione")
max_ticks = st.sidebar.radio("Durata Simulazione (ticks)", (500, 750), index=0)
sim_speed = st.sidebar.slider("Velocità Simulazione", 0.01, 1.0, 0.1)

# Map visualization
st.subheader(f"Mappa - Istanza {file} ({data['metadata']['grid_size']}x{data['metadata']['grid_size']})")
fig = visualize(data, f"output_{file}.png")
st.pyplot(fig)

# TODO: agent interaction logic