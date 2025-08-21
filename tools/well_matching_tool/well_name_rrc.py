import re
import pandas as pd
from rapidfuzz.fuzz import ratio
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None

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
    if pd.notna(row['clean_operator_name']):
        all_di_operators = row['clean_operator_name'].split("|")
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

def extract_well_name(row):
    if pd.isna(row):
        return row
    elif "#" in row and "(" in row:
        # Find indices of # and (
        hash_index = row.find("#")
        paren_index = row.find("(")
        
        # Handle content in parentheses
        end_paren = row.find(")")
        content_in_parens = row[paren_index + 1 : end_paren]
        
        # Remove parentheses if they contain both # and a comma
        if "#" in content_in_parens:
            well_name = (row[:paren_index] + row[end_paren + 1 :]).strip()
            return well_name
        
        # Handle adjacency between # and (
        if abs(hash_index - paren_index) == 1:
            # Split at the lowest index between the two
            min_index = min(hash_index, paren_index)
            well_name = row[:min_index].strip()
            return well_name
        
        # Split at the highest index if not beside each other
        max_index = max(hash_index, paren_index)
        well_name = row[:max_index].strip()
        return well_name
    
    elif "#" in row:
        well_name = row.split("#")[0].strip()
        return well_name
    elif "(" in row:
        splitted_row = row.rsplit("(", 1)
        if not any(char.isdigit() for char in splitted_row[-1]):
            return row.strip()
        else:
            return splitted_row[0].strip()
    elif "-" in row:
        well_name = row.split("-")[0].strip()
        return well_name
    else:
        return row

# Function to process the values
def extract_well_number(value):
    if pd.isna(value):
        return value
    elif "(" in value:
        parenthesis_split =  value.split("(")[-1].replace(")", "").strip()
        return extract_well_number(parenthesis_split)
    elif "#" in value:
        hash_split = value.split("#")[-1].strip()
        return hash_split
    elif "-" in value:
        dash_split = value.split("-")[-1].strip()
        return extract_well_number(dash_split)
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

            # Well Number Mismatch Logic
            di_well_set = set(di_well_numbers)
            mh_well_set = set(mh_well_numbers)
            if di_well_set != mh_well_set:
                notes.append("Well Number Mismatch")

            # Missing Well Number Logic
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
    df['clean_mh_well_name'] = df['mh_well_name'] \
        .str.replace("GAS UNIT", "GU") \
        .str.strip() \
        .str.replace(".", "") \
        .str.replace(",", "") \
        .str.replace('"', '') \
        .str.strip()
    df['row_number'] = df.index
    exploded_df = df.explode('mh_well_numbers')
    exploded_df['clean_combined_name'] = exploded_df.apply(
        lambda row: f"{row['clean_mh_well_name']} {row['mh_well_numbers']}" if row['mh_well_numbers'] not in [None, ''] else row['clean_mh_well_name'],
        axis=1
    )

    return exploded_df

def clean_di_file(well_df: pd.DataFrame):
    well_name_search_df = well_df.drop_duplicates()
    well_name_search_df['clean_di_well_name'] = well_name_search_df['well_name'] \
        .str.replace("GAS UNIT", "GU") \
        .str.strip() \
        .str.replace(".", "") \
        .str.replace(",", "") \
        .str.replace('"', '') \
        .str.strip()
    
    well_name_search_df['clean_combined_name'] = well_name_search_df.apply(
        lambda row: f"{row['clean_di_well_name']} {row['well_number']}" if row['well_number'] not in [None, ''] else row['clean_di_well_name'],
        axis=1
    )
    # well_name_search_df.drop_duplicates(subset=['clean_combined_name'], inplace=True)

    return well_name_search_df

def merge_and_filter(exploded_df: pd.DataFrame, well_name_search_df: pd.DataFrame, orig_df: pd.DataFrame):
    merged_df = exploded_df.merge(well_name_search_df,
                                  left_on=['clean_combined_name', 'RRC'],
                                  right_on=['clean_combined_name', 'rrc'],
                                  how='left')
    filtered_df = merged_df[merged_df['id'].notna()]
    filtered_df['id'] = filtered_df['id'].astype(int)
    filtered_df['api10'] = filtered_df['api10'].astype(int)
    filtered_df['api14'] = filtered_df['api14'].astype(int)

    columns_to_separate = [
        'row_number',
        'raw_well_number',
        'mh_well_numbers',
        'clean_mh_well_name',
        'clean_combined_name',
        'id',
        'api10',
        'api14',
        'well_status',
        'well_name',
        'well_number',
        'lease_name',
        'operator',
        'county',
        'state',
        'well_name_number',
        'clean_di_well_name'
    ]

    selected_cols_df = filtered_df[columns_to_separate]
    grouped_df = selected_cols_df.groupby('row_number').agg(
        lambda x: ' | '.join(set(str(v) if pd.notna(v) else '' for v in x))
    ).reset_index()

    # Add well matched rows to the original dataframe
    add_well_matched_df = orig_df.merge(grouped_df,
                                        on='row_number',
                                        how='left')
    
    # Add list of notes to be joined by commas later
    add_well_matched_df['Notes'] = [[] for _ in range(len(add_well_matched_df))]
    add_well_matched_df['mh_county'] = add_well_matched_df['County'].str.split(" ").str[0].str.upper().str.strip()
    add_well_matched_df['mh_state'] = add_well_matched_df['State'].str.upper().str.strip()
    add_well_matched_df['clean_operator_name'] = add_well_matched_df['operator'] \
        .str.replace('PRODUCTION', "PROD") \
        .str.replace('.', "") \
        .str.replace(',', "") \
        .str.replace(r'\s+', ' ', regex=True) \
        .str.strip()
    
    return add_well_matched_df

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

    # # Well Number Mismatch Logic
    # well_number_mismatch_mask = (pd.notna(df['api10'])) & (df['raw_well_number'] != df['well_number'])
    # apply_mask(df, well_number_mismatch_mask, 'Well Number Mismatch')

    # Extract all valid well numbers from raw well number
    df['mh_well_numbers'] = df['raw_well_number'].apply(split_mh_well_numbers)

    # Missing Well Numbers Logic
    df['Notes'] = df.apply(pop_well_number, axis=1)

    # Set the db_match if Y or N for tracking
    with_db_match_df = set_db_match(df)

    # Format all notes
    with_db_match_df['Notes'] = with_db_match_df.apply(add_all_notes, axis=1)

    return with_db_match_df

def apply_first_filters(df: pd.DataFrame):
    # Extract well name
    df['mh_well_name'] = df['Property'].apply(extract_well_name)

    # Example output for this:
    # ROGERS BILLIE NEAL GU 1/3/4/5 -> ROGERS BILLIE NEAL GU
    df['mh_well_name'] = df['mh_well_name'].str.replace(r'\b\d+(?:/\d+)+\b', '', regex=True).str.strip()
    df['raw_well_number'] = df['Property'].apply(extract_well_number)
    df['mh_well_numbers'] = df['raw_well_number'].apply(split_mh_well_numbers)

    return df
    
def main(well_df: pd.DataFrame, df: pd.DataFrame):
    try:
        
        # Make copies of input dataframes
        well_name_matching_df = df.copy()
        well_name_matching_well_df = well_df.copy()

        # Format input df
        well_name_matching_df['RRC'] = well_name_matching_df.apply(format_rrc, axis=1)
        well_name_matching_df['RRC'] = well_name_matching_df['RRC'].astype('Int64')

        # Create orig_df for reference
        orig_df = well_name_matching_df.copy()
        orig_df['row_number'] = orig_df.index

        # Apply first input file filters for well name then cleanup
        with_well_name_df = apply_first_filters(well_name_matching_df)
        cleaned_input_df = cleanup_input_file(with_well_name_df)

        # Cleanup well df
        cleaned_di_df = clean_di_file(well_name_matching_well_df)

        # Match by well name and number
        well_matched_df = merge_and_filter(cleaned_input_df, cleaned_di_df, orig_df)

        # Apply the rest of the filters
        final_df = apply_all_filters(well_matched_df)

        # Clean up
        final_df.rename(columns={
            'id': 'Well ID',
            'api10': 'API10',
            'api14': 'API14',
            'well_status': 'Well Status',
            'well_name': 'DI Well Name',
            'well_number': 'DI Well Number',
            'lease_name': 'Lease Name',
            'operator': 'DI Operator Name',
            'well_name_number': 'Well Name & Number'}, inplace=True)
        
        final_df.drop(columns=[
                        'mh_county',
                        'mh_state',
                        'raw_well_number',
                        'mh_well_numbers',
                        'county',
                        'state',
                        'db_match',
                        'clean_di_well_name',
                        'row_number',
                        'clean_mh_well_name',
                        'clean_combined_name',
                        'clean_operator_name'],
                axis=1,
                inplace=True)

        # Return to main for further processing
        return final_df

    except Exception as e:
        print(f"An error occurred: {e}")
        raise RuntimeError    

if __name__ == "__main__":
    main()
