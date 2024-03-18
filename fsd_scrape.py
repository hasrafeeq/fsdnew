from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import json
home_url = 'https://lincolnshire.fsd.org.uk/kb5/lincs/fsd/home.page'

def extract_category_details(home_url):
    response = requests.get(home_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    category_details = []

    # Find all div elements with class 'category-block'
    category_blocks = soup.find_all('div', class_='category-block')

    # Loop through each category block
    for block in category_blocks:
        category_info = {}
        # Find the first 'a' tag within the category block
        a_tag = block.find('a')
        # Extract the 'href' attribute from the 'a' tag
        category_info['url'] = urljoin(home_url, a_tag.get('href'))
        
        # Find the 'span' element with class 'p-3' within the category block
        span_element = block.find('span', class_='p-3')
        # Extract the text from the span element
        category_info['name'] = span_element.get_text(strip=True)

        category_details.append(category_info)

    return category_details

def extract_subcategory_urls(category_url):
    response = requests.get(category_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    subcategory_urls = []

    # Find all links to subcategories
    subcategory_links = soup.select('h3.mb-2 a')
    for link in subcategory_links:
        subcategory_urls.append(urljoin(category_url, link['href']))

    return subcategory_urls

def extract_subcategory_details(subcategory_url):
    response = requests.get(subcategory_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the details you want to extract
        name = soup.find('h1', class_='mb-2').text.strip()
        description = soup.find('p').text.strip()
        address_element = soup.find('dt', string='Address')
        address = address_element.find_next_sibling('dd').text.strip() if address_element else None
        postcode_element = soup.find('dt', string='Postcode')
        postcode = postcode_element.find_next_sibling('dd').find('p').text.strip() if postcode_element else None

        return {
            "Name": name,
            "Description": description,
            "Address": address,
            "Postcode": postcode,
            "URL": subcategory_url
        }
    else:
        print(f"Failed to fetch URL: {subcategory_url}")
        return None

def scrape_subcategories(category_info):
    print("Scraping data for category:", category_info['name'])
    scraped_data = []
    # Scrape subcategories from all pages
    page_number = 0
    while True:
        page_url = f"{category_info['url']}&sr={page_number * 10}"
        subcategory_urls = extract_subcategory_urls(page_url)
        if not subcategory_urls:
            break
        for subcategory_url in subcategory_urls:
            subcategory_details = extract_subcategory_details(subcategory_url)
            if subcategory_details:
                data = {
                    "Category": category_info['name'],
                    "Name": subcategory_details['Name'],
                    "Description": subcategory_details['Description'],
                    "Address": subcategory_details['Address'],
                    "Postcode": subcategory_details['Postcode'],
                    "URL": subcategory_details['URL']
                }
                scraped_data.append(data)
        page_number += 1
    return scraped_data

# Main code
def main():
 category_details = extract_category_details(home_url)
 scraped_data_all = []

 for category_info in category_details:
    scraped_data = scrape_subcategories(category_info)
    scraped_data_all.extend(scraped_data)

# Save scraped data as JSON
 with open('scraped_data.json', 'w') as f:
    json.dump(scraped_data_all, f, indent=4)

if __name__ == "__main__":
    main()
print("Scraped data saved as scraped_data.json")
