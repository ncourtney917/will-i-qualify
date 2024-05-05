import pandas as pd
import numpy as np
from datetime import datetime
import re

class MarathonCleaner:
    def __init__(self, results_df, boston_date):
        self.BOSTON_DATE = boston_date
        self.df = results_df
    def name_age_gender_sep(self):
        # Separate name, age, and gender
        biographic_pattern = r'\(([MFX]\d*)\)$'
        gender_age_split = r'([MFX])(\d*)'

        self.df[["Name", "Gender Age", "Throwaway"]] = self.df['Name'].str.split(biographic_pattern, expand=True)
        self.df[["Gender", "Age"]] = self.df['Gender Age'].str.extract(gender_age_split, expand=True)
        return

    # Function to generate random age in age group
    @staticmethod
    def generate_random_age_in_age_group(row):
        if isinstance(row["Division Start"], str) and isinstance(row["Division End"], str):
            return int(np.random.randint(int(row['Division Start']), int(row['Division End'])))
        else:
            return ""

    @staticmethod
    def generate_elite_age(row):
        return int(np.random.randint(25,35))

    @staticmethod
    def generate_master_age(row):
        return int(np.random.randint(40,59))

    @staticmethod
    def generate_grand_master_age(row):
        return int(np.random.randint(60,80))

    @staticmethod
    def generate_standard_age(row):
        return int(np.random.randint(25,50))

    def fill_blank_ages(self):
        # Pick random age in middle of age group
        self.df[["Division Start", "Division End"]] = self.df["Division"].str.extract(r"(\d+)-(\d+)")
        self.df['Random Age'] = self.df.apply(self.generate_random_age_in_age_group, axis=1)
        self.df.loc[self.df["Age"]=="", "Age"] = self.df["Random Age"]

        self.df['Division'] = self.df['Division'].fillna('')
        self.df['Division_lower'] = self.df['Division'].str.lower()

        # Give random young age to elite runners and olympians
        self.df['Random Age'] = self.df.apply(self.generate_elite_age, axis=1)
        self.df.loc[(self.df["Age"]=="") & (self.df['Division_lower'].str.contains('|'.join(["elite", "open"]))), "Age"] = self.df["Random Age"]
        self.df.loc[(self.df["Age"]=="") & (self.df['Marathon'].str.contains('Olympic')), "Age"] = self.df["Random Age"]

        # Give random age to grand masters
        self.df['Random Age'] = self.df.apply(self.generate_grand_master_age, axis=1)
        self.df.loc[(self.df["Age"]=="") & (self.df['Division_lower'].str.contains("grandmas")), "Age"] = self.df["Random Age"]

        # Give random age to masters
        self.df['Random Age'] = self.df.apply(self.generate_master_age, axis=1)
        self.df.loc[(self.df["Age"]=="") & (self.df['Division_lower'].str.contains('master')), "Age"] = self.df["Random Age"]

        # Give standard random age to everyone else
        self.df['Random Age'] = self.df.apply(self.generate_standard_age, axis=1)
        self.df.loc[self.df["Age"]=="", "Age"] = self.df["Random Age"]
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
        s=1
        # TODO convert this to column-level, not static
        self.df["Marathon Date"] = pd.to_datetime(self.df["Marathon Date"])
        self.df["Race Day of Year"] = self.df["Marathon Date"].apply(lambda x: x.dayofyear)
        self.df["Race Year"] = self.df["Marathon Date"].apply(lambda x: x.year)
        #race_dt = pd.to_datetime(self.race_date)
        #race_day_of_year = race_dt.dayofyear
        #race_year = race_dt.year

        # Calculate year of birth estimate
        self.df['Year of Birth'] = self.df["Race Year"] - self.df['Age'].astype(int)

        # Shift birth year back 1 if birthday hadn't yet occurred by race date
        self.df.loc[self.df['Unadjusted Birthday'].dt.dayofyear > self.df["Race Day of Year"], 'Year of Birth'] -= 1
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
        self.fill_blank_ages()
        self.generate_random_birthdays()
        self.calculate_birth_year()
        self.adjust_birthday()
        self.calculate_boston_age()
        self.df = self.df[["Name", "Hometown", "Gender", "Random Birthday", "Age", "Age at Boston Marathon", "Boston Qualify", "Time"]]

def bq_marathon_splitter(df: pd.DataFrame, window_file: pd.DataFrame, bq_year: int, to_csv: bool = False):
    bq_year_window = window_file.loc[window_file["Boston Marathon Year"]==bq_year, :].reset_index(drop=True)
    bq_year_start = datetime.strptime(bq_year_window["Window Open"][0], "%m/%d/%Y")
    bq_year_end = datetime.strptime(bq_year_window["Window Closed"][0], "%m/%d/%Y")
    df["Marathon Date"] = pd.to_datetime(df["Marathon Date"])
    bq_year_results = df.loc[(df["Marathon Date"]<=bq_year_end) & (df["Marathon Date"] >= bq_year_start), :]
    if to_csv:
        bq_year_results.to_csv(f"data/bq{bq_year}_raw_results.csv", index=False)
    return bq_year_results

if __name__=="__main__":
    bq_year = 2025
    boston_date = "04/25/2025"

    split_marathons = False
    if split_marathons:
        full_filename = "data/raw_results_all.csv"
        full_results_df = pd.read_csv(full_filename)
        window_df = pd.read_csv("data/bq_windows.csv")
        bq_year_results = bq_marathon_splitter(full_results_df, window_df, bq_year, to_csv=True)

    clean_marathons = True
    if clean_marathons:
        df = pd.read_csv(f"data/bq{bq_year}_raw_results.csv")
        Boston25 = MarathonCleaner(df, boston_date)
        Boston25.clean_marathon()
        Boston25.df.to_csv(f"data/bq{str(bq_year)}_cleaned_results.csv", index=False)
