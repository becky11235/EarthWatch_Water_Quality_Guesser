# Earthwatch_Water_Quality_Guesser
Human Baseline Water Quality Judgement Script

# Code

The main script is _human_baseline_1.py_ which does the following:
  Asks a participant how many photos they want to judge.
  
  The participant is shown photos one at a time and selects:
      - Poor/Moderate
      - Good
      - INVALID
  
  A photo is INVALID if it does not show the waterbody
  (e.g. it shows data collection forms, people, etc.).
  
  Results are:
      1. Saved as an individual timestamped CSV.
      2. Appended to _human_baseline_results_overall.csv_.
      3. Used to calculate the overall accuracy across all participants.

# Data

Contains the photo manifest _photo_manifest.xslx_ and the global dataset _Global_Data_Set_XvsX_0.csv_. You will need both of these to run the script. 
Also contains some sample photos from the Great_UK_WaterBlitz folder of photos. You can replace that sample folder with the full folder of images for a larger sample, but that folder will not upload to GitHub. 

# Results
