import os
import pandas as pd
import numpy as np
import warnings
from rapidfuzz import process, fuzz
from sqlalchemy import create_engine
from urllib.parse import quote

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None

def read_file(path: str):
    if path.endswith('.csv'):
        return pd.read_csv(path, low_memory=False)
    elif path.endswith('.xlsx'):
        return pd.read_excel(path)
    else:
        raise RuntimeError("Incorrect file format")

def compile_c3_contacts():
    print("Compiling database files")
    # c3_data_path = './data/c3_files'

    # # Compile contact addresses
    # for subdir, _, files in os.walk(os.path.join(c3_data_path, 'contact_addresses')):
    #     source_address_df = pd.concat([pd.read_csv(os.path.join(subdir, file), low_memory=False) for file in files], ignore_index=True)

    # # Compile email addresses
    # for subdir, _, files in os.walk(os.path.join(c3_data_path, 'contact_email_addresses')):
    #     email_address_df = pd.concat([pd.read_csv(os.path.join(subdir, file), low_memory=False) for file in files], ignore_index=True)

    # # Compile phone numbers
    # for subdir, _, files in os.walk(os.path.join(c3_data_path, 'contact_phone_numbers')):
    #     phone_number_df = pd.concat([pd.read_csv(os.path.join(subdir, file), low_memory=False) for file in files], ignore_index=True)

    # # Compile skip traced addresses
    # for subdir, _, files in os.walk(os.path.join(c3_data_path, 'contact_skip_traced_addresses')):
    #     skip_traced_df = pd.concat([pd.read_csv(os.path.join(subdir, file), low_memory=False) for file in files], ignore_index=True)

    # # Compile skip traced addresses
    # for subdir, _, files in os.walk(os.path.join(c3_data_path, 'contacts')):
    #     contacts_df = pd.concat([pd.read_csv(os.path.join(subdir, file), low_memory=False) for file in files], ignore_index=True)
    # skip_traced_df['skip_traced_address'] = skip_traced_df[['address', 'city', 'state']].fillna('').agg(' '.join, axis=1)

    CM_HOST = os.getenv('DB_HOST')
    CM_USER = os.getenv('DB_USER')
    CM_PASSWORD = os.getenv('DB_PASSWORD')
    CM_DB = os.getenv('DB_NAME')

    skip_traced_query = """
    SELECT
        contact_id,
        CONCAT_WS(' ', address, city, state) AS skip_traced_address,
        deleted_at
    FROM
        contact_skip_traced_addresses;
    """

    source_address_query = """
    SELECT
        contact_id,
        CONCAT_WS(' ', source_address, source_city, source_state) AS source_address,
        deleted_at
    FROM
        contact_addresses;
    """

    email_query = """
    SELECT
        contact_id,
        email_address,
        deleted_at
    FROM
        contact_email_addresses;
    """

    phone_query = """
    SELECT
        contact_id,
        phone_number,
        deleted_at
    FROM
        contact_phone_numbers;
    """

    contact_query = """
    SELECT
        id AS contact_id,
        UPPER(CONCAT_WS(' ', first_name, middle_name, last_name)) AS full_name,
        deleted_at
    FROM
        contacts;
    """

    engine = create_engine(f"mysql+pymysql://{CM_USER}:{quote(CM_PASSWORD)}@{CM_HOST}/{CM_DB}")
    skip_traced_df = pd.read_sql_query(skip_traced_query, con=engine)
    source_address_df = pd.read_sql_query(source_address_query, con=engine)
    email_address_df = pd.read_sql_query(email_query, con=engine)
    phone_number_df = pd.read_sql_query(phone_query, con=engine)
    contacts_df = pd.read_sql_query(contact_query, con=engine)

    # Skip traced cleanups
    skip_traced_df.dropna(subset=['skip_traced_address'], inplace=True)
    skip_traced_df['skip_traced_address'] = skip_traced_df['skip_traced_address'].str.upper().str.strip()
    skip_traced_df['skip_traced_address'] = skip_traced_df['skip_traced_address'].str.replace(',', '')
    skip_traced_df['skip_traced_address'] = skip_traced_df['skip_traced_address'].str.replace(r'\s+', ' ', regex=True).str.strip()
    skip_traced_df = skip_traced_df[['contact_id', 'skip_traced_address', 'deleted_at']]

    # Source address cleanups
    # source_address_df['source_address'] = source_address_df[['source_address', 'source_city', 'source_state']].fillna('').agg(' '.join, axis=1)
    source_address_df.dropna(subset=['source_address'], inplace=True)
    source_address_df['source_address'] = source_address_df['source_address'].str.upper().str.strip()
    source_address_df['source_address'] = source_address_df['source_address'].str.replace(',', '')
    source_address_df['source_address'] = source_address_df['source_address'].str.replace(r'\s+', ' ', regex=True).str.strip()
    source_address_df = source_address_df[['contact_id', 'source_address', 'deleted_at']]

    # Emaill address cleanups
    email_address_df.dropna(subset=['email_address'], inplace=True)
    email_address_df['email_address'] = email_address_df['email_address'].str.upper().str.strip()
    email_address_df['email_address'] = email_address_df['email_address'].str.replace(',', '')
    email_address_df['email_address'] = email_address_df['email_address'].str.replace(r'\s+', ' ', regex=True).str.strip()
    email_address_df.rename(columns={'email_deleted_at': 'deleted_at'}, inplace=True)

    # Phone number cleanups
    phone_number_df.dropna(subset=['phone_number'], inplace=True)
    phone_number_df.drop_duplicates(subset=['contact_id', 'phone_number'], inplace=True)
    phone_number_df['phone_number'] = phone_number_df['phone_number'].str.upper().str.strip()
    phone_number_df['phone_number'] = phone_number_df['phone_number'].str.replace(',', '')
    phone_number_df['phone_number'] = phone_number_df['phone_number'].str.replace(r'\s+', ' ', regex=True).str.strip()
    phone_number_df.rename(columns={'phone_deleted_at': 'deleted_at'}, inplace=True)

    # Contact names cleanup
    contacts_df.dropna(subset=['full_name'], inplace=True)
    contacts_df['full_name'] = contacts_df['full_name'].str.upper().str.strip()
    contacts_df['full_name'] = contacts_df['full_name'].str.replace(',', '')
    contacts_df['full_name'] = contacts_df['full_name'].str.replace(r'\s+', ' ', regex=True).str.strip()

    skip_traced_df.to_csv('./data/c3_files/contact_skip_traced_addresses/skip_traced.csv', index=False)
    source_address_df.to_csv('./data/c3_files/contact_addresses/source_addresses.csv', index=False)
    email_address_df.to_csv('./data/c3_files/contact_email_addresses/emails.csv', index=False)
    phone_number_df.to_csv('./data/c3_files/contact_phone_numbers/phones.csv', index=False)
    contacts_df.to_csv('./data/c3_files/contacts/contact_names.csv', index=False)

    return skip_traced_df, source_address_df, email_address_df, phone_number_df, contacts_df

def find_phone_number_match(input_df: pd.DataFrame, phone_number_df: pd.DataFrame, contacts_df: pd.DataFrame):
    print("Processing phone numbers")
    input_df['row_number'] = input_df.index
    merged_contacts_df = phone_number_df.merge(contacts_df[['contact_id', 'deleted_at']].rename(columns={'deleted_at': 'contact_deleted_at'}),
                                                on='contact_id',
                                                how='left')
    filtered_email_df = merged_contacts_df[(merged_contacts_df['phone_number'].isin(input_df['Contact Information']))]
    input_df = input_df.merge(filtered_email_df,
                              left_on='Contact Information',
                              right_on='phone_number',
                              how='left')
    input_df.loc[input_df['contact_id'].notna(), 'Contact ID'] = input_df['contact_id']
    input_df['Contact ID'] = input_df['Contact ID'].astype('Int64')
    input_df.drop(columns=['phone_number', 'contact_id', 'contact_deleted_at'], inplace=True)
    return input_df

def find_email_address_match(input_df: pd.DataFrame, email_address_df: pd.DataFrame, contacts_df: pd.DataFrame):
    print("Processing email addresses")
    input_df['row_number'] = input_df.index
    merged_contacts_df = email_address_df.merge(contacts_df[['contact_id', 'deleted_at']].rename(columns={'deleted_at': 'contact_deleted_at'}),
                                                on='contact_id',
                                                how='left')
    filtered_email_df = merged_contacts_df[(merged_contacts_df['email_address'].isin(input_df['Contact Information']))]
    input_df = input_df.merge(filtered_email_df,
                              left_on='Contact Information',
                              right_on='email_address',
                              how='left')
    input_df.loc[input_df['contact_id'].notna(), 'Contact ID'] = input_df['contact_id']
    input_df['Contact ID'] = input_df['Contact ID'].astype('Int64')
    input_df.drop(columns=['email_address', 'contact_id', 'contact_deleted_at'], inplace=True)
    return input_df

def check_address_to_name(df: pd.DataFrame, contact_df: pd.DataFrame):
    mo_name_merged_df = df.merge(contact_df,
                                 left_on='Contact ID',
                                 right_on='contact_id',
                                 how='left')
    
    matching_mo_name_mask = mo_name_merged_df['MO NAME'].str.upper().str.strip() == mo_name_merged_df['full_name'].str.upper().str.strip()
    mo_name_merged_df.loc[matching_mo_name_mask, 'Notes'] += ', Matched MO Name'

    not_matching_mo_name_mask = ((mo_name_merged_df['MO NAME'].str.upper().str.strip() != mo_name_merged_df['full_name'].str.upper().str.strip()) & (mo_name_merged_df['Notes'] == 'Contact Close Address Match'))
    mo_name_merged_df.loc[not_matching_mo_name_mask, 'Notes'] += ', Not Matching MO Name'
    mo_name_merged_df.loc[not_matching_mo_name_mask, 'Contact ID'] = pd.NA
    
    mo_name_merged_df.drop(columns=['contact_id', 'full_name'], axis=1, inplace=True)

    return mo_name_merged_df

def mailing_address_note(row: pd.Series):
    best_score = row.get('Best Score', None)
    if best_score == 100.0:
        return 'Contact Exact Address Match'
    elif 100.0 > best_score >= 90.0:
        return 'Contact Close Address Match'
    else:
        return 'No Address Match Found'

def find_skip_trace_match(input_df: pd.DataFrame, skip_traced_df: pd.DataFrame):
    print("Processing direct mails")
    # Convert addresses to lists for efficient lookup
    direct_mail_df = input_df[input_df["Opt-out Medium"] == "Direct Mail"]
    input_addresses = direct_mail_df['address_info'].tolist()
    skip_addresses = skip_traced_df['skip_traced_address'].tolist()

    # Efficient bulk fuzzy matching
    matches = process.cdist(input_addresses, skip_addresses, scorer=fuzz.ratio, score_cutoff=90)
    best_match_dict = {}
    best_score_dict = {}
    best_address_match_dict = {}

    for input_idx, match_list in enumerate(matches):
        best_match_idx = np.argmax(match_list)
        best_score = match_list[best_match_idx]
        if best_score >= 90.0:
            best_address_match_dict[input_addresses[input_idx]] = skip_traced_df.iloc[best_match_idx]['skip_traced_address']
            best_match_dict[input_addresses[input_idx]] = skip_traced_df.iloc[best_match_idx]['contact_id']
            best_score_dict[input_addresses[input_idx]] = best_score

    # Map matched contact_ids to input_df
    input_df['Skip Traced Address'] = input_df['address_info'].map(best_address_match_dict)
    input_df['Contact ID'] = input_df['address_info'].map(best_match_dict)
    input_df['Best Score'] = input_df['address_info'].map(best_score_dict)
    
    return input_df

def find_source_address_match(input_df: pd.DataFrame, source_address_df: pd.DataFrame):
    # Convert addresses to lists for efficient lookup
    input_addresses = input_df['address_info'].tolist()
    skip_addresses = source_address_df['source_address'].tolist()

    # Efficient bulk fuzzy matching
    matches = process.cdist(input_addresses, skip_addresses, scorer=fuzz.ratio, score_cutoff=90)
    best_match_dict = {}
    best_score_dict = {}
    best_address_match_dict = {}

    for input_idx, match_list in enumerate(matches):
        best_match_idx = np.argmax(match_list)
        best_score = match_list[best_match_idx]
        if best_score >= 90.0:
            best_address_match_dict[input_addresses[input_idx]] = source_address_df.iloc[best_match_idx]['source_address']
            best_match_dict[input_addresses[input_idx]] = source_address_df.iloc[best_match_idx]['contact_id']
            best_score_dict[input_addresses[input_idx]] = best_score

    # Apply mappings only where 'Contact ID' is NaN
    mask = input_df['Contact ID'].isna()

    # Map matched contact_ids to input_df
    input_df.loc[mask, 'Skip Traced Address'] = input_df.loc[mask, 'address_info'].map(best_address_match_dict)
    input_df.loc[mask, 'Contact ID'] = input_df.loc[mask, 'address_info'].map(best_match_dict)
    input_df.loc[mask, 'Best Score'] = input_df.loc[mask, 'address_info'].map(best_score_dict)
    input_df['Contact ID'] = input_df['Contact ID'].astype('Int64')
    input_df['Notes'] = input_df.apply(mailing_address_note, axis=1)

    # Drop unnecessary columns
    input_df.drop(columns=['Skip Traced Address', 'Best Score'], axis=1, inplace=True)

    return input_df

def check_name_to_address(df: pd.DataFrame, skip_traced_address_df: pd.DataFrame, source_address_df: pd.DataFrame, contact_df: pd.DataFrame):
    # Merge Full Names from database to Skip Traced Address and Source Address Dataframes
    source_address_df.rename(columns={'source_address': 'skip_traced_address'}, inplace=True)
    address_df = pd.concat([skip_traced_address_df, source_address_df], ignore_index=True)
    database_df = contact_df.merge(address_df,
                                   on='contact_id',
                                   how='left')

    # Merge to input dataframe
    merged_df = df.merge(database_df,
                         left_on=['MO NAME', 'address_info'],
                         right_on=['full_name', 'skip_traced_address'],
                         how='left')
    
    mask = (merged_df['Contact ID'].isna()) & (merged_df['contact_id'].notna())
    merged_df.loc[mask, 'Contact ID'] = merged_df['contact_id']
    merged_df.loc[mask, 'Notes'] += ', Passed Criteria 2'
    merged_df.drop(columns=['contact_id', 'full_name', 'skip_traced_address', 'address_info', 'deleted_at_x', 'deleted_at_y'], axis=1, inplace=True)
    
    return merged_df

def filter_input_file(input_df: pd.DataFrame):
    direct_mail_df = input_df.loc[input_df['Opt-out Medium'] == 'Direct Mail'].copy()
    phone_df = input_df.loc[input_df['Opt-out Medium'] == 'Phone'].copy()
    email_df = input_df.loc[input_df['Opt-out Medium'] == 'Email'].copy()

    if not direct_mail_df.empty:
        direct_mail_df['address_info'] = direct_mail_df['Contact Information']
        direct_mail_df['address_info'] = direct_mail_df['address_info'].str.replace(',', '').str.upper().str.strip() # Remove comma
        direct_mail_df['address_info'] = direct_mail_df['address_info'].str.replace(r'\s+', ' ', regex=True).str.strip() # Remove double spacing
        direct_mail_df['address_info'] = direct_mail_df['address_info'].str.replace(r'\s*-\s*', '-', regex=True) # Remove space before and after hyphen
        direct_mail_df['address_info'] = direct_mail_df['address_info'].str.split(' ').str[:-1].str.join(' ').str.strip() # Remove postal code from contact information
        direct_mail_df['MO NAME'] = direct_mail_df['MO NAME'].str.replace('.', '').str.replace(',', '').str.strip().str.upper()
        direct_mail_df['row_number'] = direct_mail_df.index

    if not phone_df.empty:
        phone_df['Contact Information'] = phone_df['Contact Information'].astype(str)
        phone_df['Contact Information'] = phone_df['Contact Information'].str.replace(',', '').str.upper().str.strip() # Remove comma
        phone_df['Contact Information'] = phone_df['Contact Information'].str.replace(' ', '') # Remove space

    if not email_df.empty:
        email_df['Contact Information'] = email_df['Contact Information'].str.replace(',', '').str.upper().str.strip() # Remove comma
        email_df['Contact Information'] = email_df['Contact Information'].str.replace(' ', '') # Remove space
    
    return direct_mail_df, email_df, phone_df

def add_pipedrive_columns(input_df: pd.DataFrame, pipedrive_exploded_df: pd.DataFrame):
    pipedrive_columns = [
        'Deal - ID',
        'Activity - Subject',
        'Activity - Add time',
        'Activity - Deal',
        'Activity - Contact person',
        'Deal - Deal Status',
        'Deal - Unique Database ID',
        'Deal - Marketing Medium',
        'Person - Mailing Address'
    ]
    agg_columns = [
        'Contact ID',
        'Deal ID',
        'Activity',
        'PD Removal Activity Date',
        'Contact Person',
        'Deal Status',
        'Marketing Medium',
        'Notes'
    ]
    output_columns = [
        'Contact ID',
        'Deal ID',
        'Contact Person',
        'PD Removal Activity Date',
        'Source of Opt-out Request',
        'Opt-out Medium',
        'Contact Information',
        'Opt-out Entry Date',
        'Contact Info Removal from Database Date',
        'Source',
        'Marketing Medium',
        'Deal Status',
        'Activity',
        'Category',
        'Notes'
    ]
    groupby_column = 'row_number'

    merged_df = input_df.merge(pipedrive_exploded_df,
                               left_on='Contact ID',
                               right_on='Deal - Unique Database ID',
                               how='left')

    merged_df['Contact Info Removal from Database Date'] = merged_df['deleted_at']
    merged_df['Deal ID'] = merged_df['Deal - ID']
    merged_df['Contact Person'] = merged_df['Activity - Contact person']
    merged_df['PD Removal Activity Date'] = merged_df['Activity - Add time']
    merged_df['Deal Status'] = merged_df['Deal - Deal Status']
    merged_df['Activity'] = merged_df['Activity - Subject']
    merged_df['Marketing Medium'] = merged_df['Deal - Marketing Medium']

    pipedrive_columns.append('deleted_at')
    merged_df.drop(columns=pipedrive_columns, axis=1, inplace=True)

    columns_to_retain = [col for col in merged_df.columns if col not in agg_columns and col != groupby_column]
    aggregated_df = merged_df[merged_df['Deal ID'].notna()].groupby(groupby_column).agg(
        {col: lambda x: ' | '.join(map(str, sorted(set(x[pd.notna(x)])))) if x[pd.notna(x)].any() else np.nan for col in agg_columns}
    ).reset_index()

    contact_id_col = merged_df.groupby(groupby_column, sort=False, observed=True)['Contact ID'] \
        .agg(lambda x: ' | '.join(map(str, sorted(set(x.dropna())))) if x.notna().any() else pd.NA) \
        .reset_index()

    retained_df = merged_df[columns_to_retain + [groupby_column]].drop_duplicates(groupby_column)
    with_pipedrive_df = retained_df.merge(aggregated_df, on=groupby_column, how='left').drop(columns=['Contact ID'], axis=1)
    final_df = with_pipedrive_df.merge(contact_id_col, on=groupby_column, how='left')[output_columns]
    final_df.drop_duplicates(inplace=True)
    final_df.rename(columns={
        'Contact ID': 'UNIQUE_DB_ID',
        'Deal ID': 'DEAL_ID',
        'Contact Person': 'CONTACT_PERSON',
        'PD Removal Activity Date': 'PD_REMOVAL_ACTIVITY_DATE',
        'Source of Opt-out Request': 'SOURCE_OF_OPT-OUT_REQUEST',
        'Opt-out Medium': 'OPT-OUT_MEDIUM',
        'Contact Information': 'OPT-OUT_CONTACT',
        'Opt-out Entry Date': 'OPT-OUT_ENTRY_DATE',
        'Contact Info Removal from Database Date': 'CONTACT_INFO_REMOVED_FROM_DB_DATE',
        'Source': 'SOURCE',
        'Marketing Medium': 'MARKETING_MEDIUM',
        'Deal Status': 'DEAL_STATUS',
        'Activity': 'ACTIVITY'}, inplace=True)
    return final_df

def clean_ids(id_str):
    return " | ".join([x.strip() for x in id_str.split("|") if x.strip()])

def extract_pipedrive_data(path: str):
    print("Reading pipedrive data")
    pipedrive_df = read_file(path)
    pipedrive_columns = [
        'Deal - ID',
        'Activity - Subject',
        'Activity - Add time',
        'Activity - Deal',
        'Activity - Contact person',
        'Deal - Deal Status',
        'Deal - Unique Database ID',
        'Deal - Marketing Medium',
        'Person - Mailing Address'
    ]

    pipedrive_df.loc[pipedrive_df['Deal - Unique Database ID'].notna(), 'Deal - Unique Database ID'] = \
    pipedrive_df.loc[pipedrive_df['Deal - Unique Database ID'].notna(), 'Deal - Unique Database ID'].apply(clean_ids)
    pipedrive_df['Deal - Unique Database ID'] = pipedrive_df['Deal - Unique Database ID'].str.split(' | ', regex=False)
    pipedrive_exploded_df = pipedrive_df.explode('Deal - Unique Database ID') \
        .drop_duplicates(subset=['Deal - Unique Database ID']) \
        .dropna(subset=['Deal - Unique Database ID']) \
        [pipedrive_columns]

    pipedrive_exploded_df['Deal - Unique Database ID'] = pipedrive_exploded_df['Deal - Unique Database ID'].astype('Int64')
    pipedrive_exploded_df['Deal - ID'] = pipedrive_exploded_df['Deal - ID'].astype('Int64')
    return pipedrive_exploded_df

def format_file_and_export(df: pd.DataFrame, file_path: str, save_path: str):
    print("Exporting output file")
    filename = os.path.basename(file_path)
    if filename.endswith('.csv'):
        df.to_csv(f"{save_path}/(C3 Output) {filename}", index=False)
    elif filename.endswith('.xlsx'):
        df.to_excel(f"{save_path}/(C3 Output) {filename}", index=False)
    else:
        raise RuntimeError("No output generated. Invalid file format")

def main(pipedrive_path: str, file_paths: tuple, save_path: str):

    try:
        pipedrive_exploded_df = extract_pipedrive_data(pipedrive_path)
        skip_traced_df, source_address_df, email_address_df, phone_number_df, contacts_df = compile_c3_contacts()
        for file in file_paths:
            df_list = []
            input_df = read_file(file)
            direct_mail_df, email_df, phone_df = filter_input_file(input_df)

            # Direct mail processing
            if not direct_mail_df.empty:
                skip_traced_matched_df = find_skip_trace_match(direct_mail_df, skip_traced_df)
                direct_mail_matched_df = find_source_address_match(skip_traced_matched_df, source_address_df)
                mo_names_df = check_address_to_name(direct_mail_matched_df, contacts_df)
                mo_names_criteria_2_df = check_name_to_address(mo_names_df, skip_traced_df, source_address_df, contacts_df)
                df_list.append(mo_names_criteria_2_df)

            # Email address processing
            if not email_df.empty:
                email_address_matched_df = find_email_address_match(email_df, email_address_df, contacts_df)
                df_list.append(email_address_matched_df)

            # Phone number processing
            if not phone_df.empty:
                phone_matched_df = find_phone_number_match(phone_df, phone_number_df, contacts_df)
                df_list.append(phone_matched_df)

            print("Adding pipedrive data")

            # Add pipedrive details
            final_df_list = []
            for df in df_list:
                with_pipedrive_df = add_pipedrive_columns(df, pipedrive_exploded_df)
                final_df_list.append(with_pipedrive_df)

            # Concat and export
            final_df = pd.concat(final_df_list, ignore_index=True)
            format_file_and_export(final_df, file, save_path)

    except Exception as e:
        print(f"An error occurred: {e}")
        raise RuntimeError

if __name__ == "__main__":
    main()
