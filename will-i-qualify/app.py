import pandas as pd
import streamlit as st
from datetime import timedelta
from cutoff_calculator import read_cutoff_data, run_cutoff_workflow


FIELD_SIZE = 5000

@st.cache_data
def fetch_cutoff_data():
    male_cutoffs, female_cutoffs = read_cutoff_data()
    return male_cutoffs, female_cutoffs

def convert_to_timedelta(timestring):
    time_parts = timestring.split(":")
    delta = timedelta(hours=int(time_parts[0]), minutes=int(time_parts[1]), seconds=int(time_parts[2]))
    return delta


def main():
    st.title("Will I Qualify?")
    st.write("Calculate the current 2025 Boston Marathon qualifying time using current marathon times from the 50 top North American marathons")

    male_cutoffs, female_cutoffs = fetch_cutoff_data()

    # Get user input for age and gender
    col1, col2 = st.columns([1,1])
    gender = col1.radio("Select gender:", ('Male', 'Female'))
    age = col2.number_input("Enter age on date of Boston Marathon (4/25/25):", min_value=18, max_value=110, step=1)
    application_integer = st.slider("Select percentage of runners who qualify for Boston that will actually try to apply", min_value=75, max_value=85, value=80)
    application_percentage = application_integer / 100

    # Calculate current cutoff time
    total_runners_qualified, cutoff_time = run_cutoff_workflow(application_percentage, FIELD_SIZE)

    # Get the standard cutoff time for the user's age group
    if gender == "Male":
        standard_cutoff = male_cutoffs.loc[male_cutoffs["Age"] == age, "M"]
    elif gender == "Female":
        standard_cutoff = female_cutoffs.loc[male_cutoffs["Age"] == age, "F"]
    standard_cutoff_time = standard_cutoff.iloc[0]

    # Calculate the adjusted cutoff time for the user's age group
    standard_cutoff_delta = convert_to_timedelta(standard_cutoff_time)
    cutoff_time_delta = convert_to_timedelta(cutoff_time)
    adjusted_cutoff_time = standard_cutoff_delta - cutoff_time_delta

    button = st.button("Calculate Cutoff")
    st.write("----------")
    if button:
        # Display result
        st.html("<h3>Results</h3>")
        st.write("Total qualified runners:", total_runners_qualified)
        st.write("Current cutoff time:", cutoff_time)
        st.write(f"Standard cutoff time for an age {age} {gender}: {standard_cutoff_time}")
        st.write(f"Adjusted cutoff time: {adjusted_cutoff_time}")


if __name__ == "__main__":
    main()
