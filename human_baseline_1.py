"""
Human Baseline Water Quality Judgement Script

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

Author: Rebecca Tichford
Date: 11-09-26
"""

#Load packages
from datetime import datetime
from pathlib import Path
import random
import tkinter as tk
from tkinter import messagebox
import pandas as pd
from PIL import Image, ImageTk


#Set paths

#Project folder:
# team_project/
# ├── Data/
# │   ├── Great_UK_WaterBlitz/
# │   ├── photo_manifest.xlsx
# │   └── Global_Data_Set_XvsX_0.csv
# └── human_baseline_1.py

ROOT = Path.cwd()
IMAGE_DIR = ROOT / "Data" / "Great_UK_WaterBlitz"
PHOTO_MANIFEST = ROOT / "Data" / "photo_manifest.xlsx"
MAIN_DATA_FILE = ROOT / "Data" / "Global_Data_Set_XvsX_0.csv"
RESULTS_DIR = ROOT / "human_baseline_results"
OVERALL_RESULTS_FILE = RESULTS_DIR / "human_baseline_results_overall.csv"



#Load the data
quality_df = pd.read_csv(
    MAIN_DATA_FILE,
    low_memory=False
)

photo_df = pd.read_excel(
    PHOTO_MANIFEST
)

print(f"Loaded {len(photo_df)} rows from photo_manifest.xlsx")
print(f"Loaded {len(quality_df)} rows from Global_Data_Set_XvsX_0.csv")


#Clean column names
#Remove accidental spaces from column names
photo_df.columns = photo_df.columns.astype(str).str.strip()
quality_df.columns = quality_df.columns.astype(str).str.strip()


#Check needed columns are present in the dataframes
required_photo_columns = {
    "saved_filename",
    "feature_global_id",
    "attachment_global_id",
}

required_quality_columns = {
    "GlobalID",
}

missing_photo_columns = required_photo_columns - set(photo_df.columns)
missing_quality_columns = required_quality_columns - set(quality_df.columns)

if missing_photo_columns:
    raise ValueError(
        "The following columns are missing from photo_manifest.xlsx:\n"
        + "\n".join(sorted(missing_photo_columns))
    )

if missing_quality_columns:
    raise ValueError(
        "The following columns are missing from "
        "Global_Data_Set_XvsX_0.csv:\n"
        + "\n".join(sorted(missing_quality_columns))
    )


#Find the water quality column - 'Feedback Rating'
#Variations so spelling etc. doesn't matter too much
quality_column_candidates = [
    "Feedback Rating",
    "Feedback_Rating",
    "feedback_rating",
    "FeedbackRating",
]

quality_column = None

for column in quality_column_candidates:
    if column in quality_df.columns:
        quality_column = column
        break

if quality_column is None:
    raise ValueError(
        "Could not find the water quality column in "
        "Global_Data_Set_XvsX_0.csv.\n\n"
        "Expected a column called 'Feedback Rating'.\n\n"
        "Columns actually found:\n"
        + "\n".join(quality_df.columns)
    )

print(f"Using '{quality_column}' as the actual water quality column.")

# Convert IDs to strings so that Excel/CSV formatting differences do not stop the merge.

photo_df["attachment_global_id"] = (
    photo_df["attachment_global_id"]
    .astype(str)
    .str.strip()
)

quality_df["GlobalID"] = (
    quality_df["GlobalID"]
    .astype(str)
    .str.strip()
)


#Useful function to standardise water quality labels, making sure they aren't missed due to spelling differences etc.
def canonical_label(value):
    """
    Convert different versions of a water quality label into:

        poor
        moderate
        good

    """

    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    # Remove a few common variations
    value = value.replace("_", " ")
    value = value.replace("-", " ")

    aliases = {
        "p": "poor",
        "poor": "poor",
        "very poor": "poor",

        "m": "moderate",
        "moderate": "moderate",
        "medium": "moderate",

        "g": "good",
        "good": "good",
        "very good": "good",
    }

    return aliases.get(value, value)


#Merge photo_manifest.xlsx with Global_Data_Set_XvsX_0.csv
#feature_global_id --> GlobalID

#Clean the IDs
photo_df["feature_global_id"] = (
    photo_df["feature_global_id"]
    .astype(str)
    .str.strip()
)

quality_df["GlobalID"] = (
    quality_df["GlobalID"]
    .astype(str)
    .str.strip()
)

#Merge photo manifest with main water-quality dataset
data = pd.merge(
    photo_df,
    quality_df[["GlobalID", quality_column]],
    left_on="feature_global_id",
    right_on="GlobalID",
    how="left",
)

#Give Feedback Rating a simpler name
data = data.rename(
    columns={
        quality_column: "actual_quality"
    }
)

#Standardise Poor / Moderate / Good
data["actual_quality"] = data["actual_quality"].apply(
    canonical_label
)


#Find the iamge files and match them to the manifest
images = sorted(
    image
    for image in IMAGE_DIR.iterdir()
    if image.suffix.lower() in {".jpg", ".jpeg", ".png"}
)

print(f"Found {len(images)} image files.")


data["saved_filename_clean"] = (
    data["saved_filename"]
    .astype(str)
    .str.strip()
)

data["saved_filename_stem"] = (
    data["saved_filename_clean"]
    .apply(lambda x: Path(x).stem)
)

#Dictionary:
#filename stem -> manifest row

manifest_lookup = {}
for _, row in data.iterrows():

    filename_stem = str(row["saved_filename_stem"]).lower()

    manifest_lookup[filename_stem] = row

photo_records = []

for image_path in images:

    image_stem = image_path.stem.lower()

    if image_stem not in manifest_lookup:
        print(
            f"WARNING: No matching manifest row found for:\n"
            f"    {image_path.name}"
        )
        continue

    row = manifest_lookup[image_stem]

    # Skip photographs for which we cannot find actual quality
    if row["actual_quality"] not in {"poor", "moderate", "good"}:
        print(
            f"WARNING: No valid actual water quality found for:\n"
            f"    {image_path.name}"
        )
        continue

    photo_records.append(
        {
            "image_path": image_path,
            "saved_filename": row["saved_filename"],
            "feature_global_id": row["feature_global_id"],
            "attachment_global_id": row["attachment_global_id"],
            "GlobalID": row["GlobalID"],
            "actual_quality": row["actual_quality"],
        }
    )
    
print(
    f"Successfully matched {len(photo_records)} "
    f"photos to metadata and water quality."
)


#Check that there are actually photos to use
if len(photo_records) == 0:
    raise ValueError(
        "No usable photographs were found after matching "
        "the images to the data."
    )


#See how many photos the person wants to judge
while True:
    response = input(
        f"\nHow many photos would you like to judge? "
        f"(1-{len(photo_records)}): "
    ).strip()

    try:
        number_of_photos = int(response)

        if 1 <= number_of_photos <= len(photo_records):
            break

        print(
            f"Please enter a number between 1 and "
            f"{len(photo_records)}."
        )

    except ValueError:
        print("Please enter a whole number.")


#Select the photos randomly
selected_records = random.sample(
    photo_records,
    number_of_photos,
)

print("Please select Poor, Moderate, Good, or INVALID for each photo.")


#Store the results
records = []

correct_count = 0
incorrect_count = 0
invalid_count = 0


#DEfine a function that can record a guess
def record_guess(guess):
    """
    Record the participant's guess for the current photo.

    Participant choices are:
        - Poor / Moderate
        - Good
        - INVALID

    Poor and Moderate are treated as a single category
    when calculating whether the participant was right.
    However, the original actual quality (Poor/Moderate/Good)
    is retained in the CSV.
    """

    global current_index
    global correct_count
    global incorrect_count
    global invalid_count

    current_record = selected_records[current_index]

    actual_quality = current_record["actual_quality"]

    #What to do if the guess was invalid as this is neither right nor wrong
    if guess == "INVALID":
        guess_right_wrong = ""
        invalid_count += 1
    else:
        #Group the actual water qualities in the global data csv for scoring e.g. the poor and moderate categories are combined.
        if actual_quality in {"poor", "moderate"}:
            actual_group = "poor_moderate"
        elif actual_quality == "good":
            actual_group = "good"
        else:
            actual_group = None

        #Participant's guesses
        if guess == "Poor / Moderate":
            guess_group = "poor_moderate"
        elif guess == "Good":
            guess_group = "good"
        else:
            guess_group = None
        #See if the guess was right or wrong
        if guess_group == actual_group:
            guess_right_wrong = "Right"
            correct_count += 1
        else:
            guess_right_wrong = "Wrong"
            incorrect_count += 1

    #Save the results for this photo

    records.append(
    {
        "saved_filename": current_record["saved_filename"],
        "feature_global_id": current_record["feature_global_id"],
        "attachment_global_id": current_record["attachment_global_id"],
        "GlobalID": current_record["GlobalID"],
        "participant_guess": guess,
        "actual_water_quality": actual_quality.capitalize(),
        "guess_right_wrong": guess_right_wrong,
    }
    )

    #Move on to the next photo
    current_index += 1

    if current_index < len(selected_records):
        show_current_photo()
    else:
        finish_session()

#Show the current photo and the three answer buttons

def show_current_photo():
    """
    Display the current photograph and the answer buttons.
    """

    global current_photo_tk

    record = selected_records[current_index]

    image_path = record["image_path"]

    # Update progress text
    progress_label.config(
        text=(
            f"Photo {current_index + 1} of "
            f"{len(selected_records)}"
        )
    )

    filename_label.config(
        text=image_path.name
    )

    # Load image
    image = Image.open(image_path)

    #Resize image to fit window

    max_width = 800
    max_height = 450

    image.thumbnail(
        (max_width, max_height),
        Image.Resampling.LANCZOS
    )

    current_photo_tk = ImageTk.PhotoImage(image)

    image_label.config(
        image=current_photo_tk
    )

    image_label.image = current_photo_tk


#Finish

def finish_session():
    #Close the image window
    root.destroy()

    #Create results folder if needed
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    #Create a timestamp that the guesses were made at
    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    individual_results_file = (
        RESULTS_DIR
        / f"human_baseline_results_{timestamp}.csv"
    )

    #make a dataframe
    results_df = pd.DataFrame(records)

    #save the individual results to a CSV
    results_df.to_csv(
        individual_results_file,
        index=False,
    )

    #Add them to the overall database
    if OVERALL_RESULTS_FILE.exists():
        overall_df = pd.read_csv(
            OVERALL_RESULTS_FILE
        )

        overall_df = pd.concat(
            [overall_df, results_df],
            ignore_index=True,
        )
    else:
        overall_df = results_df.copy()

    overall_df.to_csv(
        OVERALL_RESULTS_FILE,
        index=False,
    )

    #Calculate participant accuracy

    valid_guesses = correct_count + incorrect_count

    if valid_guesses > 0:
        participant_accuracy = (
            correct_count / valid_guesses
        ) * 100
    else:
        participant_accuracy = 0

    #Work out the overall accuracy
    overall_valid = (
        overall_df["guess_right_wrong"]
        .isin(["Right", "Wrong"])
    )

    overall_correct = (
        (
            overall_df["guess_right_wrong"]
            == "Right"
        )
        & overall_valid
    ).sum()

    overall_incorrect = (
        (
            overall_df["guess_right_wrong"]
            == "Wrong"
        )
        & overall_valid
    ).sum()

    overall_valid_guesses = (
        overall_correct + overall_incorrect
    )

    if overall_valid_guesses > 0:
        overall_accuracy = (
            overall_correct
            / overall_valid_guesses
        ) * 100
    else:
        overall_accuracy = 0

   
    #Print statements for the results
    print("\n")
    print("=" * 60)
    print("HUMAN BASELINE RESULTS")
    print("=" * 60)

    print(
        f"Correct guesses:   {correct_count}"
    )

    print(
        f"Incorrect guesses: {incorrect_count}"
    )

    print(
        f"Invalid guesses:   {invalid_count}"
    )

    print(
        f"Participant accuracy: "
        f"{participant_accuracy:.2f}%"
    )

    print()
    print(
        f"Overall correct guesses:   "
        f"{overall_correct}"
    )

    print(
        f"Overall incorrect guesses: "
        f"{overall_incorrect}"
    )

    print(
        f"Overall accuracy: "
        f"{overall_accuracy:.2f}%"
    )

    print()
    print(
        f"Individual results saved to:\n"
        f"{individual_results_file}"
    )

    print()
    print(
        f"Overall results saved to:\n"
        f"{OVERALL_RESULTS_FILE}"
    )

    print("=" * 60)

    #Display results to the participant in a small window
    result_message = (
        "Your results\n\n"
        f"Correct: {correct_count}\n"
        f"Incorrect: {incorrect_count}\n"
        f"Invalid: {invalid_count}\n\n"
        f"Your accuracy: {participant_accuracy:.2f}%\n\n"
        f"Overall accuracy across all participants: "
        f"{overall_accuracy:.2f}%"
    )

    #Create a small results window
    results_root = tk.Tk()
    results_root.title(
        "Human Baseline Results"
    )
    results_root.geometry(
        "500x350"
    )
    results_label = tk.Label(
        results_root,
        text=result_message,
        font=("Arial", 14),
        justify="center",
        padx=20,
        pady=20,
    )
    results_label.pack(
        expand=True
    )
    close_button = tk.Button(
        results_root,
        text="Close",
        font=("Arial", 12),
        command=results_root.destroy,
        width=15,
    )
    close_button.pack(
        pady=20
    )
    results_root.mainloop()


#Make a GUI (graphical user interface) for the main image judgement window

root = tk.Tk()
root.title(
    "Human Baseline Water Quality Judgement"
)
root.geometry(
    "900x750"
)
root.configure(
    padx=20,
    pady=20,
)

current_index = 0
current_photo_tk = None

#Progress label to show which photo the participant is on
progress_label = tk.Label(
    root,
    text="",
    font=("Arial", 18, "bold"),
)
progress_label.pack(
    pady=(0, 10)
)

filename_label = tk.Label(
    root,
    text="",
    font=("Arial", 10),
)
filename_label.pack(
    pady=(0, 10)
)

image_label = tk.Label(
    root,
    text="Loading image...",
)
image_label.pack(
    expand=True
)


#Instructions - check this 
instructions_label = tk.Label(
    root,
    text=(
        "What is the water quality shown in this photograph?\n"
        "Choose POOR / MODERATE or GOOD.\n"
        "Select INVALID if the photograph does not show the waterbody."
    ),
    font=("Arial", 13),
    justify="center",
)
instructions_label.pack(
    pady=15
)


#Buttons
button_frame = tk.Frame(
    root
)
button_frame.pack(
    pady=10
)
poor_moderate_button = tk.Button(
    button_frame,
    text="POOR / MODERATE",
    font=("Arial", 14, "bold"),
    width=18,
    height=2,
    command=lambda: record_guess("Poor / Moderate"),
)

poor_moderate_button.grid(
    row=0,
    column=0,
    padx=10,
)


good_button = tk.Button(
    button_frame,
    text="GOOD",
    font=("Arial", 14, "bold"),
    width=18,
    height=2,
    command=lambda: record_guess("Good"),
)

good_button.grid(
    row=0,
    column=1,
    padx=10,
)


invalid_button = tk.Button(
    button_frame,
    text="INVALID",
    font=("Arial", 14, "bold"),
    width=18,
    height=2,
    command=lambda: record_guess("INVALID"),
)

invalid_button.grid(
    row=0,
    column=2,
    padx=10,
)


#Show the first photo
show_current_photo()


#Start the GUI
root.mainloop()