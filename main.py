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
        open_price = float(ohlc_data[1].text.replace(',', ''))
        high_price = float(ohlc_data[2].text.replace(',', ''))
        low_price = float(ohlc_data[3].text.replace(',', ''))
        close_price = float(ohlc_data[4].text.replace(',', ''))
        volume = float(ohlc_data[6].text.strip().replace(',', ''))

        return open_price, high_price, low_price, close_price, volume
    except RequestException as e:
        print(f"HTTP request error: {e}")
        return None

def scrape_nasdaq():
    url = 'https://finance.yahoo.com/quote/%5EIXIC/history?p=%5EIXIC'

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
        table_nasdaq = soup.find_all('table')[0]
        rows_nasdaq = table_nasdaq.find_all('tr')

        # Check if the table contains data
        if len(rows_nasdaq) < 3:  # The table should have at least 3 rows (Header + 2 data entries)
            raise RequestException("The table does not contain sufficient data.")

        # Get the last entry in the table
        nasdaq_row_latest = rows_nasdaq[1]
        nasdaq_row_previous = rows_nasdaq[2]
        nasdaq_data_latest = nasdaq_row_latest.find_all('td')
        nasdaq_data_previous = nasdaq_row_previous.find_all('td')
        latest_close_price_cleaned_string = nasdaq_data_latest[4].text.replace(',', '')
        latest_close_price = float(latest_close_price_cleaned_string)
        previous_close_price_cleaned_string = nasdaq_data_previous[4].text.replace(',', '')
        previous_close_price = float(previous_close_price_cleaned_string)

        # Calculate the change in IXIC
        result = ((latest_close_price - previous_close_price) / previous_close_price) * 100

        return result
    except RequestException as e:
        print(f"HTTP request error: {e}")
        return None

# Test the function
change_percentage = scrape_nasdaq()
if change_percentage is not None:
    print(f"NASDAQ change percentage: {change_percentage:.2f}%")
else:
    print("Failed to retrieve the data.")

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

        # Get the 6th row in the table (20-day EMA row)
        ema_20_row = rows_ema[6] 
        
        # Get all 'td' elements in this row
        ema_20_data = ema_20_row.find_all('td')
        
        # Get the 20-day EMA value from the first 'td' element
        ema_20_text = ema_20_data[0].text.replace(',', '').strip()
        ema_20 = float(ema_20_text)

        return ema_20
    except RequestException as e:
        print(f"HTTP request error: {e}")
        return None

# Streamlit application
st.title('Apple Inc. Stock Price Forecast')

# Automatic scraping when the app loads
ohlc_data_new = scrape_ohlc_data()
nasdaq = scrape_nasdaq()
ema = scrape_ema_20()

if ohlc_data_new:
    st.write("Scraped OHLC data:")
    
    # Change nasdaq and ema into lists with a single element
    nasdaq_list = [nasdaq]
    ema_list = [ema]
    
    ohlc_table = pd.DataFrame({
        "Metric": ["Open", "High", "Low", "Close", "Volume", "IXIC", "ema_20"],
        "Value": [ohlc_data_new[0], ohlc_data_new[1], ohlc_data_new[2], ohlc_data_new[3], ohlc_data_new[4], nasdaq_list[0], ema_list[0]]
    }).set_index("Metric")  # Here we set the "Metric" column as the index
    st.table(ohlc_table)

    # Create a DataFrame from the scraped data
    df = pd.DataFrame({
        "Opening Price USD": [ohlc_data_new[0]],
        "Highest Price USD": [ohlc_data_new[1]],
        "Lowest Price USD": [ohlc_data_new[2]],
        "Closing Price USD": [ohlc_data_new[3]],
        "Volume USD": [ohlc_data_new[4]],
        "IXIC change in %": [nasdaq_list[0]],
        "ema_20 USD": [ema_list[0]],
    })

    if st.button("Predict"):
        # Apply MinMaxScaler to the input data
        input_data_scaled = scaler.transform(df)
        print(scaler.feature_names_in_)

        # Prediction with the model
        prediction = svr_model.predict(input_data_scaled)
        st.success(f"The closing price of Apple stock is predicted to be ${prediction[0]:.2f} by the end of tomorrow.")

        if prediction > df["Close"].values[0]:
            st.success("According to this forecast, tomorrow's closing price is expected to be higher than today's!")
        else:
            st.warning("Tomorrow's evening closing price is predicted to be lower or equal to today's closing price.")
