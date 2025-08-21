# **AutoDialer Cleanup Tool**

The **AutoDialer Cleanup Tool** automates the process of cleaning up the phone list for AutoDialer based on a pre-defined list cleaner file.

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [How to Use](#how-to-use-autodialer-cleanup-tool)
- [Troubleshooting](#troubleshooting)

---

## Features
- Cleans out the entries from `AutoDialer List File` if it is existing on a pre-defined list cleaner file.
- Tool grabs the columns `phone1` to `phone5` from the files that it is gonna clean.
- Then it will search if it is existing in the `List Cleaner File`. Those existing phone number in the `List Cleaner File` will be removed from the `AutoDialer List File`.
- Tool will search existing phone numbers from the following tabs/sheets of `List Cleaner File`:  
    - `ContMgt+MVP+JC+PD+RC`
    - `DNC`
    - `SMS-Sent`
    - `Outbound-2weeks`
    - `FromOtherList`
- Tool will also filter out the generated output file to specific primary dispositions from Max Outbound Calls table:
    - `Business/ Work number`
    - `Sold Interests`
    - `Incorrect contact / Wrong number`
    - `Fax, Invalid Number, Proactive Identified - Fax`
    - `Do Not Call Again (remove from list)`
    - `Lead Not interested`
    - `Uncooperative Lead`
- No additional columns will be added from the cleaned output file of `AutoDialer List File`.
- Cleaned output file of the tool will have a prefix of `(Clean file)` + the original filename of the input file.

---

## Requirements

- **Appropriate Input Files Format**  
    - Ensure that the `AutoDialer List File` contains the columns `phone1` to `phone5`, as the tool will use these columns to search it in the `List Cleaner File`.
    - Also, ensure that the `List Cleaner File` contains the tabs/sheets mentioned in the [Features](#features) section.

---

## How to Use AutoDialer Cleanup Tool

1. **Select AutoDialer Cleanup Tool**  
    Click `AutoDialer Cleanup Tool` from the tool selection area in the left-hand side of the application UI.

2. **Select List Cleaner File**  
    From the tool interface area in the right-hand side, select the list cleaner file by clicking `Select list cleaner file` button.
    
2. **Select Input Files**  
    From the tool interface area in the right-hand side, select the files to be cleaned by clicking `Select files to clean` button. You can select multiple files to be cleaned and process all at once.
   
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
