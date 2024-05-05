import pandas as pd
import streamlit as st
from datetime import timedelta
from cutoff_calculator import read_cutoff_data, run_cutoff_workflow


FIELD_SIZE = 30000
BQ_YEAR = "2025"

@st.cache_data
def fetch_cutoff_data():
    male_cutoffs, female_cutoffs, x_cutoffs = read_cutoff_data()
    return male_cutoffs, female_cutoffs, x_cutoffs

def convert_to_timedelta(timestring):
    time_parts = timestring.split(":")
    delta = timedelta(hours=int(time_parts[0]), minutes=int(time_parts[1]), seconds=int(time_parts[2]))
    return delta


def main():
    st.title("Will I Qualify?")
    st.write("Calculate the current 2025 Boston Marathon qualifying time using current marathon times from the 50 top North American marathons")

    male_cutoffs, female_cutoffs, x_cutoffs = fetch_cutoff_data()

    # Get user input for age and gender
    col1, col2 = st.columns([1,1])
    gender = col1.radio("Select gender:", ('Male', 'Female'))
    age = col2.number_input("Enter age on date of Boston Marathon (4/25/25):", min_value=18, max_value=110, step=1)

    # Get the standard cutoff time for the user's age group
    if gender == "Male":
        standard_cutoff = male_cutoffs.loc[male_cutoffs["Age"] == age, "M"]
    elif gender == "Female":
        standard_cutoff = female_cutoffs.loc[male_cutoffs["Age"] == age, "F"]
    standard_cutoff_time = standard_cutoff.iloc[0]
    standard_cutoff_delta = convert_to_timedelta(standard_cutoff_time)

    button = st.button("Calculate Cutoff")
    st.write("----------")
    if button:

        application_rates = [.77, .8, .83, 1]
        application_rate_labels = [["Everyone Applies", "More than Usual Apply", "Average Number Apply", "Less than Usual Apply"]]
        # Create cutoff table and projected qualifying times based on application rates
        df = pd.DataFrame(columns=["Cut-Off Time", "Projected Qualifying Time"])
        for rate in application_rates:
            total_runners_qualified, cutoff_time = run_cutoff_workflow(rate, FIELD_SIZE, BQ_YEAR)

            cutoff_time_delta = convert_to_timedelta(cutoff_time)
            adjusted_cutoff_time = standard_cutoff_delta - cutoff_time_delta
            df.loc[-1] = [cutoff_time, str(adjusted_cutoff_time)]
            df.index = df.index + 1
            df = df.sort_index()
        df.set_index(application_rate_labels, drop=True, inplace=True)

        # Display result
        st.html(f"""<h3>Results</h3>
            <b>Total qualified runners:</b> {str(total_runners_qualified)}<br>
            <b>Official Qualifying Time for an Age {age} {gender}</b>: {standard_cutoff_time}<br><br>
            
            Projected cut-off and qualifying times based on the rate at which people who qualify for Boston actually apply for it
            """
        )
        st.write(df)


if __name__ == "__main__":
    main()
