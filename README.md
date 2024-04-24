# will-i-qualify
Boston Marathon Qualifying Predictor

## Project Phases
### Phase 0: Create predictor using times 1 marathon (2024 Boston Marathon)
Deliverable: 4/28/24
* Stored data from 2024 Boston Marathon
* Stored cutoff times by age group
* Uniformly distributed birthdays
* Compute “time below cutoff” per runner (using age and gender cutoffs)
* Compute current cutoff time
* Light user interface
* User enters age and gender and app tells you the cutoff time

### Phase 1: Create predictor using top 50 qualifiers to-date from the last year
Deliverable: 5/5/24
* Pull in data from top 50 marathon qualifiers so far this year
* Repeat analysis from Phase 0
* Create best case, worst case, and most likely based on how many people will choose to register (based off Medium article)
* Exact-match entity resolution


### Phase 2: Project what the cutoff time will be based on projections for the remaining races
Deliverable: 5/19/24
* Get list of remaining marathons that are major Boston qualifiers. Review the results of these races from prior years. Create distribution of those times
* Generate projections on this year’s data


------------------------

### Assumptions:
* 2025 qualifying window: 9/1/2023 and 9/13/2024
* The qualifying times below are based upon each athlete's age on the date of the 2025 Boston Marathon (April 21, 2025)
* Field size: 30,000 (2024)


------------------------

### Sources
* Official site (with 2024 cutoffs): Qualify | Boston Athletic Association (baa.org)
* Find My Marathon (Top 50 BQs): 2025 Boston Marathon Qualifiers (findmymarathon.com)
* Historical BQ Marathons: Boston Marathon Qualifiers - Most Popular Qualifying Marathons- 2023 (marathonguide.com)
* Marathon Results Page: Boston Marathon Race Results 2024 (marathonguide.com)
* Medium Article: An attempt to predict the cutoff time for the 2025 Boston Marathon. | by Joe Drake | Medium
