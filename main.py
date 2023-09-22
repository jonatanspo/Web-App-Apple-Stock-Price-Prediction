import time
import pickle
import pandas as pd
import streamlit as st
import requests
import plotly.graph_objects as go  # Plotly für Diagramme
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

# Import des trainierten SVR-Modells
with open('model_svr.pkl', 'rb') as file: 
    svr_model = pickle.load(file)

# Import des MinMaxScaler
with open('min_max_scaler.pkl', 'rb') as file:
    scaler = pickle.load(file)

# Funktion zum Scrapen der OHLC-Daten von der Börsen-Website
# (Code für das Scraping bleibt unverändert)

# Streamlit-Anwendung
st.title('Apple Inc. Aktienkursprognose')

# Automatisches Scraping beim Laden der App
ohlc_data_new = scrape_ohlc_data()
if ohlc_data_new:
    st.write("Gescrapte OHLC-Daten:")
    ohlc_table = pd.DataFrame({
        "Kennzahl": ["Open", "High", "Low", "Close", "Volume"],
        "Wert": ohlc_data_new
    }).set_index("Kennzahl")  # Hier setzen wir die "Kennzahl" Spalte als Index
    st.table(ohlc_table)

    # Erstellen eines DataFrame aus den gescrapten Daten
    df = pd.DataFrame({
        "Open": [ohlc_data_new[0]],
        "High": [ohlc_data_new[1]],
        "Low": [ohlc_data_new[2]],
        "Close": [ohlc_data_new[3]],
        "Volume": [ohlc_data_new[4]]
    })
else:
    st.error("Fehler beim Scraping der Daten.")

# Eingabefelder für die Prognose
st.write("### Eingabefelder für die Prognose")

# (Code für die Eingabefelder bleibt unverändert)

if st.button("Vorhersage"):
    # Füge die Benutzereingaben zu DataFrame hinzu
    df["IXIC"] = [p6]
    df["ema_20"] = [p7]

    # Anwendung des MinMaxScaler auf die eingegebenen Daten
    input_data_scaled = scaler.transform(df)

    # Vorhersage mit dem Modell
    pred = svr_model.predict(input_data_scaled)
    st.success("Der Schlusskurs der Apple Aktie wird morgen Abend {:.2f}$ betragen".format(pred[0]))

    if pred > df["Close"].values[0]:
        st.success("Laut dieser Prognose ist es sinnvoll in die Apple Aktie zu investieren, da der morgige Schlusskurs vermutlich höher ist als der heutige!")
    else:
        st.warning("Der Schlusskurs von morgen Abend ist niedriger oder gleich hoch wie der Schlusskurs von heute Abend. Daher scheint es nicht sinnvoll zu sein, in die Apple Aktie zu investieren!")

# Diagramm erstellen
st.write("### Candlestick-Chart der OHLC-Daten")

fig = go.Figure(data=[go.Candlestick(
                x=[],
                open=[],
                high=[],
                low=[],
                close=[],
                hovertext=[]
            )])

# Daten für das Candlestick-Diagramm
x = ["Open", "High", "Low", "Close"]
open_price, high_price, low_price, close_price, volume = ohlc_data_new

fig.add_trace(go.Candlestick(x=x,
                open=[open_price],
                high=[high_price],
                low=[low_price],
                close=[close_price],
                hovertext=[f"Volume: {volume}"]
            ))

fig.update_layout(
    title="Apple Inc. Candlestick Chart",
    xaxis_title="Kennzahl",
    yaxis_title="Kurs",
)

st.plotly_chart(fig)
