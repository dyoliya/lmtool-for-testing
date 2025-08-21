import os
import re
import pandas as pd
import sqlite3
import warnings
from rapidfuzz.fuzz import ratio
from .well_name_matching import main as well_name_match

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None

def read_file(path: str) -> pd.DataFrame:
    if path.lower().endswith('.csv'):
        return pd.read_csv(path, low_memory=False)
    elif path.lower().endswith('.xlsx'):
        return pd.read_excel(path)
    else:
        raise RuntimeError('Invalid file type')

def get_well_df(db_path: str) -> pd.DataFrame:
    try:
        # Establish connection to SQLite database
        print("Extracting DB Browser Data")
        connection = sqlite3.connect(db_path)
        query = "SELECT * FROM wells"
        wells_df = pd.read_sql_query(query, connection)
        wells_df['rrc'] = wells_df['rrc'].astype('Int64')
        wells_df['well_name_number'] = wells_df.apply(lambda row: f"{row['well_name']} {row['well_number']}", axis=1)
        not_empty_rrc_df = wells_df[wells_df['rrc'].notna()].drop_duplicates()
        not_empty_rrc_df.loc[:, 'api10'] = not_empty_rrc_df['api10'].astype(str)
        not_empty_rrc_df.loc[:, 'api14'] = not_empty_rrc_df['api14'].astype(str)
        not_empty_rrc_df.loc[:, 'rrc'] = not_empty_rrc_df['rrc'].astype(str)
        grouped_df = not_empty_rrc_df.groupby('rrc').agg(
            lambda x: ' | '.join(set(str(v) if v is not None else '' for v in x))
        )
        return grouped_df, wells_df
    
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the database connection
        if connection:
            connection.close()

def format_rrc(row: pd.Series):
    if isinstance(row['RRC'], str) and "#" in row['RRC']:
        return row['RRC'].split("#")[-1].strip()
    return row['RRC']

def apply_mask(df: pd.DataFrame, mask, output_value) -> None:
    df.loc[mask, 'Notes'] = df.loc[mask, 'Notes'].apply(
        lambda lst: lst + [output_value] if isinstance(lst, list) else [output_value])
    
def remove_county(row):
    counties = row['county'].split(' | ')
    mh_county = row['mh_county']
    if mh_county in counties:
        counties.remove(mh_county)
    return ' | '.join(counties)

def remove_state(row):
    states = row['state'].split(' | ')
    mh_state = row['mh_state']
    if mh_state in states:
        states.remove(mh_state)
    return ' | '.join(states)

def check_operator_matching(row: pd.Series):
    notes = row.get('Notes', [])
    if pd.notna(row['operator']):
        all_di_operators = row['operator'].split("|")
        similarity_list = []
        for di_operator in all_di_operators:
            clean_oper = di_operator.strip()
            similarity = ratio(clean_oper, row["Operator"]) # Compare DI Oper with MH Oper
            similarity_list.append(similarity)
        best_case_ratio = max(similarity_list)
        if 100.0 > best_case_ratio >= 80.0:
            notes.append('Operator name CLOSE match')
        elif best_case_ratio < 80.0:
            notes.append('Operator name NOT matched')
        else:
            pass
        return notes

def add_missing_fields_note(row):
    columns_to_check = ['well_name', 'well_number', 'lease_name', 'operator', 'well_name_number']
    missing_columns = [col for col in columns_to_check if pd.isna(row[col])]
    notes = row.get('Notes', [])
    
    if pd.notna(row['api10']) and missing_columns:
        notes.append(f"Missing Fields: {', '.join(missing_columns)}")
    
    return notes

def extract_well_number(value):
    if pd.isna(value):
        return value
    elif "(" in value:
        parenthesis_split =  value.split("(")[-1].replace(")", "").strip()
        return extract_well_number(parenthesis_split)
    elif "#" in value:
        hash_split = value.split("#")[-1].strip()
        return extract_well_number(hash_split)
    elif "-" in value:
        dash_split = value.split("-")[-1].strip()
        return extract_well_number(dash_split)
    elif " " in value:
        space_split_last = value.split(" ")[-1].strip()
        space_split_first = value.split(" ")[0].strip()
        if re.search(r'\d', space_split_first):
            return extract_well_number(space_split_first)
        else:
            return extract_well_number(space_split_last)
    else:
        # Check if the value contains any digit
        if re.search(r'\d', value):
            return value  # Return the whole value if it contains a number
        else:
            return None  # Return None if it does not contain a number

def split_mh_well_numbers(value):
    if pd.notna(value) and isinstance(value, str):  # Ensure value is not NaN and is a string
        for delimiter in [",", "-", "&", '/']:
            if delimiter in value:
                # Split using the current delimiter and apply the function recursively
                split_values = [split_mh_well_numbers(num.strip()) for num in value.split(delimiter)]
                # Flatten the nested lists
                flat_list = [item for sublist in split_values for item in sublist]
                return list(set(flat_list))
    # If no delimiters are found or value is not a string, return as a single-element list
    return [value]

def pop_well_number(row: pd.Series):
    notes = row.get('Notes', [])
    mh_well_numbers = row.get('mh_well_numbers', [])
    if pd.notna(row['well_number']) and isinstance(row['mh_well_numbers'], list):
        try:
            di_well_numbers = row['well_number'].split(" | ")
            for well_number in di_well_numbers:
                mh_well_numbers.remove(well_number.strip())
                
            if len(mh_well_numbers) > 0:
                # Filter out None and convert items to strings
                cleaned_well_numbers = [str(w) for w in mh_well_numbers if w is not None]
                if cleaned_well_numbers:  # Check if the cleaned list has items
                    missing_well_numbers = ", ".join(cleaned_well_numbers)
                    if pd.notna(row['api10']):
                        notes.append(f"Missing well number: {missing_well_numbers}")
        except ValueError:
            pass  # well_number is not in the list, ignore

    return notes

def set_db_match(df: pd.DataFrame):
    # Identify rows where 'api10' is NaN
    no_match_rrc_mask = df['api10'].isna()

    # Apply the mask and set the 'db_match' column accordingly
    df['db_match'] = 'Y'  # Default to 'Y'
    df.loc[no_match_rrc_mask, 'db_match'] = 'N'  # Set to 'N' where the mask is True

    return df

def add_all_notes(row: pd.Series):
    notes = row.get('Notes', [])
    if isinstance(notes, list) and len(notes) > 0:
        return ", ".join(notes)
    elif isinstance(notes, list) and  len(notes) == 0 and row['db_match'] == 'Y':
        return 'Well matched in DI'
    else:
        return 'No match found in DB Browser'
    
def cleanup_input_file(df: pd.DataFrame):
    df['operator'] = df['operator'].str.replace(".", "")
    df['Operator'] = df['Operator'].str.strip()
    df['operator'] = df['operator'].str.strip()
    df['operator'] = df['operator'].str.replace(r'\s+', ' ', regex=True)
    df['operator'] = df['operator'].str.replace('PRODUCTION', 'PROD')

    # Helper columns
    df['similarity'] = df.apply(lambda row: ratio(row["operator"], row["Operator"]), axis=1)
    df['mh_county'] = df['County'].str.split(" ").str[0].str.upper().str.strip()
    df['mh_state'] = df['State'].str.upper().str.strip()

    # Add list of notes to be joined by commas later
    df['Notes'] = [[] for _ in range(len(df))]

    return df

def apply_all_filters(df: pd.DataFrame):

    # Empty operator logic
    empty_operator_mask = (pd.notna(df['api10'])) & (pd.isna(df['operator']))
    apply_mask(df, empty_operator_mask, 'Empty operator')

    # Partial or Exact Operator Match Logic
    df['Notes'] = df.apply(check_operator_matching, axis=1)

    # County Match Logic
    county_mask = (df['county'].notna()) & (df['mh_county'] != df['county'])
    df.loc[county_mask, 'county'] = df.loc[county_mask].apply(lambda row: remove_county(row), axis=1)
    df.loc[county_mask, 'Notes'] = df.loc[county_mask].apply(
        lambda row: row['Notes'] + [f"Found in {row['county']} county"], axis=1
    )

    # State Match Logic
    state_mask = (df['state'].notna()) & (df['mh_state'] != df['state'])
    df.loc[state_mask, 'state'] = df.loc[state_mask].apply(lambda row: remove_state(row), axis=1)
    df.loc[state_mask, 'Notes'] = df.loc[state_mask].apply(
        lambda row: row['Notes'] + [f"Found in {row['state']} state"], axis=1
    )

    # Missing Field Logic
    df['Notes'] = df.apply(add_missing_fields_note, axis=1)

    # Extract the raw well number from property
    df['raw_well_number'] = df['Property'].apply(extract_well_number)

    # Well Number Mismatch Logic
    well_number_mismatch_mask = (pd.notna(df['api10'])) & (df['raw_well_number'] != df['well_number'])
    apply_mask(df, well_number_mismatch_mask, 'Well Number Mismatch')

    # Extract all valid well numbers from raw well number
    df['mh_well_numbers'] = df['raw_well_number'].apply(split_mh_well_numbers)

    # Missing Well Numbers Logic
    df['Notes'] = df.apply(pop_well_number, axis=1)

    # Set the db_match if Y or N for tracking
    with_db_match_df = set_db_match(df)

    # Format all notes
    with_db_match_df['Notes'] = with_db_match_df.apply(add_all_notes, axis=1)

    # Rename and drop columns
    with_db_match_df.rename(columns={
            'id': 'Well ID',
            'api10': 'API10',
            'api14': 'API14',
            'well_status': 'Well Status',
            'well_name': 'DI Well Name',
            'well_number': 'DI Well Number',
            'lease_name': 'Lease Name',
            'operator': 'DI Operator Name',
            'well_name_number': 'Well Name & Number'}, inplace=True)
    
    with_db_match_df.drop(columns=['similarity',
                    'mh_county',
                    'mh_state',
                    'raw_well_number',
                    'mh_well_numbers',
                    'county',
                    'state',
                    'db_match'],
            axis=1,
            inplace=True)

    return with_db_match_df

def format_file_and_export(df: pd.DataFrame, file_path: str, save_path: str):
    filename = os.path.basename(file_path)
    if filename.endswith('.csv'):
        df.to_csv(f"{save_path}/(With Tagging) {filename}", index=False)
    elif filename.endswith('.xlsx'):
        df.to_excel(f"{save_path}/(With Tagging) {filename}", index=False)
    else:
        raise RuntimeError("No output generated. Invalid file format")

    
def main(db_file_path: str, file_paths: tuple, save_path: str):
    try:
        grouped_df, wells_df = get_well_df(db_file_path)

        for file in file_paths:

            print(f"Processing {os.path.basename(file)}")

            # Read and format input file
            df = read_file(file)

            # Match by well name and well number
            well_name_matched_df = well_name_match(wells_df, df)

            df['RRC'] = df.apply(format_rrc, axis=1)
            df['RRC'] = df['RRC'].astype('Int64')

            # Merge df with grouped_df to find matching RRC Numbers
            merged_df = df.merge(grouped_df, left_on='RRC', right_index=True, how='left')

            # Cleanup merged input file
            cleaned_df = cleanup_input_file(merged_df)

            # Apply all filters
            filtered_df = apply_all_filters(cleaned_df)

            # Add RRC Matched rows to Well Name Matched dataframe
            well_name_matched_df.loc[well_name_matched_df['Well ID'].isna(), :] = filtered_df.loc[well_name_matched_df['Well ID'].isna(), :].values

            # Fomart output file and export
            format_file_and_export(well_name_matched_df, file, save_path)

    except Exception as e:
        print(f"An error occurred: {e}")
        raise RuntimeError    

if __name__ == "__main__":
    main()
