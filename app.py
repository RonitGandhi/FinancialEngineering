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


# Sentiment label mapping function
def get_sentiment_label(score):
    if score <= -0.35:
        return 'Bearish'
    elif -0.35 < score <= -0.15:
        return 'Somewhat-Bearish'
    elif -0.15 < score < 0.15:
        return 'Neutral'
    elif 0.15 <= score < 0.35:
        return 'Somewhat-Bullish'
    else:
        return 'Bullish'


# Function to process sentiment data from Alpha Vantage
def process_sentiment_data(api_key, tickers):
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={tickers}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()

    if 'feed' not in data:
        st.error("No 'feed' data found in the API response.")
        return None, None, None

    articles = []
    for item in data['feed']:
        base_article = {
            'title': item.get('title'),
            'url': item.get('url'),
            'time_published': item.get('time_published'),
            'overall_sentiment_score': item.get('overall_sentiment_score'),
            'overall_sentiment_label': get_sentiment_label(item.get('overall_sentiment_score', 0)),
            'relevance_score': item.get('relevance_score')
        }

        # Process topics
        for topic in item.get('topics', []):
            topic_name = topic.get('topic', 'Unknown')
            topic_relevance = float(topic.get('relevance_score', 0))
            base_article[f'topic_{topic_name}_relevance'] = topic_relevance
            base_article[f'topic_{topic_name}_sentiment_label'] = get_sentiment_label(topic_relevance)

        # Process ticker sentiment
        for ticker_info in item.get('ticker_sentiment', []):
            article_with_ticker = base_article.copy()
            article_with_ticker.update({
                'ticker': ticker_info.get('ticker'),
                'ticker_sentiment_score': float(ticker_info.get('ticker_sentiment_score', 0)),
                'ticker_sentiment_label': get_sentiment_label(float(ticker_info.get('ticker_sentiment_score', 0))),
                'ticker_relevance_score': float(ticker_info.get('relevance_score', 0))
            })
            articles.append(article_with_ticker)

    df = pd.DataFrame(articles)

    # Calculate ticker sentiment summary
    ticker_summary = df.groupby('ticker').agg({
        'ticker_sentiment_score': 'mean',
        'ticker_relevance_score': 'mean',
    }).reset_index()
    ticker_summary['ticker_sentiment_label'] = ticker_summary['ticker_sentiment_score'].apply(get_sentiment_label)

    # Calculate topic sentiment summary
    topic_cols = [col for col in df.columns if col.startswith('topic_') and '_relevance' in col]
    topic_summary = []
    for col in topic_cols:
        topic_name = col.split('_')[1]
        topic_data = df[[col]].rename(columns={col: 'relevance_score'})
        topic_data['sentiment_label'] = topic_data['relevance_score'].apply(get_sentiment_label)
        topic_summary.append({
            'topic': topic_name,
            'average_relevance_score': topic_data['relevance_score'].mean(),
            'overall_sentiment_label': topic_data['sentiment_label'].mode()[0]
        })
    topic_summary = pd.DataFrame(topic_summary)

    return df, ticker_summary, topic_summary


# Function to load local data
def load_data():
    return pd.read_csv('processed_data.csv')


def load_data2():
    return pd.read_csv('nasdaq_stocks_2.csv')


def load_data3():
    return pd.read_csv('final_categorized_etfs_with_risk.csv')

def load_stock_data():
    # Replace 'your_csv_file.csv' with the path to your file
    df = pd.read_csv('nasdaq_stocks_2.csv')  # Load your CSV file
    stock_column = 'Symbol'  # Replace 'Symbol' with the name of your stock column
    stock_list = df[stock_column].dropna().unique().tolist()  # Extract unique stock symbols
    return df, stock_list

# Load data and get the list of stocks
stock_data, stock_list = load_stock_data()

data = load_data()
nasdaq_data = load_data2()
etf_data = load_data3()

# Set up navigation bar
st.sidebar.title("Navigation")
nav_options = ["Investment Recommendation Tool", "Financial News Feed", "Check News Sentiment"]
nav_choice = st.sidebar.radio("Go to", nav_options)

if nav_choice == "Investment Recommendation Tool":
    st.title("Investment Recommendation Tool")

    # User inputs
    age_group = st.sidebar.selectbox('Select your age group:', data['Age Group'].unique())
    investment_horizon = st.sidebar.selectbox('Select your investment time horizon:', data['Investment Time Horizon'].unique())

    # Get recommendations
    recommendations = data[(data['Age Group'] == age_group) & (data['Investment Time Horizon'] == investment_horizon)]
    recommendations = recommendations.dropna(subset=['Allocation'])

    st.header('Your Investment Recommendations')
    if not recommendations.empty:
        recommendations = recommendations.rename(columns={'Risk Type': 'Asset Type'})
        st.table(recommendations[['Asset Type', 'Allocation']])
    else:
        st.error("No recommendations available for the selected parameters. Please adjust your inputs.")

    if st.button('Show Matching Stocks/ETFs'):
        st.header('Matching Stocks/ETFs for Each Asset Type')
        for index, row in recommendations.iterrows():
            asset_type = row['Asset Type']
            matching_stocks = nasdaq_data[nasdaq_data['AssetAllocation'] == asset_type]
            matching_etfs = etf_data[etf_data['Risk Type'] == asset_type]
            if not matching_stocks.empty or not matching_etfs.empty:
                top_stocks = matching_stocks.sort_values(by='Market Cap', ascending=False).head(5)
                st.subheader(f'Top 5 Stocks for {asset_type} by Market Cap:')
                st.table(top_stocks[['Symbol', 'Name', 'Market Cap']])

                top_etfs = matching_etfs.sort_values(by='Assets', ascending=False).head(5)
                st.subheader(f'Top 5 ETFs for {asset_type} by Market Cap:')
                st.table(top_etfs[['Symbol', 'Name', 'Assets']])
            else:
                st.write(f"No stocks/ETFs found for asset type {asset_type}")

elif nav_choice == "Financial News Feed":
    st.title("Financial News Feed")
    try:
        news_articles = fetch_financial_news(api_key)
        if news_articles:
            for article in news_articles[:10]:
                with st.container():
                    st.markdown(f"### {article.get('title', 'No Title')}")
                    st.markdown(f"{article.get('description', 'No description provided.')}")
                    st.markdown(f"[Read more...]({article.get('url', '#')})", unsafe_allow_html=True)
                    st.markdown("---")
        else:
            st.error("No news articles found.")
    except Exception as e:
        st.error(f"Failed to fetch news: {str(e)}")

elif nav_choice == "Check News Sentiment":
    st.title("Check News Sentiment")
    ticker = st.selectbox("Select a Stock Ticker:", stock_list)  # Add more tickers as needed
    if st.button("Get Sentiment Data"):
        api_key = '6TUBVQA7MI2Y0C8K'
        sentiment_data, ticker_summary, topic_summary = process_sentiment_data(api_key, ticker)
        if sentiment_data is not None:
            st.subheader("Raw Sentiment Data")
            st.write(sentiment_data)

            st.subheader("Ticker Sentiment Summary")
            st.write(ticker_summary)

            st.subheader("Topic Sentiment Summary")
            st.write(topic_summary)
