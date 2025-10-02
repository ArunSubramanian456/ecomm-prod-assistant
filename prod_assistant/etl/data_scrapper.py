import csv
import time
import re
import os
from bs4 import BeautifulSoup # for parsing HTML content
import undetected_chromedriver as uc # to avoid bot detection
from selenium.webdriver.common.by import By # helps to locate elements on a web page
from selenium.webdriver.common.keys import Keys # provides keys in the keyboard like RETURN, F1, ALT etc. for sending keyboard actions
from selenium.webdriver.common.action_chains import ActionChains # helps to perform complex user interactions like hover, drag and drop etc.

class FlipkartScraper:
    def __init__(self, output_dir = "data"):
        """
        Initialize the FlipkartScraper class.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_top_reviews(self, product_url, count=2):
        """
        Get top reviews for a product.
        """
        options = uc.ChromeOptions() # Create Chrome options to run the browser in headless mode
        options.add_argument("--no-sandbox") # Bypass OS security model
        options.add_argument("--disable-blink-features=AutomationControlled") # Avoid detection
        driver = uc.Chrome(options=options,use_subprocess=True)

        if not product_url.startswith("http"):
            return "No reviews found"

        try:
            driver.get(product_url)
            time.sleep(4)
            try:
                driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click() # Close login popup if it appears
                time.sleep(1)
            except Exception as e:
                print(f"Error occurred while closing popup: {e}")

            for _ in range(4):
                ActionChains(driver).send_keys(Keys.END).perform()
                time.sleep(1.5)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            review_blocks = soup.select("div._27M-vq, div.col.EPCmJX, div._6K-7Co") # Adjusted selectors to capture various review formats
            seen = set()
            reviews = []

            for block in review_blocks:
                text = block.get_text(separator=" ", strip=True)
                if text and text not in seen:
                    reviews.append(text)
                    seen.add(text)
                if len(reviews) >= count:
                    break
        except Exception:
            reviews = []

        driver.quit()
        return " || ".join(reviews) if reviews else "No reviews found"

    def scrape_flipkart_products(self, query, max_products=1, review_count=2):
        """
        Scrape Flipkart products based on the search query.
        """
        options = uc.ChromeOptions()
        driver = uc.Chrome(options=options,use_subprocess=True)
        search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}" # Construct search URL
        driver.get(search_url)
        time.sleep(4)

        try:
            driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click() # Close login popup if it appears
        except Exception as e:
            print(f"Error occurred while closing popup: {e}")

        time.sleep(2)
        products = []

        items = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")[:max_products] # Select product items
        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, "div.KzDlHZ").text.strip() # Product title
                price = item.find_element(By.CSS_SELECTOR, "div.Nx9bqj").text.strip() # Product price
                rating = item.find_element(By.CSS_SELECTOR, "div.XQDdHH").text.strip() # Product rating
                reviews_text = item.find_element(By.CSS_SELECTOR, "span.Wphh3N").text.strip() # Product reviews text
                match = re.search(r"\d+(,\d+)?(?=\s+Reviews)", reviews_text) # Extract number of reviews
                total_reviews = match.group(0) if match else "N/A" # Default to "N/A" if not found

                link_el = item.find_element(By.CSS_SELECTOR, "a[href*='/p/']") # Product link element
                href = link_el.get_attribute("href") # Extract href attribute
                product_link = href if href.startswith("http") else "https://www.flipkart.com" + href # Complete URL if relative
                match = re.findall(r"/p/(itm[0-9A-Za-z]+)", href) # Extract product ID from URL
                product_id = match[0] if match else "N/A" # Default to "N/A" if not found
            except Exception as e:
                print(f"Error occurred while processing item: {e}")
                continue

            top_reviews = self.get_top_reviews(product_link, count=review_count) if "flipkart.com" in product_link else "Invalid product URL"
            products.append([product_id, title, rating, total_reviews, price, top_reviews])

        driver.quit()
        return products

    def save_to_csv(self, data, filename= "product_reviews.csv"):
        """
        Save the scraped data to a CSV file.
        """
        if os.path.isabs(filename):
            path = filename
        elif os.path.dirname(filename):  # filename includes subfolder like 'data/product_reviews.csv'
            path = filename
            os.makedirs(os.path.dirname(path), exist_ok=True)
        else:
            # plain filename like 'output.csv'
            path = os.path.join(self.output_dir, filename)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "product_title", "rating", "total_reviews", "price", "top_reviews"])
            writer.writerows(data)
    