import pandas as pd
import streamlit as st
from datetime import timedelta
from cutoff_calculator import read_cutoff_data, run_cutoff_workflow


FIELD_SIZE = 30000
BQ_YEAR = "2025"
NUM_FUTURE_QUALIFIERS = 4128

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
    st.write("Calculate the current 2025 Boston Marathon qualifying time using current marathon times from all North American Boston-Qualifying marathons")

    with st.sidebar:
        st.title("Methodology")

        st.header("Background")
        st.write("""
            This project is my attempt to predict the cutoff time to qualify for the 2025 Boston Marathon using scraped
            marathon results from the current year's qualifying marathons and using assumptions from prior year's 
            marathon application pools. This approach differs from other attempts to predict the Boston Marathon cutoff
            time because it relies on ground truth data about finishing times for this year's marathon runners, not broad,
            population-level estimates.
            
            For more information about Boston Qualifying standards, see the race info website: https://www.baa.org/races/boston-marathon/qualify
        """)

        st.header("Process")
        st.html("""
        <b>1. Get list of Boston Qualifying marathons</b> from www.findmymarathon.com <br><br>
        
        <b>2. Scrape marathon results. </b>Find the corresponding marathon page on www.marathonguide.com and scrape the results of the finishers.<br><br>
        
        <b>3. Predict each finisher age on next year's Boston Marathon date.</b> Predict the age each finisher will be 
        on the date of the 2025 Boston Marathon using their stated age and a randomly assigned birthday. My assumption 
        is that over the course of the entire sample of finishers, the noise from randomly assigned birthdays will smooth out.<br><br>
        
        <b>4. Calculate each runner's time below Boston Qualifying Time.</b> Based on the gender and age group 
        (determined from the imputed age in step 3), calculate the amount of time each runner finished below (or above) 
        their group's Boston Marathon Qualifying Time.<br><br>
        
        <b>5. Predict the number of Boston Qualifying times by year end.</b> FindMyMarathon gives an estimate of how many 
        runners have qualified for Boston so far this year and by what percentage that number has differed from last year
        at this point: <a href="https://findmymarathon.com/bostonmarathonqualifiers-2025.php">2025 Boston Qualifiers</a> (as of this writing, that number was
        a 15.5% increase in Boston 2025 qualifiers over Boston 2024 qualifiers (we will call this the "current year scaling factor"). To calculate the number of runners I expect
        to qualify by year's end, I took last year's number of qualifiers (according to findmymarathon.com), and increased it
        by the current year scaling factor of 15.5%. I then scaled it by a factor of 10% (which I will call Nick's methodology factor) because I have consistently found my number of Boston Qualifiers to be 10% greater than the stated number on findmymarathons.com. I believe this is due to my birthday estimations (a 39 year-old male running a 3:06 marathon wouldn't qualify, but if we adjust his age to 40, he would qualify by 4 minutes).
        These scaling factors then result to how many Boston Qualifying times will be run by year's end. Here is a summary of the calculation:<br><br>
        Data as of 5/23/24:<br><br>
        Predicted 2025 # of BQs = FMM 2024 # of BQs * Current Year Scaling Factor * Nick's Methodology Factor <br><br>
           66,363 = 52,234 * 1.155 * 1.10    <br><br>
        
        Note: Ideally, I could do this step of the analysis more precisely by applying my methodology to previous years of
        data. However, I have not yet scraped data for previous marathon years, which is why I'm using the findmymarathon
        numbers for historical data.<br><br>
        
        <b>6. Impute times for the runners who have not yet qualified.</b> The difference between the number calculated in 
        step 5 and the current number of 2025 qualifying times in my database reflects the number of runners who I predict 
        will qualify by year-end, but who have not done so yet. My assumption is that these runners will look exactly like
        the runners who have been running qualifying times earlier in the year. To create records for these "future qualifiers", 
        I randomly select a sample of the current population and duplicate their records in a temporary database. For example,
        if step 5 predicted that there are 7,000 future qualifiers, I randomly select 7,000 of my current qualifiers, duplicate their records,
        and add them to my results to create a prediction of what the final database of qualified runners might look like.<br><br>
        
        <b>7. Calculate historical Boston Marathon application rates.</b> The biggest unknown in this analysis is how many of
        the runners who have qualified for a Boston in a given year will actually apply to run the race. The Boston 
        Marathon website produces a table of how many applicants each year were not accepted. I compared these numbers with
        findmymarathon.com's previous year totals of how many Boston Qualifying times were run (scaled up by 10% according to
        Nick's methology factor, discussed in step 5) determine the historical application percentage rates. <br><br>
        For example in 2024:<br><br>
        Application Rate = Number of Applicants / (FMM # of BQs * Nick's Methology Factor)<br><br>
        71% = 41,039 / 52,217 * 1.10<br><br>
        
        In the end, I determined historical application rates of 67 - 71% of my calculated number of BQs.<br><br>
        
        <b>8. Calculate projected cut-off times using a range of different application rates.</b> Using a range of high (75%),
        medium (70%), and low (65%) application rates, select that percentage of BQ records at random as the population of
        runners who will apply for the 2025 Boston Marathon. Using these subset of applied records, calculate the exact 
        cut-off time using each runners time-below-age-group-qualifying-time score. That is, sort the runners by their 
        time-below-qualifying-time score and take the first 30,000 (since the field size is 30,000). The time-below-qualifying-time
        of the 30,000th runner is the projected 2025 Boston Marathon cutoff time!<br><br>
        
        Let me know your thoughts on my approach!<br><br>
        
        Happy running,<br>
        Nick           
        """)

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

        application_rates = [.6388, .70, .75, 1]
        application_rate_labels = [["Everyone Applies", "More than Usual Apply", "Average Number Apply", "Less than Usual Apply"]]
        # Create cutoff table and projected qualifying times based on application rates
        df = pd.DataFrame(columns=["Cut-Off Time", "Projected Qualifying Time"])
        for rate in application_rates:
            total_runners_qualified, cutoff_time = run_cutoff_workflow(rate, FIELD_SIZE, BQ_YEAR, NUM_FUTURE_QUALIFIERS)

            cutoff_time_delta = convert_to_timedelta(cutoff_time)
            adjusted_cutoff_time = standard_cutoff_delta - cutoff_time_delta
            df.loc[-1] = [cutoff_time, str(adjusted_cutoff_time)]
            df.index = df.index + 1
            df = df.sort_index()
        df.set_index(application_rate_labels, drop=True, inplace=True)

        # Display result
        st.html(f"""<h3>Results</h3>
            Data pulled on 7/10/24:<br><br>
            
            <b>Current qualified runners:</b> {str(total_runners_qualified - NUM_FUTURE_QUALIFIERS)}<br>
            <b>Projected qualified runners:</b> {str(total_runners_qualified)}<br>
            <b>Official Qualifying Time for an Age {age} {gender}</b>: {standard_cutoff_time}<br><br>
            
            Projected cut-off and qualifying times based on the rate at which people who qualify for Boston actually apply for it
            """
        )
        st.write(df)


if __name__ == "__main__":
    main()
