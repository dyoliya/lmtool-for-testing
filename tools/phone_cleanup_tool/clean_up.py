import re
import os
import dropbox
import pandas as pd
from datetime import datetime, timedelta

def download_list_cleaner(auth_code: str) -> None:
    global dnc_df, mvp_df, db_id_df, time_df, conv_df

    print("Downloading list cleaner files")

    sheet_names = [
        "CCM+CH+MVPC+MVPT+JC+RC+PD (Cold)",
        "DNC (Cold-PD)",
        "UniqueDB ID (Cold)",
        "CallOut-14d+TextOut-30d (Cold)",
        "CallTextOut-7d (PD)",
        "PDConvDup (PD)",
        "PDJRAADups (PD)"
    ]

    for sheet_name in sheet_names:
        dropbox_path = f"/List Cleaner & JC DNC/{sheet_name}.csv"
        local_file_path = f"./data/{sheet_name}.csv"
        dbx = dropbox.Dropbox(auth_code)
        metadata, response = dbx.files_download(dropbox_path)

        with open(local_file_path, 'wb') as f:
            f.write(response.content)

def is_valid_phone(phone):
    return bool(re.fullmatch(r'\d{10,15}', phone))

def read_file(path: str):

    if path.endswith('.csv'):
        return pd.read_csv(path, low_memory=False)

    elif path.endswith('.xlsx'):
        return pd.read_excel(path)
    
    else:
        raise ValueError("Invalid file format: Please provide a .csv or .xlsx file.")

    
def apply_mask(df: pd.DataFrame, mask, output_value) -> None:
    df.loc[mask, 'reason_for_removal'] = df.loc[mask, 'reason_for_removal'].apply(
        lambda lst: lst + [output_value] if isinstance(lst, list) else [output_value])


def check_date(df: pd.DataFrame, col: str) -> pd.DataFrame:
    current_date = datetime.now().date()
    seven_days_ago = current_date - timedelta(days=7)
    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    mask = (df[col] >= seven_days_ago) & (df[col] <= current_date)

    return mask


def check_date_30_days(df: pd.DataFrame, col: str) -> pd.DataFrame:
    current_date = datetime.now().date()
    thirty_days_ago = current_date - timedelta(days=30)
    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    mask = (df[col] >= thirty_days_ago) & (df[col] <= current_date)

    return mask


def apply_all_filters(df: pd.DataFrame, run_mode: str) -> pd.DataFrame:
    
    df['reason_for_removal'] = [[] for _ in range(len(df))]
    
    if 'Rolling 30 Days Rvm Count' in df.columns:
        df['Rolling 30 Days Rvm Count'] = pd.to_numeric(df['Rolling 30 Days Rvm Count'], errors='coerce')
    
    if 'Rolling 30 Days Text Marketing Count' in df.columns:
        df['Rolling 30 Days Text Marketing Count'] = pd.to_numeric(df['Rolling 30 Days Text Marketing Count'], errors='coerce')
    
    if 'Rolling 30 Days Max Outbound Count' in df.columns:
        df['Rolling 30 Days Max Outbound Count'] = pd.to_numeric(df['Rolling 30 Days Max Outbound Count'], errors='coerce')

    if 'in_pipedrive' in df.columns:
        in_pipedrive_mask = df['in_pipedrive'].str.upper() == 'Y'
        apply_mask(df, in_pipedrive_mask, 'in_pipedrive is Y')

    if 'rc_pd' in df.columns:
        rc_pd_mask = df['rc_pd'].str.upper() == 'YES'
        apply_mask(df, rc_pd_mask, 'rc_pd is Yes')

    if run_mode == 'text_marketing':
        if 'type' and 'carrier_type' in df.columns:
            type_ctype_mask = (df['type'].str.upper() == 'LANDLINE') & (df['carrier_type'].str.upper() == 'LANDLINE')
            apply_mask(df, type_ctype_mask, 'Both type & carrier_type are Landline')

    if 'text_opt_in' in df.columns:
        text_opt_in_mask = df['text_opt_in'].str.upper() == 'NO'
        apply_mask(df, text_opt_in_mask, 'text_opt_in is No')

    if 'contact_deal_id' in df.columns:
        contact_deal_id_mask = df['contact_deal_id'].notna()
        apply_mask(df, contact_deal_id_mask, 'contact_deal_id Not Empty')

    if 'contact_deal_status' in df.columns:
        contact_deal_status_mask = df['contact_deal_status'].notna()
        apply_mask(df, contact_deal_status_mask, 'contact_deal_status Not Empty')

    if 'contact_person_id' in df.columns:
        contact_person_id_mask = df['contact_person_id'].notna()
        apply_mask(df, contact_person_id_mask, 'contact_person_id Not Empty')

    if 'phone_number_deal_id' in df.columns:
        phone_number_deal_id_mask = df['phone_number_deal_id'].notna()
        apply_mask(df, phone_number_deal_id_mask, 'phone_number_deal_id Not Empty')

    if 'phone_number_deal_status' in df.columns:
        phone_number_deal_status_mask = df['phone_number_deal_status'].notna()
        apply_mask(df, phone_number_deal_status_mask, 'phone_number_deal_status Not Empty')

    if 'RVM - Last RVM Date' in df.columns:
        last_rvm_mask = check_date(df, 'RVM - Last RVM Date')
        apply_mask(df, last_rvm_mask, 'RVM - Last RVM Date - last 7 days from tool run date')

    if run_mode == 'text_marketing':
        if 'Latest Text Marketing Date (Sent)' in df.columns:
            last_marketing_text_mask = check_date(df, 'Latest Text Marketing Date (Sent)')
            apply_mask(df, last_marketing_text_mask, 'Latest Text Marketing Date (Sent) - last 7 days from tool run date')

    if 'Rolling 30 Days Max Outbound Count' and 'Rolling 30 Days Text Marketing Count' in df.columns:
        rolling_days_mask = (df['Rolling 30 Days Max Outbound Count'] + df['Rolling 30 Days Text Marketing Count']) >= 3
        apply_mask(df, rolling_days_mask, 'Rolling 30 Days Max Outbound Count and Rolling 30 Days Text Marketing Count - total >= 3')

    if 'Deal - ID' in df.columns:
        deal_id_mask = df['Deal - ID'].notna()
        apply_mask(df, deal_id_mask, 'Deal - ID Not Empty')

    if 'Deal - Text Opt-in' in df.columns:
        deal_text_opt_in = df['Deal - Text Opt-in'].str.upper().str.contains('NO', na=False)
        apply_mask(df, deal_text_opt_in, 'Deal - Text Opt-in is No')

    if run_mode == 'call_marketing':
        # Updated this old mask from 7 days to 30 days
        if 'Latest Text Marketing Date (Sent)' in df.columns:
            last_marketing_text_mask = check_date_30_days(df, 'Latest Text Marketing Date (Sent)')
            apply_mask(df, last_marketing_text_mask, 'Latest Text Marketing Date (Sent) - last 30 days from tool run date')

        # All below masks are new conditions
        if 'Latest Text Marketing Date (Received)' in df.columns:
            last_marketing_text_mask = check_date_30_days(df, 'Latest Text Marketing Date (Received)')
            apply_mask(df, last_marketing_text_mask, 'Latest Text Marketing Date (Received) - last 30 days from tool run date')

        if 'RVM - Last Reason for Failure' in df.columns:
            rvm_last_reason_mask = df['RVM - Last Reason for Failure'].isin(["Not Covered", "Removed", "Do not Dial List removed"])
            apply_mask(df, rvm_last_reason_mask, 'RVM - Last Reason for Failure is either Not Covered, Removed, Do not Dial List removed')
    
    """End of new conditions"""
    
    # Deduplication
    df['reason_length'] = df['reason_for_removal'].apply(len)
    df_longest_reason = df.loc[df.groupby('phone_number', sort=False)['reason_length'].idxmax()]
    df_longest_reason = df_longest_reason.drop(columns=['reason_length'])

    # Capitalization of names
    columns_to_transform = ['full_name', 'first_name', 'last_name']
    df_longest_reason[columns_to_transform] = df_longest_reason[columns_to_transform].applymap(lambda x: x.title() if isinstance(x, str) else x)

    return df_longest_reason

def get_phone_set(run_mode: str) -> set:

    data_path = './data'
    file_list = [
        "CCM+CH+MVPC+MVPT+JC+RC+PD (Cold).csv",
        "DNC (Cold-PD).csv",
        "CallOut-14d+TextOut-30d (Cold).csv",
        "CallTextOut-7d (PD).csv",
        "PDConvDup (PD).csv",
        "PDJRAADups (PD).csv"
    ]
    if run_mode == 'recleaning':
        file_list.remove('CallOut-14d+TextOut-30d.csv')
        
    final_list_cleaner_df = pd.concat([pd.read_csv(os.path.join(data_path, file), low_memory=False, header=None) for file in file_list], ignore_index=True)

    # Clean up the list and filter for valid phone numbers
    valid_phone_set = set(int(phone) for phone in map(str, final_list_cleaner_df[0].tolist()) if is_valid_phone(phone))
    return valid_phone_set

def get_id_set() -> set:

    unique_db_df = pd.read_csv('./data/UniqueDB ID (Cold).csv', low_memory=False)
    valid_numbers = pd.to_numeric(unique_db_df['Deal - Unique Database ID'], errors='coerce')
    valid_numbers = valid_numbers.dropna().astype(int)
    valid_id_set = set(valid_numbers)
    return valid_id_set

def clean_contact_id(df: pd.DataFrame, id_set: set) -> pd.DataFrame:

    if 'contact_id' in df.columns:
        df['contact_id'] = df['contact_id'].apply(pd.to_numeric, errors='coerce').astype('Int64')
        df = df[~df['contact_id'].isin(id_set)]

    return df

def export_output(df: pd.DataFrame, file_path: str, save_path: str) -> None:

    filename = os.path.basename(file_path)

    df['reason_for_removal'] = df['reason_for_removal'].apply(
        lambda lst: ', '.join(lst) if isinstance(lst, list) else lst
    )

    output_df = df[[
        'phone_number',
        'contact_id',
        'carrier_type',
        'full_name',
        'first_name',
        'last_name',
        'target_county',
        'target_state',
        'phone_index',
        'time_zone',
        'reason_for_removal'
    ]]

    if filename.endswith('.csv'):
        output_df.to_csv(f"{save_path}/(With Cleanup Tagging) {filename}", index=False)
    
    elif filename.endswith('.xlsx'):
        output_df.to_excel(f"{save_path}/(With Cleanup Tagging) {filename}", index=False)
    
    else:
        print("No output generated. Invalid file format")


def main(auth_code: str, files: tuple, save_path: str, run_mode: str):

    try:
        download_list_cleaner(auth_code)

        valid_phone_set = get_phone_set(run_mode)
        valid_id_set = get_id_set()

        for file in files:

            print(f"Processing file {file}")

            df = read_file(file)
            filtered_df = apply_all_filters(df, run_mode)
            output_df = filtered_df[filtered_df['phone_number'].isin(valid_phone_set) == False]
            final_df = clean_contact_id(output_df, valid_id_set)

            export_output(final_df, file, save_path)
        
        print("Successfully processed all files")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise RuntimeError

if __name__ == "__main__":
    main()
