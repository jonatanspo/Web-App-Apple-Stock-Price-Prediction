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

# Funktion zum Scrapen der OHLC-Daten und des Volumens von der Börsen-Website
def scrape_data():
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
        
        # Extrahiere die neuesten OHLC-Daten (Zeile 1) und das Volumen (letzte Spalte)
        ohlc_row = rows[1]  # Ändern Sie die Zeilennummer auf 1, um die erste Zeile zu erhalten
        ohlc_data = ohlc_row.find_all('td')
        open_price = float(ohlc_data[1].text)
        high_price = float(ohlc_data[2].text)
        low_price = float(ohlc_data[3].text)
        close_price = float(ohlc_data[4].text)
        
        volume = float(rows[-1].find_all('td')[-1].text.replace(',', ''))  # Extrahiere das Volumen
        
        return open_price, high_price, low_price, close_price, volume
    except RequestException as e:
        print(f"Fehler bei der HTTP-Anfrage: {e}")
        return None

# Streamlit-Anwendung
st.title('Apple Inc. Aktienkursprognose')

# Automatisches Scraping beim Laden der App
ohlc_data_new = scrape_data()    
if ohlc_data_new:
    # Anzeige der gescrapten OHLC-Daten in einer Tabelle ohne Index
    st.write("Gescrapte OHLC-Daten:")
    ohlc_table = pd.DataFrame({
        "Kennzahl": ["Open", "High", "Low", "Close"],
        "Wert": ohlc_data_new[:-1]  # Das letzte Element ist das Volumen, daher entfernen wir es
    })
    st.table(ohlc_table)
    
    # Erstellen eines DataFrame aus den gescrapten OHLC-Daten und dem Volumen
    df = pd.DataFrame({
        "Open": [ohlc_data_new[0]],
        "High": [ohlc_data_new[1]],
        "Low": [ohlc_data_new[2]],
        "Close": [ohlc_data_new[3]],
        "Volume": [ohlc_data_new[4]]  # Das Volumen hinzufügen
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
        st.warning("Der Schlusskurs von morgen Abend ist niedriger oder gleich hoch wie der Schlusskurs von heute Abend. Daher scheint es nicht sinnvoll zu sein, in die Apple Aktie zu investieren!")
