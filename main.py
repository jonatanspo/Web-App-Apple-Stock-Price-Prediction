import time
import pickle
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

# Import the trained SVR model
@st.cache(allow_output_mutation=True)
def load_model(model_path):
    try:
        with open(model_path, 'rb') as file:
            return pickle.load(file)
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        return None

svr_model = load_model('model_svr.pkl')
scaler = load_model('min_max_scaler.pkl')

# Function to scrape the OHLC data from the stock market website
def scrape_ohlc_data():
    st.write("Scraping OHLC data...")
    url = 'https://investor.apple.com/stock-price/default.aspx'

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

        # Select the desired <span> elements through class attributes
        open_price_span = soup.find('span', class_='module-stock_open')
        high_price_span = soup.find('span', class_='module-stock_high')
        low_price_span = soup.find('span', class_='module-stock_low')
        close_price_span = soup.find('span', class_='module-stock_value')
        volume_span = soup.find('span', class_='module-stock_volume')

        # Check if <span> elements were found
        if open_price_span and high_price_span and low_price_span and close_price_span and volume_span:
            # Extract text contents and convert to desired data types
            open_price = float(open_price_span.text)
            high_price = float(high_price_span.text)
            low_price = float(low_price_span.text)
            close_price = float(close_price_span.text)
            volume = float(volume_span.text.strip().replace(',', ''))  # Remove thousands separator and convert to a floating point number
            volume *= 1_000  # Convert volume to millions

            print(open_price, high_price, low_price, close_price, volume)

            return open_price, high_price, low_price, close_price, volume
        else:
            print("Required <span> elements not found.")
            return None
    except RequestException as e:
        print(f"Error in HTTP request: {e}")
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
            raise RequestException("Table does not contain sufficient data.")

        # Here we get the last entry in the table
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
        print(f"Error in HTTP request: {e}")
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

if not svr_model or not scaler:
    st.error("Model or scaler is not loaded. Please check the file paths and formats.")
else:
    ohlc_data_new = scrape_ohlc_data()
    nasdaq = scrape_nasdaq()
    ema = scrape_ema_20()

    if ohlc_data_new and nasdaq is not None and ema is not None:
        st.success("Data successfully scraped.")
    
    # Change nasdaq and ema to lists with a single element
    nasdaq_list = [nasdaq]
    ema_list = [ema]
    
    ohlc_table = pd.DataFrame({
        "Metric": ["Open", "High", "Low", "Close", "Volume", "IXIC", "ema_20"],
        "Value": [ohlc_data_new[0], ohlc_data_new[1], ohlc_data_new[2], ohlc_data_new[3], ohlc_data_new[4], nasdaq_list[0], ema_list[0]]
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
    
    else:
        st.error("Failed to scrape one or more data sources.")
         
    if st.button("Predict"):
        
        # Apply MinMaxScaler to the input data
        input_data_scaled = scaler.transform(df)

        # Predict with the model
        pred = svr_model.predict(input_data_scaled)
        st.success("The closing price of Apple's stock tomorrow evening will be {:.2f}$".format(pred[0]))

        if pred > df["Close"].values[0]:
            st.success("According to this forecast, it makes sense to invest in Apple's stock, as tomorrow's closing price is likely to be higher than today's!")
        else:
            st.warning("Tomorrow evening's closing price is lower or equal to today's closing price.")
