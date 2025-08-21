import os
import pandas as pd
from datetime import datetime, timedelta

def read_file(path: str):

    if path.endswith('.csv'):
        return pd.read_csv(path, low_memory=False)

    elif path.endswith('.xlsx'):
        return pd.read_excel(path)
    
    else:
        raise ValueError("Invalid file format: Please provide a .csv or .xlsx file.")
    
def format_deal_title(row: pd.Series):
    first_name = str(row['first_name']).title() if not pd.isna(row['first_name']) else ''
    last_name = str(row['last_name']).title() if not pd.isna(row['last_name']) else ''
    full_name = str(row['full_name']).title() if not pd.isna(row['full_name']) else ''
    target_county = str(row['target_county']).title() if not pd.isna(row['target_county']) else ''
    
    if pd.isna(row['Deal - Title']):
        if last_name:
            return f"{first_name} {last_name} {target_county} County, {row['target_state']}"
        else:
            return f"{full_name} {target_county} County, {row['target_state']}"
    else:
        return row['Deal - Title']
    
def format_mailing_address(row: pd.Series):
    md_address = str(row['md_address1']).upper() if not pd.isna(row['md_address1']) else ''
    md_city = str(row['md_city']).upper() if not pd.isna(row['md_city']) else ''
    md_state = str(row['md_state']).upper() if not pd.isna(row['md_state']) else ''
    if md_address:
        return f"{md_address}, {md_city}, {md_state}"
    
def apply_mask(df: pd.DataFrame, mask, output_value) -> None:
    df.loc[mask, 'reason_for_removal'] = df.loc[mask, 'reason_for_removal'].apply(
        lambda lst: lst + [output_value] if isinstance(lst, list) else [output_value])

def check_date(df: pd.DataFrame, col: str) -> pd.DataFrame:
    current_date = datetime.now().date()
    sixty_date_ago = current_date - timedelta(days=60)
    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    mask = (df[col] >= sixty_date_ago) & (df[col] <= current_date)
    return mask

def apply_database_id_mask(df: pd.DataFrame, pipedrive_df: pd.DataFrame):
    # Explode 'Deal - Unique Database ID' into individual rows
    exploded_pipedrive_df = pipedrive_df.assign(
        Deal_Ids=pipedrive_df['Deal - Unique Database ID'].str.split(' | ')
    ).explode('Deal_Ids')

    # Generate a set of unique IDs from exploded values for faster lookup
    deal_ids_set = set(exploded_pipedrive_df['Deal_Ids'].astype(str))

    # Filter rows where contact_id exists in the set
    contact_id_mask = df['contact_id'].astype(str).isin(deal_ids_set)

    # Apply mask
    apply_mask(df, contact_id_mask, 'Matched Unique Database ID')

def apply_filters(df: pd.DataFrame, pipedrive_df: pd.DataFrame):

    apply_database_id_mask(df, pipedrive_df)
    contact_type_mask = df['contact_type'].str.lower() == 'company'
    apply_mask(df, contact_type_mask, 'Company type is Company')

    in_pipedrive_mask = df['in_pipedrive'].str.lower() == 'y'
    apply_mask(df, in_pipedrive_mask, 'in_pipedrive is Y')

    # deal_id
    deal_id_mask = df['deal_id'].notna()
    apply_mask(df, deal_id_mask, 'deal_id not empty')

    # deal_status
    deal_status_mask = df['deal_status'].notna()
    apply_mask(df, deal_status_mask, 'deal_status not empty')

    # person_id
    person_id_mask = df['person_id'].notna()
    apply_mask(df, person_id_mask, 'person_id not empty')

    # category
    category_mask = df['category'].notna()
    apply_mask(df, category_mask, 'category not empty')

    # Mail Marketing Undel Flag
    undel_mask = df['Mail Marketing Undel Flag'].notna()
    apply_mask(df, undel_mask, 'Mail Marketing Undel Flag not empty')

    # Mail Marketing Bad Data Flag
    bad_data_mask = df['Mail Marketing Bad Data Flag'].notna()
    apply_mask(df, bad_data_mask, 'Mail Marketing Bad Data Flag not empty')

    # Deal - ID
    deal_id_2_mask = df['Deal - ID'].notna()
    apply_mask(df, deal_id_2_mask, 'Deal - ID not empty')

    # Deal - Title
    deal_title_mask = df['Deal - Title'].notna()
    apply_mask(df, deal_title_mask, 'Deal - Title not empty')

    # Deal - Value
    deal_value_mask = df['Deal - Value'].notna()
    apply_mask(df, deal_value_mask, 'Deal - Value not empty')

    # Deal - County
    deal_county_mask = df['Deal - County'].notna()
    apply_mask(df, deal_county_mask, 'Deal - County not empty')

    # Deal - Created
    deal_created_mask = df['Deal - Created'].notna()
    apply_mask(df, deal_created_mask, 'Deal - Created not empty')

    # Last Marketing Date
    last_marketing_date_mask = check_date(df, 'Last Marketing Date')
    apply_mask(df, last_marketing_date_mask, 'Last marketing date is within 60 days from run date')

    # Deal Title
    df['new_deal_title'] = df.apply(lambda x: format_deal_title(x), axis=1)
    match_title_mask = df['new_deal_title'].str.upper().isin(pipedrive_df['Deal - Title'].str.upper())
    apply_mask(df, match_title_mask, 'Found matching Deal Title from Pipedrive file')

    # Mailing Address
    pipedrive_df['Person - Mailing Address'] = pipedrive_df['Person - Mailing Address'].str.replace(r', USA(, \d{5})?$', '', regex=True)
    df['mailing_address'] = df.apply(lambda x: format_mailing_address(x), axis=1)
    mailing_address_mask = df['mailing_address'].str.upper().isin(pipedrive_df['Person - Mailing Address'].str.upper())
    apply_mask(df, mailing_address_mask, 'Found matching Mailing Address from Pipedrive file')

    # Drop duplicates and columns
    df.drop_duplicates(subset=['contact_id'], inplace=True)
    df.drop_duplicates(subset=['first_name', 'last_name', 'md_address1', 'md_city', 'md_state'], inplace=True)
    df.drop(columns=['mailing_address', 'new_deal_title'], axis=1, inplace=True)

    # Join all reasons with comma separator
    df['reason_for_removal'] = df['reason_for_removal'].apply(lambda lst: ', '.join(lst) if isinstance(lst, list) else lst)

    # Capitalization of all names
    columns_to_transform = ['full_name', 'first_name', 'middle_name', 'last_name']
    df[columns_to_transform] = df[columns_to_transform].applymap(lambda x: x.title() if isinstance(x, str) else x)

    return df

def export_output(df: pd.DataFrame, file_path: str, save_path: str) -> None:

    filename = os.path.basename(file_path)

    if filename.endswith('.csv'):
        df.to_csv(f"{save_path}/(With Cleanup Tagging) {filename}", index=False)
    
    elif filename.endswith('.xlsx'):
        df.to_excel(f"{save_path}/(With Cleanup Tagging) {filename}", index=False)
    
    else:
        raise RuntimeError("No output generated. Invalid file format")


def main(files: tuple, pipedrive_file: str, save_path: str):

    try:
        print("Reading Pipedrive Export file")
        pipedrive_df = read_file(pipedrive_file)

        for file in files:

            print(f"Processing file {file}")
            df = read_file(file)
            df['reason_for_removal'] = pd.NA
            final_df = apply_filters(df, pipedrive_df)
            export_output(final_df, file, save_path)
        
        print("Successfully processed all files")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise RuntimeError

if __name__ == "__main__":
    main()
