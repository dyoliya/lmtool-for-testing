import os
import re
import pandas as pd
import warnings
import dropbox
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

disposition_query = """
SELECT
	dnis_to
FROM
	max_outbound_calls
WHERE
	primary_disposition IS NOT NULL AND
    primary_disposition IN 
	(
		'Business/ Work number',
		'Sold Interests',
		'Incorrect contact / Wrong number',
		'Do Not Call Again (remove from list)',
		'Invalid Number',
		'Proactive Identified - Answering Machine Left Message',
		'Answering Machine Left Message'
	)
GROUP BY
	dnis_to
"""

six_months_query = """
WITH ranked_calls AS (
    SELECT
        dnis_to,
        ROW_NUMBER() OVER (PARTITION BY dnis_to ORDER BY start_time DESC) AS date_rank
    FROM
        max_outbound_calls
    WHERE
        primary_disposition IN ('Lead Not interested', 'Uncooperative Lead')
        AND start_time BETWEEN DATE_ADD(CURRENT_DATE, INTERVAL -6 MONTH) AND CURRENT_DATE
)
SELECT
    dnis_to
FROM
    ranked_calls
WHERE
    date_rank = 1;
"""

def extract_list_cleaner_file(auth_code: str, local_path: str, dropbox_path: str):
    dbx = dropbox.Dropbox(auth_code)
    metadata, response = dbx.files_download(dropbox_path)
    with open(local_path, 'wb') as f:
        f.write(response.content)

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

def read_cm_live_db() -> 'tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame | None]':

    try:
        # Create database engine
        host = os.getenv('DB_HOST')
        user = os.getenv('DB_USER')
        name = os.getenv('DB_NAME')
        password = os.getenv('DB_PASSWORD')
        engine = create_engine(f'mysql+pymysql://{user}:{quote(password)}@{host}/{name}')

        print(f'Reading Community Minerals Database')

        disposition_df = pd.read_sql_query(disposition_query, engine)
        six_months_df = pd.read_sql_query(six_months_query, engine)

        disposition_df['dnis_to'] = pd.to_numeric(disposition_df['dnis_to'], errors='coerce')
        disposition_df['dnis_to'] = disposition_df['dnis_to'].astype('Int64')
        disposition_set = set(disposition_df.loc[disposition_df['dnis_to'].notna(), 'dnis_to'].map(int))

        six_months_df['dnis_to'] = pd.to_numeric(six_months_df['dnis_to'], errors='coerce')
        six_months_df['dnis_to'] = six_months_df['dnis_to'].astype('Int64')
        months_set = set(six_months_df.loc[six_months_df['dnis_to'].notna(), 'dnis_to'].map(int))

        return disposition_set, months_set

    except Exception as e:
        raise RuntimeError(f"An error occurred while reading from the database: {e}")

    finally:
        engine.dispose()


def export_output(df: pd.DataFrame, file_path: str, save_path: str) -> None:

    # Capitalization of all names
    columns_to_transform = ['Owner','Combined Name', 'First Name', 'Middle Name', 'Last Name']
    df[columns_to_transform] = df[columns_to_transform].applymap(lambda x: x.title() if isinstance(x, str) else x)

    filename = os.path.basename(file_path)
    if filename.endswith('.csv'):
        df.to_csv(f"{save_path}/(Clean file) {filename}", index=False)
    
    elif filename.endswith('.xlsx'):
        df.to_excel(f"{save_path}/(Clean file) {filename}", index=False)

    elif filename.endswith('.xlsb'):
        df.to_excel(f"{save_path}/(Clean file) {filename.split('.')[0]}.xlsx", index=False)
    
    else:
        print("No output generated. Invalid file format")

def export_reclean_output(df: pd.DataFrame, file_path: str, save_path: str) -> None:

    # Capitalization of all names
    columns_to_transform = ['Owner', 'First Name']
    df[columns_to_transform] = df[columns_to_transform].applymap(lambda x: x.title() if isinstance(x, str) else x)

    filename = os.path.basename(file_path)
    if filename.endswith('.csv'):
        df.to_csv(f"{save_path}/(Re-clean file) {filename}", index=False)
    
    elif filename.endswith('.xlsx'):
        df.to_excel(f"{save_path}/(Re-clean file) {filename}", index=False)

    elif filename.endswith('.xlsb'):
        df.to_excel(f"{save_path}/(Re-clean file) {filename.split('.')[0]}.xlsx", index=False)
    
    else:
        print("No output generated. Invalid file format")

def read_file(path: str):

    if path.endswith('.csv'):
        return pd.read_csv(path, low_memory=False)

    elif path.endswith('.xlsx'):
        return pd.read_excel(path)
    
    elif path.endswith('.xlsb'):
        return pd.read_excel(path, engine='pyxlsb', sheet_name=['List'])['List']
    
    else:
        raise ValueError("Invalid file format: Please provide a .csv, .xlsx or .xlsb file.")
    
def is_valid_phone(phone):
    return bool(re.fullmatch(r'\d{10,15}', phone))

def remove_phone_dupes(df: pd.DataFrame) -> pd.DataFrame:

    df['original_index'] = df.index
    phone_columns = ['phone1', 'phone2', 'phone3', 'phone4', 'phone5']
    sorted_df = df.sort_values(by=phone_columns, ascending=False)

    for phone in phone_columns:
        sorted_df.loc[(sorted_df[phone].notna()) & (sorted_df[phone].duplicated(keep='last')), phone] = pd.NA
    
    phone_filter_mask = (sorted_df['phone5'].isin(sorted_df['phone2'])) \
    | (sorted_df['phone5'].isin(sorted_df['phone3'])) \
    | (sorted_df['phone5'].isin(sorted_df['phone4'])) \
    | (sorted_df['phone5'].isin(sorted_df['phone1']))
    sorted_df.loc[(sorted_df['phone5'].notna()) & (phone_filter_mask), 'phone5'] = pd.NA

    phone_filter_mask = (sorted_df['phone4'].isin(sorted_df['phone3'])) \
    | (sorted_df['phone4'].isin(sorted_df['phone2'])) \
    | (sorted_df['phone4'].isin(sorted_df['phone1']))
    sorted_df.loc[(sorted_df['phone4'].notna()) & (phone_filter_mask), 'phone4'] = pd.NA

    phone_filter_mask = (sorted_df['phone3'].isin(sorted_df['phone2'])) \
    | (sorted_df['phone3'].isin(sorted_df['phone1']))
    sorted_df.loc[(sorted_df['phone3'].notna()) & (phone_filter_mask), 'phone3'] = pd.NA

    phone_filter_mask = (sorted_df['phone2'].isin(sorted_df['phone1']))
    sorted_df.loc[(sorted_df['phone2'].notna()) & (phone_filter_mask), 'phone2'] = pd.NA
            
    sorted_df = sorted_df.sort_values(by='original_index')
    sorted_df = sorted_df.drop(columns='original_index')
    return sorted_df

def clean_contact_id_deal_id(df: pd.DataFrame, id_set: set) -> pd.DataFrame:

    if 'contact_id' in df.columns:
        df['contact_id'] = df['contact_id'].apply(pd.to_numeric, errors='coerce').astype('Int64')
        df = df[~df['contact_id'].isin(id_set)]
    
    if 'Deal ID' in df.columns:
        df = df[df['Deal ID'].isna()]

    final_df = df[~df[['phone1', 'phone2', 'phone3', 'phone4', 'phone5']].isna().all(axis=1)]

    return final_df

def get_phone_set() -> tuple[set, set]:

    data_path = './data'

    # Initial cleaning phone set
    file_list = [
        "CCM+CH+MVPC+MVPT+JC+RC+PD (Cold).csv",
        "DNC (Cold-PD).csv",
        "CallOut-14d+TextOut-30d (Cold).csv",
        "CallTextOut-7d (PD).csv",
        "PDConvDup (PD).csv",
        "PDJRAADups (PD).csv"
    ]
    final_list_cleaner_df = pd.concat([pd.read_csv(os.path.join(data_path, file), low_memory=False, header=None) for file in file_list], ignore_index=True)
    valid_phone_set = set(int(phone) for phone in map(str, final_list_cleaner_df[0].tolist()) if is_valid_phone(phone))

    # Recleaning phone set
    recleaning_list = [
        "CCM+CH+MVPC+MVPT+JC+RC+PD (Cold).csv",
        "DNC (Cold-PD).csv",
        "PDConvDup (PD).csv",
        "PDJRAADups (PD).csv"
    ]
    final_list_recleaner_df = pd.concat([pd.read_csv(os.path.join(data_path, file), low_memory=False, header=None) for file in recleaning_list], ignore_index=True)
    valid_phone_reclean_set = set(int(phone) for phone in map(str, final_list_recleaner_df[0].tolist()) if is_valid_phone(phone))
    
    return valid_phone_set, valid_phone_reclean_set

def get_id_set() -> set:

    unique_db_df = pd.read_csv('./data/UniqueDB ID (Cold).csv', low_memory=False)
    valid_numbers = pd.to_numeric(unique_db_df['Deal - Unique Database ID'], errors='coerce')
    valid_numbers = valid_numbers.dropna().astype(int)
    valid_id_set = set(valid_numbers)
    return valid_id_set

def upper_first(text):
    if pd.isna(text):
        return text
    words = text.split()
    return " ".join([word.title() if not re.fullmatch(r'(?i)(i{1,3}|iv|v?i{0,3}|ix|x{1,3}|xl|l{1,3}|xc|c{1,3}|cd|d{1,3}|cm|m{1,4})', word) else word.upper() for word in words])

def export_text_marketing(df: pd.DataFrame, file_path: str, save_path: str):

    filename = os.path.basename(file_path)
    if filename.endswith('.csv'):
        df.to_csv(f"{save_path}/(Autodialer - Text Marketing) {filename}", index=False)
    
    elif filename.endswith('.xlsx'):
        df.to_excel(f"{save_path}/(Autodialer - Text Marketing) {filename}", index=False)

    elif filename.endswith('.xlsb'):
        df.to_excel(f"{save_path}/(Autodialer - Text Marketing) {filename.split('.')[0]}.xlsx", index=False)
    
    else:
        print("No output generated. Invalid file format")

def text_marketing_melt(df: pd.DataFrame):

    columns_to_transform = ['First Name', 'Owner']
    id_vars = [
        'row_order',
        'date_created',
        'is_latest_offer',
        'First Name',
        'Total Value - High ($)',
        'County',
        'State',
        'Serial Number',
        'Owner',
        'Contact Type'
    ]
    selected_columns = [
        'date_created',
        'is_latest_offer',
        'First Name',
        'Total Value - High ($)',
        'County',
        'State',
        'Serial Number',
        'Owner',
        'Contact Type',
        'phone1',
        'phone2',
        'phone3',
        'phone4',
        'phone5'
    ]

    df = df[selected_columns]
    df['row_order'] = df.index
    df[columns_to_transform] = df[columns_to_transform].map(upper_first)
    df_melted = df.melt(id_vars=id_vars, 
                        value_vars=['phone1', 'phone2', 'phone3', 'phone4', 'phone5'],
                        var_name='Phone Index', 
                        value_name='Phone Number')
    df_melted = df_melted.dropna(subset=['Phone Number'])
    df_melted['Phone Index'] = df_melted['Phone Index'].str.extract('(\d)').astype(int)
    df_melted = df_melted.sort_values(by=['row_order', 'Phone Index'])
    df_melted = df_melted.drop(columns='row_order').reset_index(drop=True)
    df_melted['Total Value - High ($)'] = df_melted['Total Value - High ($)'].astype('Int64')
    df_melted['Phone Number'] = df_melted['Phone Number'].astype('Int64')
    export_df = df_melted[[
        'date_created',
        'is_latest_offer',
        'Phone Index',
        'Phone Number',
        'First Name',
        'Total Value - High ($)',
        'County',
        'State',
        'Serial Number',
        'Owner',
        'Contact Type'
    ]]

    return export_df

def main(auth_code: str, list_files: tuple, save_path: str, run_mode: str):

    try:
        download_list_cleaner(auth_code)

        valid_phone_set, valid_reclean_phone_set = get_phone_set()
        valid_id_set = get_id_set()
        disposition_set, months_set = read_cm_live_db()
        
        for list_file in list_files:

            print(f"Processing file {os.path.basename(list_file)}")
            list_df = read_file(list_file)

            # Run recleaning
            if run_mode == 'recleaning':
                list_df['Phone Number'] = list_df['Phone Number'].apply(pd.to_numeric, errors='coerce').astype('Int64')
                recleaning_df = list_df[~list_df['Phone Number'].isin(valid_reclean_phone_set)]
                export_reclean_output(recleaning_df, list_file, save_path)
                continue

            # Convert phone numbers to int
            phone_columns = ['phone1', 'phone2', 'phone3', 'phone4', 'phone5']
            list_df[phone_columns] = (
                list_df[phone_columns]
                .apply(pd.to_numeric, errors='coerce')
                .astype('Int64')
            )

            # Search phones in cleaner file
            output_df = list_df[~list_df[phone_columns].isin(valid_phone_set).any(axis=1)]

            # Remove Company contact type
            column_name = next((col for col in output_df.columns if col.strip().lower() == 'contact_type'), None)
            if column_name:
                output_df = output_df[output_df[column_name].str.lower() != 'company']
            
            # Remove duplicates
            removed_dupes_df = remove_phone_dupes(output_df)

            # Clean df based on contact id and deal id
            clean_contact_deal_df = clean_contact_id_deal_id(removed_dupes_df, valid_id_set)

            # Check if has existing dispositions
            clean_dispo_df = clean_contact_deal_df[~clean_contact_deal_df[phone_columns].isin(disposition_set).any(axis=1)]

            # Check if within 6 months for specific dispositions
            final_df = clean_dispo_df[~clean_dispo_df[phone_columns].isin(months_set).any(axis=1)]

            if run_mode == 'text_marketing':
                text_marketing_df = text_marketing_melt(final_df)
                export_text_marketing(text_marketing_df, list_file, save_path)
            else:
                export_output(final_df, list_file, save_path)
        
        print("Sucessfully processed all files")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise RuntimeError   

if __name__ == "__main__":
    main()
