# import requests

# key = '6TUBVQA7MI2Y0C8K'
# symbol = 'VAX'

# # Using an f-string to interpolate variables directly into the URL
# #url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={key}'
# url = f'https://www.alphavantage.co/query?function=ETF_PROFILE&symbol={symbol}&apikey={key}'

# print(url)

# r = requests.get(url)
# data = r.json()

# #print(data)


# import requests

# # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
# url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=6TUBVQA7MI2Y0C8K'
# r = requests.get(url)
# data = r.json()

# print(data)

# import requests
# import pandas as pd

# # Fetch data from Alpha Vantage API
# api_key = '6TUBVQA7MI2Y0C8K'
# url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=6TUBVQA7MI2Y0C8K'
# response = requests.get(url)
# data = response.json()

# # Check if 'feed' is in the response
# if 'feed' in data:
#     articles = []
#     for item in data['feed']:
#         base_article = {
#             'title': item.get('title'),
#             'url': item.get('url'),
#             'time_published': item.get('time_published'),
#             'authors': ", ".join(item.get('authors', [])),
#             'summary': item.get('summary'),
#             'banner_image': item.get('banner_image'),
#             'source': item.get('source'),
#             'category_within_source': item.get('category_within_source'),
#             'source_domain': item.get('source_domain'),
#             'overall_sentiment_score': item.get('overall_sentiment_score'),
#             'overall_sentiment_label': item.get('overall_sentiment_label')
#         }

#         # Flatten topics
#         for topic in item.get('topics', []):
#             base_article[f"topic_{topic.get('topic')}"] = topic.get('relevance_score')

#         # Handle ticker sentiment
#         for ticker_info in item.get('ticker_sentiment', []):
#             article_with_ticker = base_article.copy()
#             article_with_ticker.update({
#                 'ticker': ticker_info.get('ticker'),
#                 'ticker_relevance_score': ticker_info.get('relevance_score'),
#                 'ticker_sentiment_score': ticker_info.get('ticker_sentiment_score'),
#                 'ticker_sentiment_label': ticker_info.get('ticker_sentiment_label')
#             })
#             articles.append(article_with_ticker)

#     # Create DataFrame
#     df = pd.DataFrame(articles)

#     # Convert time_published to datetime
#     df['time_published'] = pd.to_datetime(df['time_published'], format='%Y%m%dT%H%M%S')

#     # Display the DataFrame
#     print(df.head())

#     # Save to CSV for further use
#     df.to_csv('news_sentiment_analysis.csv', index=False)
# else:
#     print("No 'feed' data found in the API response")



import requests
import pandas as pd

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

# Function to process API data
def process_sentiment_data(api_key, tickers):
    # Fetch data from Alpha Vantage
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={tickers}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    
    if 'feed' not in data:
        print("No 'feed' data found in the API response")
        return None
    if response.status_code != 200:
        print(f"API request failed with status code: {response.status_code}")
        return None, None, None
    if 'Note' in data:
        print("API call limit reached. Please wait and try again later.")
        return None, None, None

    # Parse articles and flatten data
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
    
    # Convert to DataFrame
    df = pd.DataFrame(articles)

    # Calculate overall sentiment scores for each ticker
    ticker_summary = df.groupby('ticker').agg({
        'ticker_sentiment_score': 'mean',
        'ticker_relevance_score': 'mean',
    }).reset_index()
    ticker_summary['ticker_sentiment_label'] = ticker_summary['ticker_sentiment_score'].apply(get_sentiment_label)

    # Calculate overall sentiment scores for each topic
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

# Example usage
api_key = '6TUBVQA7MI2Y0C8K'
tickers = 'MSFT'
raw_df, ticker_summary_df, topic_summary_df = process_sentiment_data(api_key, tickers)

# Display results
print("Raw DataFrame:")
print(raw_df.head())
print("\nTicker Summary:")
print(ticker_summary_df)
print("\nTopic Summary:")
print(topic_summary_df)

# Save the results to CSV
raw_df.to_csv('news_sentiment_raw_2.csv', index=False)
ticker_summary_df.to_csv('ticker_sentiment_summary_2.csv', index=False)
topic_summary_df.to_csv('topic_sentiment_summary_2.csv', index=False)

## API limit reached. Please wait and try again later
## 25 calls per day