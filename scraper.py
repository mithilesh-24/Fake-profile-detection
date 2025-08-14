import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()
IG_USERNAME = os.getenv("IG_USERNAME", "lethish_kumar_420")
IG_PASSWORD = os.getenv("IG_PASSWORD", "geetha@21234")

# Regex patterns
EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"\+?\d[\d\s()-]{7,15}"

def instagram_login(driver):
    """Logs into Instagram with dummy account."""
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    # Fill username
    username_input = driver.find_element(By.NAME, "username")
    username_input.clear()
    username_input.send_keys(IG_USERNAME)

    # Fill password
    password_input = driver.find_element(By.NAME, "password")
    password_input.clear()
    password_input.send_keys(IG_PASSWORD)
    password_input.send_keys(Keys.RETURN)

    time.sleep(2)  # Wait for login to complete

    # Dismiss "Save Login Info?" popup
    try:
        not_now_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]")
        not_now_btn.click()
        time.sleep(3)
    except:
        pass

    # Dismiss notifications popup
    try:
        not_now_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]")
        not_now_btn.click()
        time.sleep(3)
    except:
        pass

def scrape_profile(username, login=False):
    """
    Scrapes Instagram profile data.
    If login=True, will log in with dummy account.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    profile_data = {
        "username": username,
        "is_private": None,
        "bio": "",
        "posts_count": None,
        "followers_count": None,
        "following_count": None,
        "captions": [],
        "hashtags": [],
        "mentions": [],
        "likes": [],
        "comments_count": 0,
        "first_comments": [],
        "mutual_count": 0,
        "emails_found": [],
        "phones_found": []
    }

    try:
        # Login if required
        if login:
            instagram_login(driver)

        # Visit profile
        driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(3)

        page_source = driver.page_source

        # Scrape posts, followers, following counts (available for both public and private)
        try:
            counts = driver.find_elements(By.CSS_SELECTOR, "header section ul li span span")
            if len(counts) >= 3:
                profile_data["posts_count"] = counts[0].get_attribute("title") or counts[0].text
                profile_data["followers_count"] = counts[1].get_attribute("title") or counts[1].text
                profile_data["following_count"] = counts[2].text
        except:
            profile_data["posts_count"] = None
            profile_data["followers_count"] = None
            profile_data["following_count"] = None

        # Detect private account
        if "This Account is Private" in page_source:
            profile_data["is_private"] = True
            try:
                bio_text = driver.find_element(By.TAG_NAME, "header").text
                profile_data["bio"] = bio_text
            except:
                pass
        else:
            profile_data["is_private"] = False

            # Bio
            try:
                bio_element = driver.find_element(By.CSS_SELECTOR, "header section div.-vDIg span")
                profile_data["bio"] = bio_element.text
            except:
                pass

            # Captions
            try:
                captions = driver.find_elements(By.CSS_SELECTOR, "div._a9zr span")
                for cap in captions:
                    text = cap.text
                    if text:
                        profile_data["captions"].append(text)
                        profile_data["hashtags"].extend(re.findall(r"#\w+", text))
                        profile_data["mentions"].extend(re.findall(r"@\w+", text))
            except:
                pass

            # Likes
            try:
                like_elements = driver.find_elements(By.CSS_SELECTOR, "section span._aacl._aaco._aacw._aad6._aade")
                profile_data["likes"] = [el.text for el in like_elements if el.text]
            except:
                pass

            # Comments
            try:
                comment_elements = driver.find_elements(By.CSS_SELECTOR, "ul._a9ym li")
                profile_data["first_comments"] = [c.text for c in comment_elements[:5]]
                profile_data["comments_count"] = len(comment_elements)
            except:
                pass

            # Mutual count (requires login)
            if login:
                try:
                    mutual_element = driver.find_element(By.XPATH, "//span[contains(text(), 'mutual')]")
                    profile_data["mutual_count"] = int(re.findall(r"\d+", mutual_element.text)[0])
                except:
                    pass

        # Extract emails and phones
        combined_text = profile_data["bio"] + " " + " ".join(profile_data["captions"])
        profile_data["emails_found"] = re.findall(EMAIL_REGEX, combined_text)
        profile_data["phones_found"] = re.findall(PHONE_REGEX, combined_text)

    finally:
        driver.quit()

    return profile_data

if __name__ == "__main__":
    # Example test
    print(scrape_profile("_mithilesh_24_", login=True))
