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

        # Get the text of the <span> elements for stock information
        open_price = soup.find('span', text=re.compile(r"Day’s Open\s*")).find_next('span').text
        high_price = soup.find('span', text="Intraday High").find_next('span').text
        low_price = soup.find('span', text="Intraday Low").find_next('span').text
        close_price = soup.find('span', text="Closing Price").find_next('span').text
        volume = soup.find('span', text="Volume").find_next('span').text

        # Check if values were found
        if open_price and high_price and low_price and close_price and volume:
            # Convert volume to a number and adjust the units (if necessary)
            volume = float(volume.strip().replace(',', '').replace('M', '')) * 1_000_000  # Convert volume from 'M' to a number

            print(open_price, high_price, low_price, close_price, volume)

            return float(open_price), float(high_price), float(low_price), float(close_price), volume
        else:
            print("Required stock information not found.")
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
