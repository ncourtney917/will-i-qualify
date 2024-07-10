import find_my_marathon_scraper
import marathon_guide_scraper
import marathon_cleaner
import pandas as pd
from selenium import webdriver

def main():
    driver = webdriver.Chrome()
    bq_year = "2025"
    year = 2024
    boston_date = "04/25/2025"

    # Get top-50 marathon list from marathonguide.com for given year and add to marathon list
    marathon_guide_scraper.get_marathon_list(driver, year)

    # Get all marathons from find_my_marathon and add to marathon list
    find_my_marathon_scraper.find_my_marathon_search(driver, bq_year)

    # Get the equivalent marathon on marathon_guide
    find_my_marathon_scraper.find_marathon_guide_equivalent(driver, detailed_search=False)

    # Retrieve dates
    find_my_marathon_scraper.find_my_marathon_date_search(driver)

    # Re-run equivalent search using dates
    find_my_marathon_scraper.find_marathon_guide_equivalent(driver, detailed_search=True)


    # Scrape the results of whatever we still need to
    marathon_guide_scraper.scrape_results(driver, bq_year)


    # Split results by bq year
    full_filename = "data/raw_results_all.csv"
    full_results_df = pd.read_csv(full_filename)
    window_df = pd.read_csv("data/bq_windows.csv")
    bq_year_results = marathon_cleaner.bq_marathon_splitter(full_results_df, window_df, bq_year, to_csv=True)

    # Clean results from specific BQ year
    df = pd.read_csv(f"data/bq{bq_year}_raw_results.csv")
    Boston25 = marathon_cleaner.MarathonCleaner(df, boston_date)
    Boston25.clean_marathon()
    Boston25.df.to_csv(f"data/bq{str(bq_year)}_cleaned_results.csv", index=False)

if __name__ == "__main__":
    main()
