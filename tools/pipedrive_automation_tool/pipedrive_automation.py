import os
import pandas as pd
import pymysql
import warnings
from dotenv import load_dotenv
from tqdm import tqdm

def read_file(path: str) -> pd.DataFrame:

    if path.endswith('.csv'):
        return pd.read_csv(path, low_memory=False)
    
    elif path.endswith('.xlsx'):
        return pd.read_excel(path)
    
    else:
        return None

def connect_to_db():

    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    name = os.getenv('DB_NAME')
    password = os.getenv('DB_PASSWORD')

    connection = pymysql.connect(
        host=host,
        user=user,
        database=name,
        password=password,
    )

    return connection

def get_serials(
        database_id: str,
        df: pd.DataFrame,
        cursor,
        row,
        i
    ) -> None:

    serials_query = f"""
    SELECT
        GROUP_CONCAT(DISTINCT s.serial_number SEPARATOR ' | ') AS serial_numbers
    FROM
        contact_serial_numbers s
    LEFT JOIN
        contacts c ON s.contact_id = c.id
    WHERE 1=1
        AND s.contact_id IN ({database_id})
        AND s.serial_number NOT LIKE '%MUS%'
        AND s.serial_number NOT LIKE '%CMS%';
    """

    # Execute query and fetch result
    cursor.execute(serials_query)
    result = cursor.fetchone()

    # Collect serial numbers from the query
    if result[0]:
        unique_serials = set(str(result[0]).split(" | "))
    else:
        unique_serials = set()

    # Process the 'Deal - Serial Number' column in the DataFrame to add unique serials
    serial_column_value = row.get('Deal - Serial Number')
    if pd.notna(serial_column_value):
        # Split serials if there's a " | " separator and add only unique ones
        for serial in str(serial_column_value).split(" | "):
            if serial not in unique_serials:
                unique_serials.add(serial)

    # Join the unique serials and store in 'new_serials'
    df.loc[i, 'new_serials'] = " | ".join(unique_serials)

def get_mailing_address(
        database_id: str,
        df: pd.DataFrame,
        cursor,
        row,
        i
    ) -> None:

    address_query = f"""
    SELECT
        address,
        city,
        state,
        postal_code
    FROM
        contact_skip_traced_addresses
    WHERE 1=1
        AND contact_id IN ({database_id})
        AND address IS NOT NULL
        AND city IS NOT NULL
        AND state IS NOT NULL
        AND postal_code IS NOT NULL
    LIMIT 1;
    """    

    address_column_value = row.get('Person - Mailing Address')
    if pd.isna(address_column_value):
    
        cursor.execute(address_query)
        result = cursor.fetchone()

        if result:
            new_address = f"{result[0]}, {result[1]}, {result[2]}, {result[3]}, USA".upper()
        else:
            new_address = None

        df.loc[i, 'Person - Mailing Address'] = new_address

def get_phone_number(
        database_id: str,
        df: pd.DataFrame,
        cursor,
        row,
        i
    ) -> None:

    phone_number_query = f"""
    SELECT 
        DISTINCT phone_number
    FROM
        contact_phone_numbers
    WHERE 1=1
        AND contact_id IN ({database_id})
        AND phone_number IS NOT NULL
        AND phone_index IS NOT NULL
    ORDER BY
        phone_index;
    """

    columns_to_check = [
        'Person - Phone - Work',
        'Person - Phone - Home',
        'Person - Phone - Mobile',
        'Person - Phone - Other',
        'Person - Phone 1'
    ]

    if row[columns_to_check].isna().all():

        cursor.execute(phone_number_query)
        result = cursor.fetchall()
        df.loc[i, 'Person - Phone'] = ", ".join([str(phone[0]) for phone in result])
        for phone_index, phone in enumerate(result, start=1):
            df.loc[i, f'Person - Phone {phone_index}'] = int(phone[0])

def get_email_address(
        database_id: str,
        df: pd.DataFrame,
        cursor,
        row,
        i
    ) -> None:

    email_query = f"""
    SELECT
        DISTINCT email_address
    FROM
        contact_email_addresses
    WHERE 1=1
        AND contact_id IN ({database_id})
        AND email_address IS NOT NULL;
    """

    email_column_value = row.get('Person - Email 1')
    if pd.isna(email_column_value):

        cursor.execute(email_query)
        result = cursor.fetchall()
        if result:
            df.loc[i, 'Person - Email'] = result[0][0]
            for index, email in enumerate(result[:17], start=1):
                df.loc[i, f'Person - Email {index}'] = email[0]

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

def add_constants(df: pd.DataFrame) -> None:

    timezone_dict = get_timezone_dict()
    df['Person - Timezone'] = df.apply(get_timezone,
                                        tz_dict=timezone_dict,
                                        axis=1)
    df['Deal - Serial Number'] = df['new_serials']
    df['Deal - Deal Summary'] = 'Completed'
    df.drop(columns=['new_id',
                     'new_serials',
                     'Deal - Unique Database ID',
                     'Deal - Abandoned Call Flag',
                     'Deal - Title',
                     'Deal - County (Old)',
                     'Deal - Deal Status',
                     'Deal - Stage'], axis=1, inplace=True)

def split_id(id):
    return ", ".join(str(id).split(" | "))

def export_file(df: pd.DataFrame, save_path: str, file: str):

    filename = os.path.basename(file)
    if filename.endswith('.csv'):
        df.to_csv(f"{save_path}/(Automation Output) {filename}", index=False)
    
    elif filename.endswith('.xlsx'):
        df.to_excel(f"{save_path}/(Automation Output) {filename}", index=False)

def main(files: tuple, save_path: str):

    try:
        load_dotenv(dotenv_path='./misc/.env')
        warnings.filterwarnings("ignore", category=FutureWarning)

        for file in files:
            print(f"Processing {os.path.basename(file)}")

            df = read_file(file)
            df['new_id'] = df['Deal - Unique Database ID'].apply(split_id)
            df['new_serials'] = ''
            df['Notes'] = ''
            df['Person - Email'] = ''
            df['Person - Phone'] = ''
            connection = connect_to_db()

            with connection.cursor() as cursor:
                for i, row in tqdm(df.iterrows(), total=df.shape[0], unit='entry'):

                    database_id = row.get('new_id')
                    get_serials(database_id, df, cursor, row, i)
                    get_mailing_address(database_id, df, cursor, row, i)
                    get_phone_number(database_id, df, cursor, row, i)
                    get_email_address(database_id, df, cursor, row, i)
                        
            add_constants(df)
            export_file(df, save_path, file)

        print("Successfully Processed All Files")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise RuntimeError
    
    finally:
        connection.close()

if __name__ == "__main__":
    main(None, None)
