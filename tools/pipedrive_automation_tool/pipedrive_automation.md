# **Pipedrive Automation Tool**

The **Pipedrive Automation Tool** streamlines the process of verifying the contact details of each deals from Pipedrive CRM.

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [How to Use](#how-to-use-pipedrive-automation-tool)
- [Troubleshooting](#troubleshooting)

---

## Features

- Parses the column **Deal - Unique Database ID** from the input file and cross verifies the values to the database.
- Tool will extract the following data from the database for matching **database ID**:  
    - `Serial Numbers`
    - `Phone Numbers`
    - `Full Mailing Address`
    - `Email Address`
- After extracting these values from the database, tool will then update the values of the corresponding columns from the input file, effectively reducing the manual work of searching and updating the contact details of each of the deals from the input file.
- Output file contains ***70 columns*** and here are some of the key columns to look for:  
    - `Deal - Serial Number` - deal's unique serial numbers separated by `|`
    - `Person - Timezone` - corresponding time zone derived from the given phone number of the contact
    - `Person - Mailing Address` - full mailing address of the contact
    - `Person - Phone 1` - main phone number of the contact
    - `Person - Email 1` - main email address of the contact

---

## Requirements

- **Appropriate Input Files Format**  
    Ensure that you are using the file downloaded from **For Automation** filter of Community Minerals' Pipedrive.

- **Time Zone File**  
    This tool has a feature that it converts the first 3 digits of the lead's phone number into a corresponding time zone. Make that you have saved the **Time Zone.csv** file in this directory ***C:\Program Files (x86)\Lead Management Tools\data\tz_file***

- **Community Minerals Pipedrive Account**  
    Make sure you have an account in Pipedrive issued by Community Minerals admins, as the tool will need the input file downloaded from the filter **For Automation**.

- **Community Minerals Database Credentials**  
    Lastly, you should have the credentials for a database user in Community Minerals database. This user should have proper grants and authorization in order for the tool to communicate with the database and extract the needed data. Contact the database admin if you don't have your database user credentials yet.

---

## How to Use Pipedrive Automation Tool

1. **Select Pipedrive Automation Tool**  
   After opening the app, click `Pipedrive Automation Tool` from the tool selection area in the left-hand side of the application UI.

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
