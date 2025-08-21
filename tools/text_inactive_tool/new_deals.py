import warnings
import pandas as pd


def add_email_columns(cm_db_exist: pd.DataFrame, email_address_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Adds Email 1 to Email 17 columns to the final dataframe.\n

    Parameters:
        `cm_db_exist (pd.DataFrame)` - Pandas DataFrame that contains ANI Numbers and other details that is existing in CM Database.\n
        `email_address_df (pd.DataFrame)` - Pandas DataFrame that contains all email entries and corresponding database id from CM Database.\n

    Return:
        `cm_db_final_df (pd.DataFrame)` - Final dataframe that contains all emails per ANI Number and will be added more columns based on specification.\n
    '''

    # Create Email 1 to Email 17 Columns
    email_cols = [
        'Deal - Unique Database ID',
    ] + [f'Person - Email {i}' for i in range(1, 18)]
    cm_db_email_columns = pd.DataFrame(columns=email_cols)

    # Filter Email Address Dataframe from Community Minerals Database
    filter_email_address_df = email_address_df[email_address_df['id'].isin(cm_db_exist['id'])]

    # Group by id and get the grouped emails
    grouped = filter_email_address_df.groupby('id')['email_address'].apply(list).reset_index()

    # Flatten the emails for easier processing
    emails_flat = []
    for _, row in grouped.iterrows():
        id = row['id']
        emails = row['email_address'][:17]  # Take only the first 17 emails
        emails_flat.append((id, emails))

    # Fill bottoms_up_final_df with the flattened email data
    rows_to_add = []
    for id, emails in emails_flat:
        # Create a dictionary for the row data
        row_data = {'Deal - Unique Database ID': id}
        row_data.update({f'Person - Email {i+1}': email for i, email in enumerate(emails)})
        rows_to_add.append(row_data)

    # Append rows to bottoms_up_final_df using pd.concat
    email_address_final_df = pd.concat([cm_db_email_columns, pd.DataFrame(rows_to_add)], ignore_index=True).drop_duplicates()

    # Add email address dataframe to the final dataframe
    cm_db_final_df = cm_db_exist.merge(email_address_final_df,
                                        left_on='id',
                                        right_on='Deal - Unique Database ID',
                                        how='left')

    return cm_db_final_df


def add_serial_number(cm_db_final_df: pd.DataFrame, serial_numbers_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Adds `Deal - Serial Number` column to the final dataframe.\n

    Parameters:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added emails column.\n

    Return:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added `Deal - Serial Number` column.\n
    '''

    # Merge serial numbers dataframe from CM Database to final dataframe
    cm_db_final_df = cm_db_final_df.merge(serial_numbers_df,
                                        left_on='Deal - Unique Database ID',
                                        right_on='id',
                                        how='left').rename(columns={'serial_numbers': 'Deal - Serial Number'})

    return cm_db_final_df


def add_cm_db_details(cm_db_final_df: pd.DataFrame, cm_db_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Merges the rest of the column needed from the CM Database to the final dataframe.\n

    Parameters:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with column based on specifications.\n
        `cm_db_df (pd.DataFrame)` - Pandas Dataframe equivalent of data from CM Database.\n

    Return:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added CM Database columns.\n
    '''

    # Merge the rest of the column from CM Database to final dataframe
    cm_db_df.rename(columns={'id': 'Deal - Unique Database ID'}, inplace=True)
    cm_db_final_df = cm_db_final_df.merge(cm_db_df,
                                        on='Deal - Unique Database ID',
                                        how='left')

    return cm_db_final_df


def add_new_database_id(cm_db_final_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Adds `Deal - Unique Database ID` column to the final dataframe.\n

    Parameters:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added CM Database details.\n

    Return:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added `Deal - Unique Database ID` column.\n
    '''

    # Define pandas function that will add deal unique database ID
    def assign_check_id(group):
        if group['Deal - Unique Database ID'].nunique() == 0:
            return None
        elif group['Deal - Unique Database ID'].nunique() == 1:
            return group['Deal - Unique Database ID'].iloc[0]
        else:
            return 'Multiple Database ID'

    # Apply pandas function and assign to a column
    new_db_id = cm_db_final_df.groupby('Phone').apply(assign_check_id).reset_index()
    new_db_id.columns = ['Phone', 'new_db_id']
    cm_db_final_df = cm_db_final_df.merge(new_db_id, on='Phone', how='left')
    cm_db_final_df.drop('Deal - Unique Database ID', axis=1, inplace=True)
    cm_db_final_df.rename(columns={'new_db_id': 'Deal - Unique Database ID'}, inplace=True)

    return cm_db_final_df


def add_deal_title(cm_db_final_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Adds `Deal - Title` column to the final dataframe.\n

    Parameters:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added `Deal - Unique Database ID` column.\n
    
    Return:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added `Deal - Title` column.\n
    '''

    # Combine first and last name and assign to column
    cm_db_final_df['first_last'] = cm_db_final_df.apply(lambda row: 
        row['first_name'].title() if pd.notna(row['first_name']) and pd.isna(row['last_name']) else 
        (row['first_name'].title() + ' ' + row['last_name'].title()) if pd.notna(row['first_name']) and pd.notna(row['last_name']) else 
        '', axis=1)

    grouped = cm_db_final_df.groupby(['Phone', 'state'])['country'].apply(list).reset_index()

    # Function to format the county names
    def format_counties(counties):
        unique_counties = list(set(counties))
        n = len(unique_counties)
        if n == 1:
            return unique_counties[0].title() + " County"
        elif n == 2:
            return unique_counties[0].title() + " and " + unique_counties[1].title() + " County"
        elif n > 2:
            return ', '.join([county.title() for county in unique_counties[:-1]]) + " and " + unique_counties[-1].title() + " County"

    # Apply the formatting function to the grouped data
    grouped['formatted'] = grouped['country'].apply(format_counties)

    aggregated = grouped.groupby('Phone').apply(
        lambda x: ' and '.join([f"{row['formatted']}, {row['state'].upper()}" for _, row in x.iterrows()])
    ).reset_index(name='formatted_result')
    final_result = cm_db_final_df[['Phone', 'first_last']].drop_duplicates().merge(aggregated, on='Phone', how='left')
    final_result['Deal - Title'] = final_result.apply(lambda row: f"{row['first_last']} {row['formatted_result']}", axis=1)
    cm_db_final_df = cm_db_final_df.merge(final_result[['Phone', 'Deal - Title']], on='Phone', how='left')


    return cm_db_final_df


def add_deal_county(cm_db_final_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Adds `Deal - County` column to the final dataframe.\n

    Parameters:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added `Deal - Title` column.\n
    
    Return:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added `Deal - County` column.\n
    '''

    # Define pandas function that will create deal county column
    def add_county(group):

        # if group['state'].nunique() > 1:

        country_list = group['country'].tolist()
        state_list = group['state'].tolist()

        # Create a set of unique (country, state) pairs
        unique_combinations = set((country.title(), state) for country, state in zip(country_list, state_list))

        # Join the unique combinations into a formatted string
        result = '|'.join([f"{country} County, {state}" for country, state in unique_combinations])

        return result

    # Create the "Deal - County" for unique phone numbers
    unique_deals = cm_db_final_df.groupby('Phone').apply(add_county).reset_index()
    unique_deals.columns = ['Phone', 'Deal - County']
    cm_db_final_df = cm_db_final_df.merge(unique_deals, on='Phone', how='left')

    return cm_db_final_df


def add_mailing_address(cm_db_final_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Adds `Person - Mailing Address` column to the final dataframe.\n

    Parameters:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added `Deal - County` column.\n

    Return:
        `cm_db_final_df (pd.DataFrame)` - Reference variable of a Pandas DataFrame with added `Person - Mailing Address` column.\n
    '''

    # Define pandas function that will create person mailing address
    def add_mailing_address(row):

        if row['address'].nunique() == 0:
            return None
        elif row['address'].nunique() == 1:
            if row['address'].iloc[0] != '':
                return f"{row['address'].iloc[0]}, {row['city'].iloc[0]}, {row['state_address'].iloc[0]}, {row['postal_code'].iloc[0]}, USA"
            else:
                return None
        else:
            return "Multiple address entries"
    
    # Apply pandas function and assign to a column
    mailing_address = cm_db_final_df.groupby('Phone').apply(add_mailing_address).reset_index()
    mailing_address.columns = ['Phone', 'Person - Mailing Address']
    cm_db_final_df = cm_db_final_df.merge(mailing_address, on='Phone', how='left')

    return cm_db_final_df


def add_person_name(cm_db_final_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Adds `Person - Name` column to the final dataframe.\n

    Parameters:
        `cm_db_final_df (pd.DataFrame)` - Final output dataframe that contains columns based on specifications.\n

    Return:
        `cm_db_final_df (pd.DataFrame)` - Dataframe with added `Person - Name` column.\n
    '''

    # Define pandas function that will create person name
    def process_names(row):
        first_name = row['first_name']
        middle_name = row['middle_name']
        last_name = row['last_name']
        
        if pd.notna(first_name) and pd.isna(last_name):
            # Split and capitalize each word in first_name
            return ' '.join([part.title() for part in first_name.split()])
        
        elif pd.notna(first_name) and pd.notna(last_name):
            if pd.notna(middle_name):
                # Capitalize first_name, middle_name, last_name and join with space
                return ' '.join([part.title() for part in [first_name, middle_name, last_name]])
            else:
                # Capitalize first_name and last_name and join with space
                return f"{first_name.title()} {last_name.title()}"
        
        else:
            return None  # or any other handling for NaN values

    # Apply the function to create the new column
    cm_db_final_df['Person - Name'] = cm_db_final_df.apply(process_names, axis=1)

    
    return cm_db_final_df


def add_constant_columns(cm_db_final_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Adds columns to the final dataframe where values are all constants.\n

    Parameters:
        `cm_db_final_df (pd.DataFrame)` - Final output dataframe that contains columns based on specifications.\n

    Return:
        `cm_db_final_df (pd.DataFrame)` - Dataframe with added constant columns.\n
    '''

    # Define and add constant columns to the final dataframe
    cm_db_final_df['Person - Phone'] = cm_db_final_df['Phone']
    cm_db_final_df['Person - Phone 1'] = cm_db_final_df['Phone']
    cm_db_final_df['Person - Email'] = cm_db_final_df['Person - Email 1']
    cm_db_final_df['Deal - Label'] = 'Text Inactive - For Review'
    cm_db_final_df['Deal - Preferred Communication Method'] = 'Phone'
    cm_db_final_df['Deal - Abandoned Call Flag'] = 'Abandoned Call - Call Center'
    cm_db_final_df['Deal - Inbound Medium'] = 'SMS'
    cm_db_final_df['Deal - Deal Summary'] = 'Completed'
    cm_db_final_df['Deal - Pipedrive Analyst Tracking Flag'] = 'PA - Joyce'
    cm_db_final_df['Deal - Phone Number Format'] = 'Complete'
    cm_db_final_df['Person - Phone 1 - Data Source'] = 'Mineral Owner'
    cm_db_final_df['Person - Mailing Address - Data Source'] = cm_db_final_df['data_source']
    cm_db_final_df['Deal - Deal Status'] = cm_db_final_df['Deal Status']
    cm_db_final_df['Person - Timezone'] = ''
    cm_db_final_df['Deal - Marketing Medium'] = 'Text'
    cm_db_final_df['Deal - Deal Stage'] = 'Inactive'
    cm_db_final_df['Deal - Non-voice Qualification Channel'] = cm_db_final_df['Non-voice Qualification Channel']
    cm_db_final_df['Deal - Reason for Not Selling'] = cm_db_final_df['Reason for Not Selling']
    cm_db_final_df['Deal - Contact Confirmation'] = cm_db_final_df['Contact Confirmation']
    cm_db_final_df['Notes'] = ''
    cm_db_final_df['Activity note'] = cm_db_final_df['Note']
    cm_db_final_df['Assigned to user'] = 'Data Team'
    cm_db_final_df['Done'] = 'Done'
    cm_db_final_df['Type'] = 'Text'
    cm_db_final_df['Due date'] = cm_db_final_df['Activity - Due date']
    cm_db_final_df['Deal ID'] = ''
    cm_db_final_df['Note Content'] = ''
    cm_db_final_df['Subject'] = cm_db_final_df['Activity - Subject']
    cm_db_final_df.drop_duplicates(subset=['Phone'], inplace=True)


    return cm_db_final_df


def tag_multi_result(df: pd.DataFrame) -> pd.DataFrame:

    # Tagging of multi result or new deals
    df['Note (if any)'] = df.apply(
            lambda row: 'Multiple Result' if (pd.notna(row['Person - Mailing Address'])) and ('Multiple' in row['Person - Mailing Address'] or isinstance(row['Deal - Unique Database ID'], str)) else 'New Deal',
            axis=1
        )
    
    # No name tags
    df['Deal - Title'] = df.apply(
            lambda row: f"No Name {row['Phone']}" if (pd.notna(row['Person - Mailing Address'])) and ('Multiple' in row['Person - Mailing Address'] or isinstance(row['Deal - Unique Database ID'], str)) else row['Deal - Title'],
            axis=1
        )
    df['Person - Name'] = df.apply(
            lambda row: f"No Name {row['Phone']}" if (pd.notna(row['Person - Mailing Address'])) and ('Multiple' in row['Person - Mailing Address'] or isinstance(row['Deal - Unique Database ID'], str)) else row['Person - Name'],
            axis=1
        )
    
    df['Deal - Deal Summary'] = df.apply(
            lambda row: f'Common Name Error' if (pd.notna(row['Person - Mailing Address'])) and ('Multiple' in row['Person - Mailing Address'] or isinstance(row['Deal - Unique Database ID'], str)) else row['Deal - Deal Summary'],
            axis=1
        )
    
    # List of columns to clear when "Multiple" is found
    columns_to_clear = ['Deal - County',
                        'Deal - Serial Number',
                        'Deal - Unique Database ID',
                        'Person - Mailing Address']

    # Apply the condition
    df[columns_to_clear] = df.apply(
        lambda row: [''] * len(columns_to_clear) if (pd.notna(row['Person - Mailing Address'])) and ('Multiple' in row['Person - Mailing Address'] or isinstance(row['Deal - Unique Database ID'], str)) else row[columns_to_clear],
        axis=1
    )

    return df

def no_result_constants(df: pd.DataFrame) -> pd.DataFrame:

    df.drop_duplicates(subset=['Phone'], inplace=True)
    df['Person - Phone'] = df['Phone']
    df['Person - Phone 1'] = df['Phone']
    df['Deal - Label'] = 'Text Inactive - For Review'
    df['Deal - Preferred Communication Method'] = 'Phone'
    df['Deal - Abandoned Call Flag'] = 'Abandoned Call - Call Center'
    df['Deal - Inbound Medium'] = 'SMS'
    df['Deal - Deal Summary'] = 'No Information in Email'
    df['Deal - Pipedrive Analyst Tracking Flag'] = 'PA - Joyce'
    df['Deal - Phone Number Format'] = 'Complete'
    df['Person - Phone 1 - Data Source'] = 'Mineral Owner'
    df['Deal - Deal Status'] = df['Deal Status']
    df['Person - Timezone'] = ''
    df['Deal - Marketing Medium'] = 'Text'
    df['Deal - Deal Stage'] = 'Inactive'
    df['Deal - Non-voice Qualification Channel'] = df['Non-voice Qualification Channel']
    df['Deal - Reason for Not Selling'] = df['Reason for Not Selling']
    df['Deal - Contact Confirmation'] = df['Contact Confirmation']
    df['Notes'] = ''
    df['Activity note'] = df['Note']
    df['Assigned to user'] = 'Data Team'
    df['Done'] = 'Done'
    df['Type'] = 'Text'
    df['Due date'] = df['Activity - Due date']
    df['Deal ID'] = ''
    df['Note Content'] = ''
    df['Subject'] = df['Activity - Subject']
    df['Deal - Title'] = df.apply(lambda x: f"No Name {x['Phone']}", axis=1)
    df['Person - Name'] = df.apply(lambda x: f"No Name {x['Phone']}", axis=1)
    df['Note (if any)'] = 'No Result'

    return df

def get_timezone(row, tz_dict: dict):
    phone_number = row.get('Person - Phone 1')
    
    # Ensure the phone number is not null and convert it to a string if needed
    if pd.notna(phone_number):
        phone_number = str(phone_number)  # Convert to string if it's not already
        
        if len(phone_number) >= 3:
            area_code = phone_number[:3]  # Get the first 3 digits
            if area_code in tz_dict:
                return tz_dict[area_code]
    
    return None  # Return None if conditions aren't met

def get_timezone_dict() -> dict:

    timezone_df = pd.read_csv("./data/tz_file/Time Zones.csv", low_memory=False)
    timezone_df['area_code'] = timezone_df['area_code'].astype('string')
    timezone_dict = timezone_df.set_index('area_code')['pipedrive_eq'].to_dict()

    return timezone_dict

def process_new_deals(no_deal_id_final: pd.DataFrame,
                      cm_db_not_exist: pd.DataFrame,
                      email_address_df: pd.DataFrame,
                      serial_numbers_df: pd.DataFrame,
                      cm_db_df: pd.DataFrame,
                      save_path: str,
                      i: int) -> None:
    
    if no_deal_id_final.empty and cm_db_not_exist.empty:
        return None
    
    output_columns = [
        'Deal - Title',
        'Deal - Label',
        'Deal - Deal Stage',
        'Deal - County',
        'Deal - Preferred Communication Method',
        'Deal - Inbound Medium',
        'Deal - Serial Number',
        'Deal - Unique Database ID',
        'Deal - Marketing Medium',
        'Deal - Deal Summary',
        'Deal - Deal Status',
        'Deal - Non-voice Qualification Channel',
        'Deal - Reason for Not Selling',
        'Deal - Contact Confirmation',
        'Notes',
        'Deal - Pipedrive Analyst Tracking Flag',
        'Deal - Phone Number Format',
        'Person - Name',
        'Person - Mailing Address',
        'Person - Email',
        'Person - Email 1',
        'Person - Email 2',
        'Person - Email 3',
        'Person - Email 4',
        'Person - Email 5',
        'Person - Email 6',
        'Person - Email 7',
        'Person - Email 8',
        'Person - Email 9',
        'Person - Email 10',
        'Person - Email 11',
        'Person - Email 12',
        'Person - Email 13',
        'Person - Email 14',
        'Person - Email 15',
        'Person - Email 16',
        'Person - Email 17',
        'Person - Phone',
        'Person - Phone 1',
        'Note Content',
        'Person - Mailing Address - Data Source',
        'Person - Phone 1 - Data Source',
        'Activity note',
        'Assigned to user',
        'Done',
        'Subject',
        'Type',
        'Due date',
        'Deal ID',
        'Note (if any)',
        'Person - Timezone'
    ]

    # New Deals and Multiple result
    if not no_deal_id_final.empty:
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        no_deal_id_final['id'] = no_deal_id_final['id']
        no_deal_id_final = no_deal_id_final[[
            'Activity - Subject',
            'Note',
            'Activity - Due date',
            'Phone',
            'Stage',
            'Marketing Medium',
            'Inbound Medium',
            'Non-voice Qualification Channel',
            'QA Tracking Flag',
            'Deal Status',
            'Reason for Not Selling',
            'Contact Confirmation',
            'id'
            ]]

        added_email_df = add_email_columns(no_deal_id_final, email_address_df)
        added_serials_df = add_serial_number(added_email_df, serial_numbers_df)
        added_cm_db_details_df = add_cm_db_details(added_serials_df, cm_db_df)
        added_new_db_id_df = add_new_database_id(added_cm_db_details_df)
        added_deal_title_df = add_deal_title(added_new_db_id_df)
        added_deal_county_df = add_deal_county(added_deal_title_df)
        added_mailing_address_df = add_mailing_address(added_deal_county_df)
        added_person_name_df = add_person_name(added_mailing_address_df)
        added_constants_df = add_constant_columns(added_person_name_df)
        multi_tagged_df = tag_multi_result(added_constants_df)
    else:
        multi_tagged_df = pd.DataFrame(columns=output_columns)

    # No Result
    if not cm_db_not_exist.empty:
        no_result_df = no_result_constants(cm_db_not_exist)
    else:
        no_result_df = pd.DataFrame(columns=output_columns)

    # Combine new deals, multiple result and no result
    final_new_deals_df = pd.concat([multi_tagged_df, no_result_df])
    timezone_dict = get_timezone_dict()
    final_new_deals_df['Person - Timezone'] = final_new_deals_df.apply(get_timezone,
                                                                    tz_dict=timezone_dict,
                                                                    axis=1)
    new_deals_export_df = final_new_deals_df[output_columns].sort_values(by=['Due date'])

    print("Creating New Deals")

    new_deals_export_df.to_excel(f'{save_path}/{i}. New Deals - Text Inactive.xlsx', index=False)

if __name__ == "__main__":
    process_new_deals()
