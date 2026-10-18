import argparse
import io
import re
import time
from urllib.parse import quote_plus

import pandas as pd
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


RESULT_LINK_SELECTORS = [
    (By.CSS_SELECTOR, "a.hfpxzc"),
    (By.CSS_SELECTOR, "a[href*='/maps/place/']"),
]


DETAIL_NAME_SELECTORS = [
    (By.CSS_SELECTOR, "h1.DUwDvf"),
    (By.CSS_SELECTOR, "h1.fontHeadlineLarge"),
]


def _add_browser_arguments(options, headless: bool) -> None:
    options.add_argument("--guest")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,2200")
    options.add_argument("--lang=en")
    if headless:
        options.add_argument("--headless=new")


def _build_driver(headless: bool):
    errors = []

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = "/usr/bin/chromium"
    _add_browser_arguments(chrome_options, headless)
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(90)
        return driver
    except WebDriverException as exc:
        errors.append(f"Chrome launch failed: {exc}")

    edge_options = webdriver.EdgeOptions()
    edge_options.use_chromium = True
    _add_browser_arguments(edge_options, headless)
    try:
        driver = webdriver.Chrome(
            service=Service("/usr/bin/chromedriver"),
            options=chrome_options
        )
        driver.set_page_load_timeout(90)
        return driver
    except WebDriverException as exc:
        errors.append(f"Edge launch failed: {exc}")

    raise RuntimeError(
        "Unable to start a Selenium browser session. Install Chrome or Edge and make sure "
        "the browser can be launched locally. "
        + " | ".join(errors)
    )


def _first_element(driver, selectors):
    for by, selector in selectors:
        elements = driver.find_elements(by, selector)
        for element in elements:
            if element.is_displayed():
                return element
    return None


def _element_value(element) -> str:
    if element is None:
        return ""

    for candidate in [element.text, element.get_attribute("aria-label"), element.get_attribute("title")]:
        if candidate and candidate.strip():
            return candidate.strip()
    return ""


def _clean_label(value: str) -> str:
    if not value:
        return ""

    cleaned = value.strip()
    prefixes = [
        "Address: ",
        "Copy address: ",
        "Website: ",
        "Open website: ",
        "Phone: ",
        "Copy phone number: ",
        "Plus code: ",
    ]
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break

    cleaned = re.sub(r"^[\ue000-\uf8ff\s]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _find_text(driver, selectors) -> str:
    element = _first_element(driver, selectors)
    return _clean_label(_element_value(element))


def _find_attr(driver, selectors, attr: str) -> str:
    element = _first_element(driver, selectors)
    if element is None:
        return ""
    value = element.get_attribute(attr)
    return value.strip() if value else ""


def _extract_rating(driver) -> str:
    rating_text = _find_text(
        driver,
        [
            (By.CSS_SELECTOR, "div.F7nice span[aria-hidden='true']"),
            (By.CSS_SELECTOR, "span.ceNzKf"),
            (By.CSS_SELECTOR, "div[role='img'][aria-label*='stars']"),
        ],
    )
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", rating_text)
    return match.group(1) if match else ""


def _extract_reviews(driver) -> str:
    review_text = _find_text(
        driver,
        [
            (By.CSS_SELECTOR, "button[jsaction*='pane.reviewChart.moreReviews']"),
            (By.CSS_SELECTOR, "button[aria-label*='reviews']"),
            (By.CSS_SELECTOR, "span[aria-label*='reviews']"),
        ],
    )
    match = re.search(r"([0-9,]+)", review_text)
    return match.group(1).replace(",", "") if match else ""


def _extract_coordinates(url: str) -> tuple[str, str]:
    match = re.search(r"@(-?[0-9.]+),(-?[0-9.]+)", url)
    if not match:
        return "", ""
    return match.group(1), match.group(2)


def _extract_additional_details(driver) -> str:
    rows = []
    elements = driver.find_elements(By.CSS_SELECTOR, "button[data-item-id], a[data-item-id]")
    for element in elements:
        data_item_id = element.get_attribute("data-item-id")
        value = _clean_label(_element_value(element))
        if not data_item_id or not value:
            continue
        rows.append(f"{data_item_id}: {value}")

    unique_rows = []
    seen = set()
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        unique_rows.append(row)
    return " | ".join(unique_rows)


def _wait_for_search_state(driver, wait: WebDriverWait) -> None:
    def _ready(browser):
        has_results = any(browser.find_elements(by, selector) for by, selector in RESULT_LINK_SELECTORS)
        has_detail = any(browser.find_elements(by, selector) for by, selector in DETAIL_NAME_SELECTORS)
        return has_results or has_detail

    wait.until(_ready)


def _collect_result_links(driver, max_results: int, scroll_pause: float = 1.5) -> list[str]:
    collected = []
    seen = set()
    stagnant_passes = 0
    previous_count = -1

    for _ in range(30):
        for by, selector in RESULT_LINK_SELECTORS:
            for element in driver.find_elements(by, selector):
                href = element.get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    collected.append(href)
                    if len(collected) >= max_results:
                        return collected

        if len(collected) == previous_count:
            stagnant_passes += 1
        else:
            stagnant_passes = 0
            previous_count = len(collected)

        if stagnant_passes >= 4:
            break

        containers = driver.find_elements(By.CSS_SELECTOR, "div[role='feed']")
        if not containers:
            break

        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", containers[0])
        time.sleep(scroll_pause)

    return collected


def _extract_listing_data(driver, wait: WebDriverWait, query: str, rank: int) -> dict:
    name_element = _first_element(driver, DETAIL_NAME_SELECTORS)
    if name_element is None:
        wait.until(lambda browser: _first_element(browser, DETAIL_NAME_SELECTORS) is not None)

    name = _find_text(driver, DETAIL_NAME_SELECTORS)
    category = _find_text(
        driver,
        [
            (By.CSS_SELECTOR, "button[jsaction*='pane.rating.category']"),
            (By.CSS_SELECTOR, "button.DkEaL"),
        ],
    )
    address = _find_text(
        driver,
        [
            (By.CSS_SELECTOR, "button[data-item-id='address']"),
            (By.CSS_SELECTOR, "button[data-item-id*='address']"),
            (By.CSS_SELECTOR, "button[aria-label^='Address']"),
            (By.CSS_SELECTOR, "button[aria-label^='Copy address']"),
        ],
    )
    website = _find_attr(
        driver,
        [
            (By.CSS_SELECTOR, "a[data-item-id='authority']"),
            (By.CSS_SELECTOR, "a[data-item-id*='authority']"),
            (By.CSS_SELECTOR, "a[aria-label^='Website']"),
        ],
        "href",
    )
    phone = _find_text(
        driver,
        [
            (By.CSS_SELECTOR, "button[data-item-id^='phone:tel:']"),
            (By.CSS_SELECTOR, "button[data-item-id*='phone']"),
            (By.CSS_SELECTOR, "button[aria-label^='Phone']"),
            (By.CSS_SELECTOR, "button[aria-label^='Copy phone number']"),
        ],
    )
    plus_code = _find_text(
        driver,
        [
            (By.CSS_SELECTOR, "button[data-item-id='oloc']"),
            (By.CSS_SELECTOR, "button[aria-label^='Plus code']"),
        ],
    )
    business_status = _find_text(
        driver,
        [
            (By.CSS_SELECTOR, "div.OMl5r"),
            (By.CSS_SELECTOR, "span.ZDu9vd"),
            (By.CSS_SELECTOR, "div[aria-label*='Open']"),
            (By.CSS_SELECTOR, "div[aria-label*='Closed']"),
        ],
    )
    maps_url = driver.current_url
    latitude, longitude = _extract_coordinates(maps_url)
    has_website = "yes" if website else "no"

    return {
        "search_query": query,
        "rank": rank,
        "name": name,
        "category": category,
        "rating": _extract_rating(driver),
        "reviews": _extract_reviews(driver),
        "address": address,
        "website": website,
        "has_website": has_website,
        "phone": phone,
        "plus_code": plus_code,
        "business_status": business_status,
        "maps_url": maps_url,
        "latitude": latitude,
        "longitude": longitude,
        "available_details": _extract_additional_details(driver),
    }


def scrape_google_maps(query: str, max_results: int = 20, headless: bool = True, delay: float = 2.0) -> pd.DataFrame:
    if not query or not query.strip():
        raise ValueError("Query is required. Example: 'cafe in nagpur'.")

    max_results = max(1, int(max_results))
    driver = _build_driver(headless=headless)

    try:
        wait = WebDriverWait(driver, 25)
        driver.get(f"https://www.google.com/maps/search/{quote_plus(query.strip())}")
        _wait_for_search_state(driver, wait)
        time.sleep(delay)

        result_links = _collect_result_links(driver, max_results=max_results)
        if not result_links:
            if _first_element(driver, DETAIL_NAME_SELECTORS) is not None:
                result_links = [driver.current_url]
            else:
                return pd.DataFrame(
                    columns=[
                        "search_query",
                        "rank",
                        "name",
                        "category",
                        "rating",
                        "reviews",
                        "address",
                        "website",
                        "has_website",
                        "phone",
                        "plus_code",
                        "business_status",
                        "maps_url",
                        "latitude",
                        "longitude",
                        "available_details",
                    ]
                )

        rows = []
        for rank, link in enumerate(result_links[:max_results], start=1):
            driver.get(link)
            try:
                wait.until(lambda browser: _first_element(browser, DETAIL_NAME_SELECTORS) is not None)
                time.sleep(delay)
                rows.append(_extract_listing_data(driver, wait, query=query.strip(), rank=rank))
            except TimeoutException:
                rows.append(
                    {
                        "search_query": query.strip(),
                        "rank": rank,
                        "name": "",
                        "category": "",
                        "rating": "",
                        "reviews": "",
                        "address": "",
                        "website": "",
                        "has_website": "no",
                        "phone": "",
                        "plus_code": "",
                        "business_status": "",
                        "maps_url": link,
                        "latitude": "",
                        "longitude": "",
                        "available_details": "Timed out while opening listing details.",
                    }
                )

        results_df = pd.DataFrame(rows)
        if results_df.empty:
            return results_df

        results_df = results_df.drop_duplicates(subset=["maps_url"]).reset_index(drop=True)
        results_df["rank"] = range(1, len(results_df) + 1)
        return results_df
    finally:
        driver.quit()


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Google_Maps_Data")
    return buffer.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Google Maps search results into Excel using a guest browser session.")
    parser.add_argument("--query", required=True, help="Search query, for example: 'cafe in nagpur'")
    parser.add_argument("--max-results", type=int, default=20, help="Maximum number of listings to collect")
    parser.add_argument("--output", default="output/google_maps_results.xlsx", help="Output Excel file path")
    parser.add_argument("--headed", action="store_true", help="Run browser with visible window")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay in seconds after each page load")
    args = parser.parse_args()

    df = scrape_google_maps(
        query=args.query,
        max_results=args.max_results,
        headless=not args.headed,
        delay=args.delay,
    )
    excel_bytes = dataframe_to_excel_bytes(df)
    with open(args.output, "wb") as output_file:
        output_file.write(excel_bytes)

    print(f"Saved {len(df)} rows to {args.output}")


if __name__ == "__main__":
    main()
