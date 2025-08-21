# **Phone Number Cleanup Tool**

The **Phone Number Cleanup Tool** is designed to streamline the process of verifying and filtering the leads based on the specific column conditions.

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [How to Use](#how-to-use-phone-number-cleanup-tool)
- [Troubleshooting](#troubleshooting)

---

## Features
- Filters the leads from the input files based on the following `column conditions`:
   - `in_pipedrive` - Y
   - `rc_pd` - Yes
   - `type` and `carrier_type` - both landline
   - `text_opt_in` - No
   - `contact_deal_id` - not empty/blank
   - `contact_deal_status` -  not empty/blank
   - `contact_person_id` -  not empty/blank
   - `phone_number_deal_id` -  not empty/blank
   - `phone_number_deal_status` -  not empty/blank
   - `RVM - Last RVM Date` - last 7 days from tool run date
   - `Latest Text Marketing Date (Sent)` - last 7 days from tool run date
   - `Rolling 30 Days Rvm Count` and `Rolling 30 Days Text Marketing Count` - total =>3
   - `Deal - ID` - not empty/blank
   - `Deal - Text Opt-in` - No
- Once the lead falls into any of these column conditions, they will be tagged accordingly via the output column `reason_for_removal`
- Output file format will be based upon the input file format:
   - If the input file is in `.csv` file format, the output file will be in `.csv` file format
   - If the input file is in `.xlsx` file format, the output file will be in `.xlsx` file format
- The filename of the output file will have a prefix of `(With Cleanup Tagging)`
- Output file includes the following columns:
   - `phone_number`
   - `contact_id`
   - `carrier_type`
   - `full_name`
   - `first_name`
   - `last_name`
   - `target_county`
   - `target_state`
   - `phone_index`
   - `time_zone`
   - `reason_for_removal`

---

## Requirements

- **Appropriate Input Files Format**  
  Ensure that the columns of the input files includes the `column conditions` in the [Features](#features) section

---

## How to Use Phone Number Cleanup Tool

1. **Select Phone Number Cleanup Tool**  
   Click `Phone Number Cleanup Tool` from the tool selection area in the left-hand side of the application UI.

2. **Select Input Files**  
   From the tool interface area in the right-hand side, select the input files by clicking `Select files to process` button. You can select multiple input files all at once.  
   
   **IMPORTANT NOTE!**
      - If you cannot see the input file that you are looking for, you can adjust the file filter in the `Select a file` pop up window by clicking the `CSV Files` above the `Open` and `Cancel` button. Then, select the appropriate file format for your input file.
      - If your input files are in .csv file format, make sure you have saved the .csv file in `UTF-8` Encoding.
      - You can do this by clicking the `Save as` button in Microsoft Excel, then click `Save as type`, then select `CSV UTF-8 (Comma delimited)`.

3. **Where to Save Output Files**  
   Click the `Save output files to` button to define where you want the output files to be saved into once the tool is done processing the input files.

4. **Run The Tool**  
   After defining the input files and save directory, you can now click `RUN TOOL` and wait for the tool to finish processing the files.

5. **Review Output Data**  
   Go the the save directory that you have defined earlier and review the output files.

6. **Accomplish the Output Checklist**
    - If the tool run is successful, an **Output Checklist** window should pop up.
    - This list will guide you on what to check and verify from the output file(s) of the tool.
    - Click `confirm` button at the bottom of the window after you've checked all of the **Output Checklist's** checkboxes.

---

## Troubleshooting

For any issues, check the error logs in the console window and contact **Armiel Gonzales** via **Slack** or contact your supervisor.

---
