import os
import pandas as pd
import warnings
from sqlalchemy import create_engine
from dotenv import load_dotenv
from urllib.parse import quote
from .sql_queries import *
from .get_pipedrive_data import main as update_pipedrive
from .follow_up import process_fu
from .new_deals import process_new_deals

warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def read_cm_live_db() -> 'tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame | None]':

    try:
        # Create database engine
        host = os.getenv('DB_HOST')
        user = os.getenv('DB_USER')
        name = os.getenv('DB_NAME')
        password = os.getenv('DB_PASSWORD')
        engine = create_engine(f'mysql+pymysql://{user}:{quote(password)}@{host}/{name}')

        print(f'Reading Community Minerals Database')

        # Execute query and fetch the data into a Pandas Dataframe
        phone_number_df = pd.read_sql_query(phone_number_query, engine)
        emaiL_address_df = pd.read_sql_query(email_address_query, engine)
        serial_numbers_df = pd.read_sql_query(serial_numbers_query_mysql, engine)
        cm_db_df = pd.read_sql_query(cm_db_query, engine)

        # Change data type of phone number to int
        phone_number_df['phone_number'] = phone_number_df[phone_number_df['phone_number']\
                                                          .str.contains(r'^[0-9]+$', na=False)]\
                                                            ['phone_number'].astype('Int64')

        return phone_number_df, emaiL_address_df, serial_numbers_df, cm_db_df

    except Exception as e:
        raise RuntimeError(f"An error occurred while reading from the database: {e}")

    finally:
        engine.dispose()

def read_file(path: str) -> pd.DataFrame:

    if path.endswith('.csv'):
        return pd.read_csv(path, low_memory=False)
    
    elif path.endswith('.xlsx'):
        return pd.read_excel(path)
    
    else:
        return None

def main(files: tuple, save_path: str):

    try:
        load_dotenv(dotenv_path='misc/.env')
        phone_number_df, email_address_df, serial_numbers_df, cm_db_df = read_cm_live_db()
        update_pipedrive()
        pipedrive_df = read_file('./data/pipedrive/pipedrive_data.csv')

        for i, file in enumerate(files, start=1):

            print(f"Processing {os.path.basename(file)}")

            df = read_file(file)
            output_type = 'Inactive' if 'Reason for Not Selling' in df.columns else 'Live'
            no_deal_id_final, cm_db_not_exist = process_fu(df,
                                                           pipedrive_df,
                                                           phone_number_df,
                                                           cm_db_df,
                                                           save_path,
                                                           i,
                                                           output_type)
            process_new_deals(no_deal_id_final,
                            cm_db_not_exist,
                            email_address_df,
                            serial_numbers_df,
                            cm_db_df,
                            save_path,
                            i,
                            output_type)

        print("Successfully Processed All Files")

    except Exception as e:
        print(f"An error occured: {e}")
        raise RuntimeError


if __name__ == "__main__":
    main()
