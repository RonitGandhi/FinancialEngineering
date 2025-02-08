import requests
from bs4 import BeautifulSoup
import pandas as pd
# URL of the page to scrape
url = "https://finance.yahoo.com/topic/stock-market-news/"

# Send HTTP request to the URL
response = requests.get(url)
# Check if the request was successful
if response.status_code == 200:
    html_content = response.text
else:
    print("Failed to retrieve the webpage")
    html_content = None

def parse_html(html_content):
    # Create a BeautifulSoup object
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all <a> tags where the articles are located
    articles = soup.find_all('div', class_='content yf-18q3fnf')
    # List to hold the news data
    news_list = []
    for article in articles:
        headers = article.find_all('h3')
        paragraphs = article.find_all('p')
        links = article.find('a',class_='subtle-link fin-size-small titles noUnderline yf-1xqzjha')
        link = links.get('href', '#')

        print("Link:" ,link)
        print("Header:", headers[0].text)
        print("Paragraph:", paragraphs[0].text)
        # Append the title and link to the news list
        news_list.append({'title': headers[0].text, 'link': f"{link}", 'description': paragraphs[0].text})

    return news_list


# Parse the fetched HTML content
news_articles = parse_html(html_content)

df = pd.DataFrame(news_articles)

# Export to CSV
print(df)
df.to_csv('news_articles.csv', index=False)

print("Exported news articles to CSV successfully.")