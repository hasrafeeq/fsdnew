import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

# Constants
BASE_URL = 'https://lincolnshire.fsd.org.uk/kb5/lincs/fsd/home.page'
CATEGORY_BLOCK_CLASS = 'category-block'
CATEGORY_URL_CLASS = 'caticon_'
RESULT_HIT_CONTAINER_ID = 'resultHitContainer'
RESULT_HIT_CLASS = 'result_hit'

def extract_organization_details(base_url, a_tag_url):
    url = urljoin(base_url, a_tag_url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    details = {}
    venue_section = soup.find(class_='field_section service_venue')
    if venue_section:
        name_element = venue_section.find('dt', string='Name')
        if name_element:
            name = name_element.find_next_sibling('dd')
            if name:
                details['Name'] = name.text.strip()

        address_element = venue_section.find('dt', string='Address')
        if address_element:
            address = ', '.join([span.text.strip() for span in address_element.find_next_sibling('dd').find_all('span')])
            details['Address'] = address

        postcode_element = venue_section.find('dt', string='Postcode')
        if postcode_element:
            postcode = postcode_element.find_next_sibling('dd')
            if postcode:
                details['Postcode'] = postcode.text.strip()

    # Extract description text and clean it
    description_text = soup.find(class_='description_text')
    if description_text:
        description = description_text.text.strip().replace('\n', ' ').replace('\u00a0', ' ')
        details['Description'] = description

    details['URL'] = urljoin(base_url, a_tag_url)  # Add URL to details

    return details


# Function to scrape details from each category URL
def scrape_category(category_url, category_title):
    response = requests.get(category_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    container = soup.find(id=RESULT_HIT_CONTAINER_ID)
    data = []
    if container:
        result_hits = container.find_all(class_=RESULT_HIT_CLASS)

        for hit in result_hits:
            h4_tag = hit.find('h4')
            a_tag = h4_tag.find('a')
            a_tag_url = a_tag['href']
            text = a_tag.text.strip()

            org_details = extract_organization_details(category_url, a_tag_url)
            if org_details:
                org_details['Name'] = text
                org_details['Category'] = category_title
                data.append(org_details)

        next_page_link = soup.find('a', class_='next-page')
        if next_page_link:
            next_page_url = urljoin(category_url, next_page_link['href'])
            data.extend(scrape_category(next_page_url, category_title))

    return data


# Extract category URLs
def extract_category_urls(base_url):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    category_blocks = soup.find_all(class_=CATEGORY_BLOCK_CLASS)
    category_urls = []

    for block in category_blocks:
        a_tag = block.find('a', class_=lambda x: x and CATEGORY_URL_CLASS in x)
        if a_tag:
            category_urls.append((urljoin(base_url, a_tag['href']), a_tag.text.strip()))

    return category_urls

# Main function
def main():
    category_urls = extract_category_urls(BASE_URL)
    all_data = []
    for category_url, category_title in category_urls:
        print("Scraping data for category:", category_title)
        category_data = scrape_category(category_url, category_title)
        all_data.extend(category_data)

    # Save data to JSON file
    with open('scraped_data.json', 'w') as json_file:
        # Preprocess the data to ensure the desired key order
        processed_data = []
        for item in all_data:
            processed_item = {
                'Category': item['Category'],
                'Name': item['Name'],
                'Description': item.get('Description', ''),
                'Address': item.get('Address', ''),
                'Postcode': item.get('Postcode', ''),
                'URL': item['URL']
            }
            processed_data.append(processed_item)

        # Dump the processed data to the JSON file
        json.dump(processed_data, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
