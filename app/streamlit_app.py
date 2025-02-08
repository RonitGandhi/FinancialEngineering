
import streamlit as st
import pandas as pd


import requests

def fetch_financial_news(api_key):
    url = 'https://newsapi.org/v2/everything'
    parameters = {
        'q': 'NASDAQ OR "Dow Jones" OR "S&P 500"',  # Using OR to combine queries
        'domains': 'bloomberg.com,ft.com,cnbc.com',  # Focusing on specific financial news domains
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': api_key
    }

    response = requests.get(url, params=parameters)
    data = response.json()

    if response.status_code == 200:
        return data['articles']
    else:
        return "Failed to fetch news: " + data.get('message', 'No error message provided')

# Example usage
api_key = 'c27c7825d1f34093804ceab847772901'


# Function to load data
def load_data():
    return pd.read_csv('/Users/ronitgandhi/Desktop_windows/Full Stack ML Project/processed_data.csv')

def load_data2():
    return pd.read_csv('/Users/ronitgandhi/Desktop_windows/Full Stack ML Project/nasdaq_stocks_2.csv')

def load_data3():
    return pd.read_csv('/Users/ronitgandhi/Desktop_windows/Full Stack ML Project/final_categorized_etfs_with_risk.csv')

# Load the processed data
data = load_data()
nasdaq_data = load_data2()
etf_data = load_data3()

# Setting up the Streamlit app
st.title('Investment Recommendation Tool')

# User inputs in the sidebar
age_group = st.sidebar.selectbox('Select your age group:', data['Age Group'].unique())
investment_horizon = st.sidebar.selectbox('Select your investment time horizon:', data['Investment Time Horizon'].unique())

# Function to filter data based on user input
def get_recommendations(data, age_group, investment_horizon):
    recommendations = data[(data['Age Group'] == age_group) &
                           (data['Investment Time Horizon'] == investment_horizon)]
    # Filter out rows where the allocation is NaN or non-existent
    recommendations = recommendations.dropna(subset=['Allocation'])
    return recommendations

# Fetch recommendations
recommendations = get_recommendations(data, age_group, investment_horizon)

# Displaying recommendations
st.header('Your Investment Recommendations')
if not recommendations.empty:
    st.write('Based on your age and investment time horizon, here are your recommended asset allocations for each asset type:')
    # Rename column for display
    recommendations = recommendations.rename(columns={'Risk Type': 'Asset Type'})
    st.table(recommendations[['Asset Type', 'Allocation']])
else:
    st.error('No recommendations available for the selected parameters. Please adjust your inputs.')


if st.button('Show Matching Stocks/ETFs'):
    st.header('Matching Stocks/ETFs for Each Asset Type')
    for index, row in recommendations.iterrows():
        asset_type = row['Asset Type']
        matching_stocks = nasdaq_data[nasdaq_data['AssetAllocation'] == asset_type]  # Assuming 'AssetAllocation' matches 'Asset Type'
        matching_etfs = etf_data[etf_data['Risk Type'] == asset_type]
        if not matching_stocks.empty or not matching_etfs.empty:
            # Sort by 'Market Cap' in descending order and pick top 5
            top_stocks = matching_stocks.sort_values(by='Market Cap', ascending=False).head(5)
            st.subheader(f'Top 5 Stocks for {asset_type} by Market Cap:')
            st.table(top_stocks[['Symbol', 'Name', 'Market Cap']])

            top_etfs = matching_etfs.sort_values(by='Assets', ascending=False).head(5)
            st.subheader(f'Top 5 ETFs for {asset_type} by Market Cap:')
            st.table(top_etfs[['Symbol', 'Name', 'Assets']])
        else:
            st.write(f'No stocks/ETFs found for asset type {asset_type}')


# Save this script as app.py and run it using Streamlit by the command: streamlit run app.py
import streamlit as st

st.title('Financial News Feed')

def display_news_articles(news_articles):
    if not news_articles:
        st.error("No news articles found.")
        return
    
    # Use Markdown and custom styling for better presentation
    for article in news_articles[:10]:  # Display only the first 10 articles
        try:
            # Each article block
            with st.container():
                st.markdown(f"### {article.get('title', 'No Title')}")
                st.markdown(f"{article.get('description', 'No description provided.')}")
                st.markdown(f"[Read more...]({article.get('url', '#')})", unsafe_allow_html=True)
                st.markdown("---")  # Horizontal line for separation
        except Exception as e:
            st.error(f"Failed to display article: {str(e)}")

try:
    news_articles = fetch_financial_news(api_key)
    display_news_articles(news_articles)
except Exception as e:
    st.error("Failed to fetch news: " + str(e))
