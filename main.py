import time
import pickle
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import matplotlib.pyplot as plt

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
    
def scrape_nasdaq():
    url = 'https://finance.yahoo.com/quote/%5EIXIC/history?p=%5EIXIC'

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
        table_nasdaq = soup.find_all('table')[0]
        rows_nasdaq = table_nasdaq.find_all('tr')

        # Überprüfen, ob die Tabelle Daten enthält
        if len(rows_nasdaq) < 2:
            raise RequestException("Die Tabelle enthält keine Daten.")

        # Hier erhalten wir den letzten Eintrag in der Tabelle
        nasdaq_row_latest = rows_nasdaq[1]
        nasdaq_row_previous = rows_nasdaq[2]
        nasdaq_data_latest = nasdaq_row_latest.find_all('td')
        nasdaq_data_previous = nasdaq_row_previous.find_all('td')
        latest_close_price = float(nasdaq_data_latest[4].text)
        previous_close_price = float(nasdaq_data_previous[4].text)

        result = float(((latest_close_price - previous_close_price) / previous_close_price) * 100)

        return result
    except RequestException as e:
        print(f"Fehler bei der HTTP-Anfrage: {e}")
        return None
    
def scrape_ema_20(): 
    url = 'https://financhill.com/stock-price-chart/aapl-technical-analysis'

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
        table_ema_20 = soup.find('table',{"class":"stock-info-table"})
        rows_ema = table_ema_20.find_all('tr')

        # Hier erhalten wir den letzten Eintrag in der Tabelle
        ema_20_row = rows_ema[2]
        ema_20_data = ema_20_row.find_all('td')
        ema_20 = float(ema_20_data[0].text)

        return ema_20
    except RequestException as e:
        print(f"Fehler bei der HTTP-Anfrage: {e}")
        return None
     
# Streamlit-Anwendung
st.title('Apple Inc. Aktienkursprognose')

# Automatisches Scraping beim Laden der App
ohlc_data_new = scrape_ohlc_data()
nasdaq = scrape_nasdaq()
ema = scrape_ema_20()

if ohlc_data_new & nasdaq:
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
        "Volume": [ohlc_data_new[4]],
        "IXIC": [nasdaq],
        "ema_20": [ema],
    })

    if st.button("Vorhersage"):
        
        # Anwendung des MinMaxScaler auf die eingegebenen Daten
        input_data_scaled = scaler.transform(df)

        # Vorhersage mit dem Modell
        pred = svr_model.predict(input_data_scaled)
        st.success("Der Schlusskurs der Apple Aktie wird morgen Abend {:.2f}$ betragen".format(pred[0]))

        if pred > df["Close"].values[0]:
            st.success("Laut dieser Prognose ist es sinnvoll in die Apple Aktie zu investieren, da der morgige Schlusskurs vermutlich höher ist als der heutige!")
        else:
            st.warning("Der Schlusskurs von morgen Abend ist niedriger oder gleich hoch wie der Schlusskurs")

# Sample OHLC data (replace with your actual data)
data = {
    'Date': ['2023-09-20', '2023-09-21', '2023-09-22'],
    'Open': [175.32, 175.67, 174.67],
    'High': [177.42, 176.32, 177.08],
    'Low': [174.21, 174.21, 174.05],
    'Close': [177.01, 174.56, 174.79],
    'Volume': [60000000, 58000000, 55110610]  # Volume in millions
}

df = pd.DataFrame(data)
df['Date'] = pd.to_datetime(df['Date'])

# Create a new figure
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot the OHLC data
ax1.plot(df['Date'], df['Open'], 'g-', label='Open', linewidth=2)
ax1.plot(df['Date'], df['Close'], 'r-', label='Close', linewidth=2)
ax1.fill_between(df['Date'], df['Open'], df['Close'], where=df['Open'] > df['Close'], facecolor='red', alpha=0.3)
ax1.fill_between(df['Date'], df['Open'], df['Close'], where=df['Open'] <= df['Close'], facecolor='green', alpha=0.3)

# Add volume bars (assuming 'Volume' is in millions)
ax2 = ax1.twinx()
ax2.bar(df['Date'], df['Volume'], color='blue', alpha=0.3, width=0.2, label='Volume (Millions)')

# Customize the plot
ax1.set_xlabel('Date')
ax1.set_ylabel('Price')
ax2.set_ylabel('Volume (Millions)')
plt.title('OHLC Data with Volume')
plt.grid(True)
fig.autofmt_xdate()  # Format the date axis
fig.legend(loc='upper left', bbox_to_anchor=(0.13, 0.87))

plt.show()