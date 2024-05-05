import pandas as pd
pd.options.mode.chained_assignment = None

FIELD_SIZE = 30000
APPLICATION_PERCENTAGE = .80


def merge_gender_cutoffs(gender_race_df, gender_cutoff_df, gender_col):
    gender_qualifying_df = pd.merge(gender_race_df, gender_cutoff_df, how="left", left_on="Age at Boston Marathon", right_on="Age")
    gender_qualifying_df.rename(columns={gender_col:"Cutoff Time"}, inplace=True)
    return gender_qualifying_df

def calculate_time_under_cutoff(df):
    df["Time Under Cutoff"] = pd.to_timedelta(df["Cutoff Time"]) - pd.to_timedelta(df["Time"])
    df = df.loc[df["Time Under Cutoff"]>=pd.to_timedelta(0), :]
    df.sort_values(by="Time Under Cutoff", ascending=False, inplace=True)
    df['Time Under Cutoff'] = df['Time Under Cutoff'].astype(str).map(lambda x: x[-8:])
    return df


def read_data(bq_year):
    df = pd.read_csv(f"will-i-qualify/data/bq{bq_year}_cleaned_results.csv")
    male_df = df.loc[df["Gender"] == "M", :]
    female_df = df.loc[df["Gender"] == "F", :]
    x_df = df.loc[df["Gender"] == "X", :]
    return male_df, female_df, x_df

def read_cutoff_data():
    cutoff_df = pd.read_csv("will-i-qualify/data/bq_cutoffs.csv")
    male_cutoffs = cutoff_df.loc[:, ["Age", "M"]]
    female_cutoffs = cutoff_df.loc[:, ["Age", "F"]]
    x_cutoffs = cutoff_df.loc[:, ["Age", "X"]]
    return male_cutoffs, female_cutoffs, x_cutoffs

def calculate_time_cutoff(male_df, male_cutoffs, female_df, female_cutoffs, x_df, x_cutoffs, application_percentage, field_size):
    male_full_df = merge_gender_cutoffs(male_df, male_cutoffs, "M")
    female_full_df = merge_gender_cutoffs(female_df, female_cutoffs, "F")
    x_full_df = merge_gender_cutoffs(x_df, x_cutoffs, "X")
    full_racer_df = pd.concat([male_full_df, female_full_df, x_full_df])
    qualifying_df = calculate_time_under_cutoff(full_racer_df)
    qualifying_df.reset_index(drop=True, inplace=True)

    applying_df = qualifying_df.sample(frac=application_percentage)
    applying_df = applying_df.sort_values(by="Time Under Cutoff", ascending=False).reset_index(drop=True)
    applying_df = applying_df.iloc[:field_size, :]
    total_runners_qualified = len(qualifying_df)
    cutoff_time = applying_df.iloc[-1, :]["Time Under Cutoff"]
    return total_runners_qualified, cutoff_time

def run_cutoff_workflow(application_percentage, field_size, bq_year):
    male_df, female_df, x_df = read_data(bq_year=bq_year)
    male_cutoffs, female_cutoffs, x_cutoffs = read_cutoff_data()
    total_runners_qualified, cutoff_time = calculate_time_cutoff(male_df, male_cutoffs, female_df, female_cutoffs, x_df, x_cutoffs, application_percentage, field_size)
    return total_runners_qualified, cutoff_time


if __name__ == "__main__":
    BQ_YEAR = "2025"
    total_runners_qualified, cutoff_time = run_cutoff_workflow(APPLICATION_PERCENTAGE, FIELD_SIZE, BQ_YEAR)

    print("\n\n")
    print(f"{total_runners_qualified} runners qualified")
    print(f"Using field size of {FIELD_SIZE} and application percentage of {APPLICATION_PERCENTAGE}...")
    print("----------------")
    print(f"The {BQ_YEAR} Boston Marathon cutoff time is currently: {cutoff_time}")

