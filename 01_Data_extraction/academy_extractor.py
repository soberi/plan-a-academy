import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def get_content(url):
    '''input url to get html elements'''
    
    html = requests.get(url).content
    return html


def make_soup(html):
    '''Using BeautifulSoup to extract relevant html elements'''
    tags = ['p', 'h2', 'h3']
    soup = BeautifulSoup(html, 'html.parser')
    
    return soup


def get_text_tags(soup):
    '''Creates array of arrays consisting of 2 items, the
        each html element and its tag.'''
    
    tags = ['p', 'h2', 'h3']
    empty_els = ['', '\xa0', ' ']
    
    # class='graf' is not present in newer posts 
    text = [element.text for element in soup.find_all(tags , class_='graf') if element.text not in empty_els]
    tag_names = [element.name for element in soup.find_all(tags, class_='graf') if element.text not in empty_els]
    
    # in newer posts, tags no longer have class. Removing the
    # authorBlock div with .decompose() is enough to get the 
    # relevant html info
    if text == []:
        if soup.find('div', {'class': 'authorBlock'}) is not None:
            soup.find('div', {'class': 'authorBlock'}).decompose()
            
        content = soup.find('section', {'class':'post-content'})
        text = [element.text for element in content.find_all(tags) if element.text not in empty_els]
        tag_names = [element.name for element in content.find_all(tags) if element.text not in empty_els]
    
    list_content = list(list(ele) for ele in zip(text, tag_names))
    
    return list_content


def clean_date(date):
    '''Converts date string to correct format for pd datetime'''
    
    # Get the year
    year_pattern = r'\d{4}$'
    year, = re.findall(year_pattern, date)
    
    # Get the month
    month_dict = {'January':'01', 'February':'02', 'March':'03', 
                  'April':'04', 'May':'05', 'June':'06', 
                  'July':'07','August':'08','September':'09', 
                  'October':'10', 'November':'11', 'December':'12'}
    
    month_pattern = r'^([\w\-]+)'
    month_r, = re.findall(month_pattern, date)
    month = month_dict.get(month_r)
    
    # Get the day
    day_pattern = r'\s(\d{2}),'
    day, = re.findall(day_pattern, date)
    
    # Putting it all together
    date_formatted = f'{year}-{month}-{day}'
    
    return date_formatted

def title_pub_date(soup):
    '''Extracting title and publication date for each post'''
    
    title = soup.find('h2', class_='secondary-post-title').text
    pub_date = soup.find('time').text
    
    date_formatted = clean_date(pub_date)
    
    return title, date_formatted


def content_to_df(url, title, pub_date, text_tags):
    '''Creates df with text and tags for each post, seperated by
        element. Url, title and published are static for each post.'''
    
    columns = ['url', 'title', 'published', 'content', 'tag']
    df = pd.DataFrame(columns=columns)
    
    '''converting to lists'''
    url_l = [url]
    title_l = [title]
    pub_date_l = [pub_date]
    zipped = zip(url_l, title_l, pub_date_l, text_tags)
    
    for z in list(zipped):
        for ele in text_tags:
            df = df.append({'url': z[0],
                            'title': z[1],
                            'published': z[2],
                            'content': ele[0],
                            'tag': ele[1]}, ignore_index=True)
    
    return df


def scraped_to_df(url):
    html = get_content(url)
    soup = make_soup(html)
    
    text_tags = get_text_tags(soup)
    title, pub_date = title_pub_date(soup)
    
    df = content_to_df(url, title, pub_date, text_tags)
    
    # convert published col to datetime
    df['published'] = pd.to_datetime(df['published'])
    
    return df