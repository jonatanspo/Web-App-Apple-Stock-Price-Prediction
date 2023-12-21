import time
import pickle
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

# Import the trained SVR model
with open('model_svr.pkl', 'rb') as file:
    svr_model = pickle.load(file)

# Import the MinMaxScaler
with open('min_max_scaler.pkl', 'rb') as file:
    scaler = pickle.load(file)

def scrape_ohlc_data():
    url = 'https://finance.yahoo.com/quote/AAPL/history?p=AAPL'

    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        headers = {'User-Agent': user_agent}

        retries = 3
        for _ in range(retries):
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                break
            else:
                time.sleep(5)
        else:
            raise RequestException("Maximum number of retries reached.")

        response.raise_for_status()

        page_content = response.content
        soup = BeautifulSoup(page_content, 'html.parser')
        table = soup.find_all('table')[0]
        rows = table.find_all('tr')

        # Checking the table
        if len(rows) < 2:
            raise RequestException("The table contains no data.")

 
        ohlc_row = rows[1] 
        ohlc_data = ohlc_row.find_all('td')
        open_price = float(ohlc_data[1].text)
        high_price = float(ohlc_data[2].text)
        low_price = float(ohlc_data[3].text)
        close_price = float(ohlc_data[4].text)
        volume = float(ohlc_data[6].text.strip().replace(',', ''))

        return open_price, high_price, low_price, close_price, volume
    except RequestException as e:
        print(f"Fehler bei der HTTP-Anfrage: {e}")
        return None
    
def scrape_nasdaq():
    url = 'https://finance.yahoo.com/quote/%5EIXIC/history?p=%5EIXIC'

    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        headers = {'User-Agent': user_agent}

        retries = 3
        for _ in range(retries):
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                break
            else:
                time.sleep(5)
        else:
            raise RequestException("Maximum number of retry attempts reached.")

        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        table_nasdaq = soup.find_all('table')[0]
        rows_nasdaq = table_nasdaq.find_all('tr')

        if len(rows_nasdaq) < 3:
            raise RequestException("Table does not contain sufficient data.")

        nasdaq_data_latest = rows_nasdaq[1].find_all('td')
        nasdaq_data_previous = rows_nasdaq[2].find_all('td')

        def clean_price(price_string):
            price_string = price_string.replace(',', '').replace('--', '')
            try:
                return float(price_string)
            except ValueError:
                return None

        latest_close_price = clean_price(nasdaq_data_latest[4].text)
        previous_close_price = clean_price(nasdaq_data_previous[4].text)

        if latest_close_price is None or previous_close_price is None:
            raise ValueError("Could not convert scraped data to float.")

        result = ((latest_close_price - previous_close_price) / previous_close_price) * 100

        return result

    except RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError as e:
        print(f"Data conversion failed: {e}")
        return None

# Test the function
change_percentage = scrape_nasdaq()
if change_percentage is not None:
    print(f"Change percentage in IXIC: {change_percentage:.2f}%")
else:
    print("Error fetching data.")


def scrape_ema_20(): 
    url = 'https://financhill.com/stock-price-chart/aapl-technical-analysis'

    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        headers = {'User-Agent': user_agent}

        retries = 3  # Number of retry attempts
        for _ in range(retries):
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                break
            else:
                time.sleep(5)  # Wait before retrying
        else:
            raise RequestException("Maximum number of retry attempts reached.")

        response.raise_for_status()

        page_content = response.content
        soup = BeautifulSoup(page_content, 'html.parser')
        table_ema_20 = soup.find('table',{"class":"stock-info-table"})
        rows_ema = table_ema_20.find_all('tr')

        # Here we get the last entry in the table
        ema_20_row = rows_ema[2]
        ema_20_data = ema_20_row.find_all('td')
        ema_20 = float(ema_20_data[0].text)

        return ema_20
    except RequestException as e:
        print(f"Error in HTTP request: {e}")
        return None

# Streamlit application
st.title('Apple Inc. Stock Price Forecast')

# Automatic scraping when loading the app
ohlc_data_new = scrape_ohlc_data()
nasdaq = scrape_nasdaq()
ema = scrape_ema_20()

if ohlc_data_new:
    st.write("Scraped OHLC data:")
    
    # Change nasdaq and ema to lists with a single element
    nasdaq_list = [nasdaq]
    ema_list = [ema]
    
    ohlc_table = pd.DataFrame({
        "Metric": ["Open", "High", "Low", "Close", "Volume", "IXIC", "ema_20"],
        "Value USD": [ohlc_data_new[0], ohlc_data_new[1], ohlc_data_new[2], ohlc_data_new[3], ohlc_data_new[4], nasdaq_list[0], ema_list[0]]
    }).set_index("Metric")  # Here we set the "Metric" column as the index
    st.table(ohlc_table)

    # Create a DataFrame from the scraped data
    df = pd.DataFrame({
        "Open": [ohlc_data_new[0]],
        "High": [ohlc_data_new[1]],
        "Low": [ohlc_data_new[2]],
        "Close": [ohlc_data_new[3]],
        "Volume": [ohlc_data_new[4]],
        "IXIC": [nasdaq_list[0]],
        "ema_20": [ema_list[0]],
    })


    if st.button("Predict"):
        
        # Apply MinMaxScaler to the input data
        input_data_scaled = scaler.transform(df)

        # Predict with the model
        pred = svr_model.predict(input_data_scaled)
        st.success("The closing price of Apple's stock tomorrow evening will be {:.2f}$".format(pred[0]))

        if pred > df["Close"].values[0]:
            st.success("According to this forecast, tomorrow evening's closing price seems to be higher or equal to today's closing price")
        else:
            st.warning("Tomorrow evening's closing price seems to be lower or equal to today's closing price.")
