# **Missing Deals Tool**

The **Missing Deals Tool** is designed to process Missing Deals Texts and creates a follow up or new deals in Pipedrive CRM.

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [How to Use](#how-to-use-missing-deals-tool)
- [Troubleshooting](#troubleshooting)

---

## Features

- Reads the Missing Deals (Live or Inactive) input file and parses the column `From`.
- Tool will then cross verify this `Phone` value in Pipedrive CRM if it has an existing deal.
- Those Missing Deals that has existing deals in Pipedrive will go into the output file `FU - Missing Deals`.
- Output file `FU - Missing Deals` will have the following columns:
    - `Activity note` - inherits the value from the input file column `Text`
    - `Assigned to user` - constant value of `Keena`
    - `Done` - constant value of `Done`
    - `Subject` - inherits the value from the input file column `From` and `To`
    - `Type` - constant value of `Text`
    - `Due date` - inherits the value from the input file column `Deal Created Date`
    - `Deal ID` - value will be extracted from Pipedrive thru API and multiple Deal ID values per phone number will be separated by ` | `
- While for those that does not have any exisiting deal will fall into the output file `New Deals - Missing Deals`.
- Phone numbers of leads from the `New Deals - Missing Deals` will then be searched in Community Minerals Database.
- Those with existing contact information will have a tag of `New Deals` from the column `Note (if any)`.
- Those with multiple contact information will have a tag of `Multiple Result` from the column `Note (if any)`.
- And for those who do not have any contact information will be tagged `No Result` from the column `Note (if any)`.
- Here are some of the key columns to look for output file `New Deals - Missing Deals`:  
    - `Deal - Title` - combined values of columns `Person - Name` and `Deal - County`
    - `Deal - Deal Stage` - `Deals to Process` if input file is Live, `Inactive - Conversion` if input file is Inactive
    - `Deal - County` - contains all of the counties and state for each of the contacts
    - `Deal - Unique Database ID` - a unique identifier for each of the contacts in the database
    - `Person - Name` - full name of the contact
    - `Person - Mailing Address` - full mailing address of the contact
    - `Person Email` to `Person - Email 17` - all of the unique emails of each of the contacts
    - `Person - Phone` - phone number of the contact
    - `Activity note` - inherits the value from the input file column `Text`
    - `Subject` - inherits the value from the input file column `From` and `To`
    - `Note (if any)` - contains any of these values: `New Deal`, `Multiple Result` or `No Result`
    - `Person - Timezone` - corresponding timezone based on the first 3 digits of the phone number of the contact
- This tool also a lookup functionality that will fillup the deals of each of the phone number from the Missing Deals List

---

## Requirements

- **Appropriate Input Files Format**  
    Missing Deals tool accepts two types file file: Live and Inactive. Ensure that the following columns exists in the input files:
    - `From`
    - `To`
    - `Text`
    - `Deal Created date`
    - `Stage`
    - `Deal Status`
    - `Reason for Not Selling`
    - `Contact Confirmation`
    - `Marketing Medium`
    - `Inbound Medium`
    - `Non-voice Qualification Channel`
    - `QC Status`
    - `Quality Control Tracking Flag`
    - `Call Review Date`

- **Time Zone File**  
    This tool has a feature that it converts the first 3 digits of the lead's phone number into a corresponding time zone. Make that you have saved the **Time Zone.csv** file in this directory ***C:\Program Files (x86)\Lead Management Tools\data\tz_file***

- **Community Minerals Pipedrive Account**  
    Make sure you have an account in Pipedrive issued by Community Minerals admins, as the tool will need the ***Pipedrive API*** from your Pipedrive Account to streamline the process of verifying the leads in Pipedrive CRM thru API Calls.

- **Community Minerals Database Credentials**  
    Lastly, you should have the credentials for a database user in Community Minerals database. This user should have proper grants and authorization in order for the tool to communicate with the database and extract the needed data. Contact the database admin if you don't have your database user credentials yet.

---

## How to Use Missing Deals Tool

1. **Select Missing Deals Tool**  
   After opening the app, click `Missing Deals Tool` from the tool selection area in the left-hand side of the application UI.

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

5. **Run Lookup**
    After you're done processing all of the follow ups and new deals, you can run the lookup functionality. Make sure to use the missing deals list file as the input file.

6. **Review Output Data**  
    Go the the save directory that you have defined earlier and review the output files.

7. **Accomplish the Output Checklist**
    - If the tool run is successful, an **Output Checklist** window should pop up.
    - This list will guide you on what to check and verify from the output file(s) of the tool.
    - Click `confirm` button at the bottom of the window after you've checked all of the **Output Checklist's** checkboxes.

---

## Troubleshooting

For any issues, check the error logs in the console window and contact **Armiel Gonzales** via **Slack** or contact your supervisor.

---
