import os
import pandas as pd
from datetime import datetime
from .get_pipedrive_data import main as update_pipedrive
import xlwings as xw

def read_file(path: str, name: str) -> pd.DataFrame:
    if path.endswith('.xlsm'):
        return pd.read_excel(path, sheet_name=name)
    else:
        return None

def format_phone(lookup_df: pd.DataFrame) -> pd.DataFrame:
    filtered_df = lookup_df[lookup_df['Deal ID'].isna()]
    if 'From' in filtered_df.columns:
        phone_column = 'From'
        filtered_df['phone'] = filtered_df[phone_column]
        filtered_df['phone'] = filtered_df['phone'].astype(str).apply(lambda x: x[1:] if len(x) == 11 else x)
        filtered_df['phone'] = pd.to_numeric(filtered_df['phone'], errors='coerce').astype('Int64').astype(str)
    else:
        phone_column = 'ANI'
        filtered_df['phone'] = filtered_df[phone_column]
        filtered_df['phone'] = filtered_df['phone'].astype(str).apply(lambda x: x[1:] if len(x) == 13 else x)
        filtered_df['phone'] = pd.to_numeric(filtered_df['phone'], errors='coerce').astype('Int64').astype(str)

    return filtered_df, phone_column

def format_pipedrive_data(pipedrive_df: pd.DataFrame) -> dict:
    print("Formatting Pipedrive data")

    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].fillna('').astype(str)
    pipedrive_df = pipedrive_df[pipedrive_df['phone_number'].str.strip() != '']
    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].str.split(',')
    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].apply(
        lambda x: sorted(set(x), key=x.index)
    )

    pipedrive_final_data = pipedrive_df.explode('phone_number').reset_index(drop=True)
    pipedrive_final_data['phone_number'] = pipedrive_final_data['phone_number'].str.replace(r'\D', '', regex=True)
    pipedrive_final_data = pipedrive_final_data[pipedrive_final_data['phone_number'] != '']

    grouped_df = (
        pipedrive_final_data.groupby('phone_number')['Deal - ID']
        .agg(lambda row: " | ".join(row.astype(str).unique()))
        .reset_index()
    )
    phone_to_deal = grouped_df.set_index('phone_number')['Deal - ID'].to_dict()
    return phone_to_deal

def lookup_text(lookup_df: pd.DataFrame, phone_column: str, phone_to_deal: dict, save_path: str, i: int) -> None:
    lookup_df[['Deal ID', 'Resolved By']] = lookup_df.apply(
        lambda row: (
            phone_to_deal.get(row['phone'], row['Deal ID']) if pd.isna(row['Deal ID']) else row['Deal ID'], 
            'Joyce Marie Gempesaw' if pd.isna(row['Deal ID']) and row['phone'] in phone_to_deal else row['Resolved By']
        ),
        axis=1,
        result_type='expand'
    )

    with xw.App(visible=False) as app:
        wb = app.books.open(save_path)
        sheet = wb.sheets['lookup_texts']
        sheet.range('A1').value = ['Phone', 'Deal ID', 'Resolved By']
        sheet.range('A2').value = lookup_df[[phone_column, 'Deal ID', 'Resolved By']].values
        wb.save()

def lookup_call(lookup_df: pd.DataFrame, phone_column: str, phone_to_deal: dict, save_path: str, i: int) -> None:
    lookup_df[['Deal ID', 'Resolved by', 'Resolve Date']] = lookup_df.apply(
        lambda row: (
            phone_to_deal.get(row['phone'], row['Deal ID']) if pd.isna(row['Deal ID']) else row['Deal ID'], 
            'Joyce Marie Gempesaw' if pd.isna(row['Deal ID']) and row['phone'] in phone_to_deal else row['Resolved by'],   
            datetime.today().strftime('%m/%d/%Y') if pd.isna(row['Deal ID']) and row['phone'] in phone_to_deal else row['Resolve Date']
        ),
        axis=1,
        result_type='expand'
    )

    with xw.App(visible=False) as app:
        wb = app.books.open(save_path)
        sheet = wb.sheets['lookup_calls']
        sheet.range('A1').value = ['Phone', 'Resolved by', 'Resolve Date', 'Deal ID']
        sheet.range('A2').value = lookup_df[[phone_column, 'Resolved by', 'Resolve Date', 'Deal ID']].values
        wb.save()

def main(files: tuple, save_path: str):
    try:
        update_pipedrive()
        pipedrive_df = pd.read_csv('./data/pipedrive/pipedrive_data.csv', low_memory=False)
        phone_to_deal_dict = format_pipedrive_data(pipedrive_df)

        for i, file in enumerate(files, start=1):
            print(f"Processing {os.path.basename(file)}")

            for name in ['raw_calls', 'raw_texts']:
                df = read_file(file, name)
                formatted_df, phone_column = format_phone(df)
                if 'Resolve Date' in formatted_df.columns:
                    lookup_call(formatted_df, phone_column, phone_to_deal_dict, file, i) 
                else:
                    lookup_text(formatted_df, phone_column, phone_to_deal_dict, file, i)

        print("Successfully Processed All Files")

    except Exception as e:
        print(f"An error occured: {e}")
        raise RuntimeError

if __name__ == "__main__":
    main()
