import time
import pickle
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

# Import des trainierten SVR-Modells
with open('model_svr.pkl', 'rb') as file: 
    svr_model = pickle.load(file)

# Import des MinMaxScaler
with open('min_max_scaler.pkl', 'rb') as file:
    scaler = pickle.load(file)

# Funktion zum Scrapen der OHLC-Daten von der Börsen-Website
def scrape_ohlc_data():
    url = 'https://finance.yahoo.com/quote/AAPL/history?p=AAPL'

    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        headers = {'User-Agent': user_agent}

        retries = 3  # Anzahl der Wiederholungsversuche
        for _ in range(retries):
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                break
            else:
                time.sleep(5)  # Warten Sie vor dem erneuten Versuch
        else:
            raise RequestException("Maximale Anzahl von Wiederholungsversuchen erreicht.")

        response.raise_for_status()

        page_content = response.content
        soup = BeautifulSoup(page_content, 'html.parser')
        table = soup.find_all('table')[0]
        rows = table.find_all('tr')

        # Überprüfen, ob die Tabelle Daten enthält
        if len(rows) < 2:
            raise RequestException("Die Tabelle enthält keine Daten.")

        # Hier erhalten wir den letzten Eintrag in der Tabelle
        ohlc_row = rows[1]  # Ändern Sie die Zeilennummer auf 1, um die zweite Zeile zu erhalten
        ohlc_data = ohlc_row.find_all('td')
        open_price = float(ohlc_data[1].text)
        high_price = float(ohlc_data[2].text)
        low_price = float(ohlc_data[3].text)
        close_price = float(ohlc_data[4].text)
        volume = float(ohlc_data[6].text.strip().replace(',', ''))  # Handelsvolumen aus der siebten Spalte (Index 6)

        return open_price, high_price, low_price, close_price, volume
    except RequestException as e:
        print(f"Fehler bei der HTTP-Anfrage: {e}")
        return None


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

p6 = st.number_input("Prozentuale Veränderung des NASDAQ Composite Index", step=0.01)
p7 = st.number_input("20 Tage EMA der Apple Aktie", min_value=0.00, step=0.01)

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
        st.warning("Der Schlusskurs von morgen Abend ist niedriger oder gleich hoch wie der Schlusskurs")
