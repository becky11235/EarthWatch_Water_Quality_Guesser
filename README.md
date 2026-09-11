# Earthwatch_Water_Quality_Guesser
Human Baseline Water Quality Judgement Script

The main script is human_baseline_1.py which does the following:
  Asks a participant how many photos they want to judge.
  
  The participant is shown photos one at a time and selects:
      - Poor/Moderate
      - Good
      - INVALID
  
  A photo is INVALID if it does not show the waterbody
  (e.g. it shows data collection forms, people, etc.).
  
  Results are:
      1. Saved as an individual timestamped CSV.
      2. Appended to human_baseline_results_overall.csv.
      3. Used to calculate the overall accuracy across all participants.

# Data

Contains the photo manifest photo_manifest.xslx and the global dataset Global_Data_Set_XvsX_0.csv. You will need both of these to run the script. 
Also contains some sample photos from the Great_UK_WaterBlitz folder of photos. You can replace that sample folder with the full folder of images for a larger sample, but that folder will not upload to GitHub. 

# Results
