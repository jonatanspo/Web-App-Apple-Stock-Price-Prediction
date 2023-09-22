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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, timeout=10)  # Timeout auf 10 Sekunden gesetzt
        response.raise_for_status()  # Wir überprüfen, ob die Anfrage erfolgreich war
        page_content = response.content
        soup = BeautifulSoup(page_content, 'html.parser')
        table = soup.find_all('table')[0]
        rows = table.find_all('tr')
        ohlc_row = rows[2]
        ohlc_data = ohlc_row.find_all('td')
        open_price = float(ohlc_data[1].text)
        high_price = float(ohlc_data[2].text)
        low_price = float(ohlc_data[3].text)
        close_price = float(ohlc_data[4].text)
        return open_price, high_price, low_price, close_price
    except RequestException as e:
        st.error(f"Fehler bei der HTTP-Anfrage: {e}")
        return None

# Streamlit-Anwendung
st.title('Apple Inc. Aktienkursprognose')

# Automatisches Scraping beim Laden der App
st.write("Scraping der Daten...")
ohlc_data_new = scrape_ohlc_data()    
if ohlc_data_new:
    st.write("Scraping abgeschlossen!")
    st.write("Bereit für die Prognose.")        
    # Anzeige der gescrapten Daten oben auf der Seite
    st.write("Gescrapte OHLC-Daten:")
    st.write("Open: {:.2f}".format(ohlc_data_new[0]))
    st.write("High: {:.2f}".format(ohlc_data_new[1]))
    st.write("Low: {:.2f}".format(ohlc_data_new[2]))
    st.write("Close: {:.2f}".format(ohlc_data_new[3]))
    
    # Erstellen eines DataFrame aus den gescrapten Daten
    df = pd.DataFrame({
        "Open": [ohlc_data_new[0]],
        "High": [ohlc_data_new[1]],
        "Low": [ohlc_data_new[2]],
        "Close": [ohlc_data_new[3]],
    })
else:
    st.error("Fehler beim Scraping der Daten.")

# Eingabefelder für die Prognose
st.write("### Eingabefelder für die Prognose")

p5 = st.number_input("Handelsvolumen heute ($)", min_value=0)
p6 = st.number_input("Prozentuale Veränderung des NASDAQ Composite Index", step=0.01)
p7 = st.number_input("20 Tage EMA der Apple Aktie", min_value=0.00, step=0.01)

if st.button("Vorhersage"):
    # Füge die Benutzereingaben zu DataFrame hinzu
    df["Volume"] = [p5]
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
