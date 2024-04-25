import pandas as pd
import numpy as np
from datetime import datetime

class MarathonCleaner:
    def __init__(self, race_date, filename):
        self.BOSTON_DATE = "04/25/2025"
        self.race_date = race_date
        self.df = pd.read_csv(filename)
    def name_age_gender_sep(self):
        # Separate name, age, and gender
        self.df[['Name', 'Race Age']] = self.df['Name'].str.extract(r'^(.*?) \((.*?)\)$')
        self.df[["Gender", "Race Age"]] = self.df['Race Age'].str.extract(r'(\D)(\d{2,3})')
        return

    def generate_random_birthdays(self):
        # Assign random birthdays to each runner
        num_rows = len(self.df)
        start_date = pd.to_datetime('1970-01-01')
        end_date = pd.to_datetime('1970-12-31')
        random_birthdays = pd.to_datetime(np.random.randint(start_date.value,end_date.value, num_rows))
        self.df["Unadjusted Birthday"] = random_birthdays
        return

    def calculate_birth_year(self):
        race_dt = pd.to_datetime(self.race_date)
        race_day_of_year = race_dt.dayofyear
        race_year = race_dt.year

        # Calculate year of birth estimate
        self.df['Year of Birth'] = race_year - self.df['Race Age'].astype(int)

        # Shift birth year back 1 if birthday hadn't yet occurred by race date
        self.df.loc[self.df['Unadjusted Birthday'].dt.dayofyear > race_day_of_year, 'Year of Birth'] -= 1
        return

    def adjust_birthday(self):
        # Create actual random birthday
        self.df["Birth Date"] = pd.to_datetime(self.df["Unadjusted Birthday"]).dt.strftime("%m-%d")
        self.df["Random Birthday"] = self.df["Year of Birth"].astype(str) + "-" + self.df["Birth Date"].astype(str)
        self.df["Random Birthday"] = pd.to_datetime(self.df["Random Birthday"])

    def calculate_boston_age(self):
        boston_dt = datetime.strptime(self.BOSTON_DATE, "%m/%d/%Y")

        # Create age at day of Boston Marathon
        self.df['Age at Boston Marathon'] = boston_dt.year - self.df['Random Birthday'].dt.year
        # Substract 1 from age if birthday occurs later in the year than Boston
        self.df.loc[(self.df['Random Birthday'].dt.month > boston_dt.month) |
               ((self.df['Random Birthday'].dt.month == boston_dt.month) & (self.df['Random Birthday'].dt.day > boston_dt.day)),
        'Age at Boston Marathon'] -= 1

    def clean_marathon(self):
        self.name_age_gender_sep()
        self.generate_random_birthdays()
        self.calculate_birth_year()
        self.adjust_birthday()
        self.calculate_boston_age()
        self.df = self.df[["Name", "Hometown", "Gender", "Random Birthday", "Race Age", "Age at Boston Marathon", "Boston Qualify", "Time"]]


if __name__=="__main__":
    filename = "data/boston_results_2024.csv"
    race_date = "04/15/2024"
    Boston24 = MarathonCleaner(race_date, filename)
    Boston24.clean_marathon()
    Boston24.df.to_csv("data/boston_2024_cleaned.csv", index=False)
