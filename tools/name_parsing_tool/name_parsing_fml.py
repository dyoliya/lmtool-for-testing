# -------------------------ABOUT --------------------------

# Tool: Name Parsing Tool
# Description: For parsing names - First Middle Last
# Original Creator: Aziz
# Modified and maintained: Julia
# Added to universal tool: 2025-08-26

# ---------------------------------------------------------


import os
import io
import re
import pandas as pd

pd.options.mode.chained_assignment = None

trust_keywords = ['REVOCABLE TRUST', 'TESTAMENTARY TRUST', 'LIVING TRUST', 'LIV TR', 'IRREVOCABLE TRUST',  'CHARITABLE TRUST', 'GRANT TR',
                  'PRIVATE TRUST', 'PUBLIC TRUST', 'GRANTOR TRUST', 
                  'CHARITABLE TR', 'GIFTING TRUST', 'PUBLIC BENEFIT TRUST', 'RESEARCH TRUST', 'GRANTORS TRUST',
                  'SOCIAL TRUST', 'T/U/W', 'TUW',
                  'FBO', 'NON-GST', 'RELVTR', 'REVTR', 'UNITR', 'UNITRUST', 'REV INTR', 'RVLVTR', 'REVLVTR', 'LVTR', 'LVG TRS',
                  'REVTR', 'EXECTR', 'SUPPLEMENTALTR', 'IRMGTTR', 'AG/TR', 'LV/TR', 'FAM/TR', '2022TR', 'TRUST', 'EXMPT',
                  'FAMILY TRUST', 'REV TRUST', 'TRST', 'TST', 'LIVTR', 'R/TR', 'COTR', 'TR UWO', 'TRUWO', 'GRANTOR TR'
                  'TR U/A', ' TR 1', ' TR 2', ' TR #', 'TR#', 'SUPP NDS TRS', 'FAMILY REVOCABLE', 'REVOC TR',
                  'FAMILY TRT', 'TEST TR', 'FAMILY LIV', 'TR %COMPASS BANK', 'REVOCABLE', 'GRANTORS TR',
                  'IRREVOCABLE', 'EXEMPT TR', 'TR UA', 'REVOCABLE LIVING', 'REV LIV', 'MARITAL TRT', 'IRREV TR', 'TR NUMBER',
                  'TR (CCCA)', '2010 TRS', 'TR 01', 'TRS DTD', 'TR DTD', 'TRS', 'HERITAGE TR', 'IRREV TRU', 'TESTAMENTARY TRU',
                  'TESTAMENTARY TR', 'TES TR', 'REV TRS', 'TR U-A', 'TR U/W', 'TR UW', 'GIFT TR', 'BANK FBO', 'BANK F/B/O', ' TR 5',
                  ' TR 3', ' TR 4', ' TR 6', ' TR 7', ' TR 8', ' TR 9', ' TR 0', '0 TR', '1 TR', '2 TR', '3 TR', '4 TR', '5 TR',
                  '6 TR', '7 TR', '8 TR', '9 TR', 'LIVING', 'REV TR', 'IRREV TR', 'FAMILY TR', 'FAM TRT', 'FAM TRST', 'TRT', 'RES TRUS',
                  'CHILDREN\'S TRUS', 'TR OF', 'RES TR', 'TR UTD', 'PARENT TR', 'RESIDUARY TR', 'TR NUM', 'TR NO', 'TR UNDER', 'FAM TR',
                  'TR A', 'TR B', 'TR C', 'TR D', 'TR E', 'TR FBO', 'TR F/B/O', 'TR F', 'TR G', 'TR N' , 'LAND TR ',
                  'TRUST FBO', 'GST NON', 'GST EX', 'GST TR', 'LIV TRST', 'GST TST', 'GSTTR', 'GST FAM', 'GST FMLY', 'GST-EX', 'GST GIFT',
                  'GST T', 'GSTT EX', 'C/O']

address_replacements = {
    r'\bCOURT\b': 'CT',
    r'\bSTREET\b': 'ST',
    r'\bLANE\b': 'LN',
    r'\bDRIVE\b': 'DR',
    r'\bROAD\b': 'RD',
    r'\bAVENUE\b': 'AVE',
    r'\bHIGHWAY\b': 'HWY',
    r'\bTRAIL\b': 'TRL',
    r'\bCIRCLE\b': 'CR',
    r'\bAPARTMENT\b': 'APT',
    r'\bSUITE\b': 'STE',
    r'\bPARKWAY\b': 'PKWY',
    r'\bBOULEVARD\b': 'BLVD',
    r'\bNORTH\b': 'N',
    r'\bSOUTH\b': 'S',
    r'\bEAST\b': 'E',
    r'\bWEST\b': 'W',
    r'\bNORTHEAST\b': 'NE',
    r'\bSOUTHEAST\b': 'SE',
    r'\bSOUTHWEST\b': 'SW',
    r'\bNORTHWEST\b': 'NW',
    r'\bP.O.\b': 'PO'
}

address_pattern = re.compile('|'.join(address_replacements.keys()), flags=re.IGNORECASE)

# separate those that have year
trust_keywords.extend([str(year) for year in range(1900, 2025)])


individual_keywords = ['ESTATE', 'TRUSTEE', 'TRSTEE', ' TTEE', '-TTEE', 'HEIRS ET AL', 'HIS HEIRS', 'THE HEIR', 'HEIRS TRUST',
                       'HEIRS UNK', 'HEIRS - UNKNOWN', 'HEIRS', 'HEIRS - UNLEASED', 'NO HEIRS', 'HER HEIRS','SUCCESSOR', 'HEIR']
companies = ["LLC", "PARTNRSHP", "LIMITED", "ROYALT", " FUND ", "FOUNDATION", "PROPERT", "COMPANY", 
             "ENTERPRISE", "LLP", " LP", " OIL", "UNIVERSITY", "ENERGY", "LP.", "LTD", "INTERNATIONAL", "AGENCY", 
             "CITY ", " STATE", "CHURCH", " INC", "PARTNER", " CO.", "CORP", "MINERALS", "INVESTORS", "INVESTMENT"]
substitutions = [r"\bTHE ESTATE OF\b", r"\bESTATE OF\b", r"\bET AL\b", r"\bET UX\b", r"\bETAL\b", r"\bETUX\b", r"\bJR.\b", r"\bSR.\b", r"\bJR\b", r"\bSR\b", r"\bTRUSTEE\b", 
                 r"\bESTATE\b", r"\bLIFE\b", r"\bEST\b", r"\bIII\b", r"\bII\b", r"\bIV\b", r"\bVI\b", r"\bVII\b",
                 r"\bDR\b", r"\bSR\b", r"\bMRS\b", r"\bMD\b", r"\bJTROS\b", r"\bJTWRS\b", r"\bHOMEPLACE\b", r"\bJTWROS\b", r"\bTBE\b", r"\bLE\b", r"\bJ/T\b"]
trust_changer = {
    r"\bREV\b": "REVOCABLE",
    r"\bREVOC\b": "REVOCABLE",
    r"\bREVC\b": "REVOCABLE",
    r"\bIRR\b": "IRREVOCABLE",
    r"\bIRRV\b": "IRREVOCABLE",
    r"\bIRV\b": "IRREVOCABLE",
    r"\bIRREV\b": "IRREVOCABLE",
    r"\bIRRVCABLE\b": "IRREVOCABLE",
    r"\bLIV\b": "LIVING",
    r"\bLVG\b": "LIVING",
    r"\bFAM\b": "FAMILY",
    r"\bFMLY\b": "FAMILY",
    r"\bTR\b": "TRUST",
    r"\bTRST\b": "TRUST",
    r"\bTRT\b": "TRUST",
    r"\bTST\b": "TRUST",
    r"\bTSTEE\b": "TRUSTEE",
    r"\bTSTEES\b": "TRUSTEES",
    r"\bTTEE\b": "TRUSTEE",
    r"\bTSTE\b": "TRUSTEE",
    r"\bTSTEE\b": "TRUSTEE",
    r"\bTRTEE\b": "TRUSTEE",
}

attn_keywords = ("ATTN", "C/O", "c/o", "%")

def replace_match_address(m):
    word = m.group()
    return address_replacements.get(rf'\b{word.upper()}\b', word)

def process_trust_and_company(df: pd.DataFrame):
    trust_mask = (df['Contact Type'].isin(['TRUST']))
    # df.loc[(trust_mask) & (df['Owner'].notna()), 'Owner'] = df.loc[(trust_mask) & (df['Owner'].notna()), 'Owner'].replace(trust_changer, regex=True)
    df.loc[trust_mask, 'First Name'] = df.loc[(trust_mask) & (df['Owner'].notna()), 'Owner'].replace(trust_changer, regex=True)
    # df.loc[trust_mask, 'First Name'] = df.loc[trust_mask, 'Owner'].str.strip()
    df.loc[trust_mask, ['Middle Name', 'Last Name']] = pd.NA
    df.loc[trust_mask, 'is_parsed'] = 'Y - Trust'

    company_mask = (df['Contact Type'].isin(['COMPANY', 'RELIGIOUS INSTITUTION', 'UNKNOWN']))
    df.loc[company_mask, ['First Name', 'Middle Name', 'Last Name']] = pd.NA
    df.loc[company_mask, 'is_parsed'] = 'Y - Company, Religious Institutions & Unknown'
    
def get_first_name(row: pd.Series):
    row = [name for name in row if pd.notna(name)]  # Remove NA values
    return row[0] if len(row) >= 1 else pd.NA
    # return " ".join(row[:-1]) if len(row) > 1 else (row[0] if row else pd.NA)

def get_middle_name(row: pd.Series):
    row = [name for name in row if pd.notna(name)]  # Remove NA values
    return f'{" ".join(row[1:])} '.replace(' & ', '').replace(' AND ', '') if len(row) >= 2 else pd.NA

def get_last_name(row: pd.Series):
    row = [name for name in row if pd.notna(name)]  # Remove NA values
    return row[-1] if row[-1] not in ['&', 'AND'] else row[-2]

def join_no_middle_name(name_list):
    if not isinstance(name_list, list) or len(name_list) < 2:
        return None, None, None  # Return None for invalid cases.
    
    last_name = name_list[0]  # First element as last name
    first_name = name_list[1]  # Second element as first name
    middle_name = " ".join(name_list[2:]) if len(name_list) > 2 else None  # Everything after the second element

    return last_name, first_name, middle_name

def format_attn(value: str) -> str:
    """
    Standardize ATTN values:
    - Remove ALL leading prefixes at the start (ATTN, C/O, %, with optional spaces/colon)
    - Handle case-insensitive and 'C / O' variants
    - Print a debug line showing what was removed
    - Return 'ATTN: <rest>' or '' if nothing meaningful
    """
    if not isinstance(value, str) or value.strip() == "":
        return ""

    # Normalize spaces & invisible chars
    val = str(value).replace("\u00A0", " ").strip()
    val = re.sub(r"\s+", " ", val)

    # Pattern to match ONE leading prefix; we'll loop to remove multiple
    # Capture the keyword so we can print it
    prefix_re = re.compile(r'^(ATTN|C\s*/\s*O|%)[:\s]*', flags=re.IGNORECASE)

    removed = []
    while True:
        m = prefix_re.match(val)
        if not m:
            break
        kw_raw = m.group(1)
        # Normalize the captured keyword for logging
        kw_norm = "C/O" if re.match(r'c\s*/\s*o', kw_raw, flags=re.IGNORECASE) else kw_raw.upper()
        removed.append(kw_norm)
        val = val[m.end():].lstrip()

    ########### for debugging purposes only
    # if removed:
    #     print(f"DEBUG: Removed prefixes {removed} from '{value}' -> '{val}'")

    # If nothing left after cleaning, keep it blank so extract_attn_from_owner() can fill it
    if not val:
        return ""

    return "ATTN: " + val

def extract_attn_from_owner(owner: str, attn: str) -> str:
    """Fill ATTN from Owner if missing"""
    attn_clean = attn.strip() if isinstance(attn, str) else ""
    if attn_clean and attn_clean.upper() != "ATTN:":
        return attn  # already has something, leave as is

    if not isinstance(owner, str):
        return attn  # nothing to extract

    # Look for common prefixes in Owner
    m = re.search(r'(ATTN.*|C/O.*|c/o.*|%.*)', owner, flags=re.IGNORECASE)
    if m:
        return m.group(0)  # return raw match, cleaning happens later
    return attn


def clean_attn(df):
    """Run full ATTN cleanup pipeline on a DataFrame"""
    
    def clean_row(owner, attn):
        # Case 1: ATTN is empty or just spaces → try extracting from Owner
        if not isinstance(attn, str) or attn.strip() == "":
            attn = extract_attn_from_owner(owner, attn)
        # Case 2: ATTN already exists → just clean it
        return format_attn(attn)

    df['ATTN'] = df.apply(lambda row: clean_row(row['Owner'], row['ATTN']), axis=1)
    return df

def process_name_parsing(df: pd.DataFrame):
    df_columns = [
        'id', 'Source', 'Owner', 'Owner ID', 'First Name', 'Middle Name', 'Last Name', 'ATTN', 'Address', 'City', 'State', 'Zip Code',
        '# of Interests', 'PDP Value ($)', 'Total Value - Low ($)', 'Total Value - High ($)', 'County', 'Target State', 'Contact Type'
    ]
    df['id'] = df.index
    df['Middle Name'] = pd.NA
    df = df[df_columns]
    df['Owner'] = df['Owner'].str.strip()
    df['Contact Type'] = df['Contact Type'].str.strip().str.upper()
    df['owner_copy'] = df['Owner'].replace(substitutions, "", regex=True)
    df['owner_copy'] = df['owner_copy'].str.replace(".", "")
    df['owner_copy'] = df['owner_copy'].str.replace(",", "")
    df['owner_copy'] = df['owner_copy'].str.strip()
    df['Address'] = df['Address'].str.replace(address_pattern, replace_match_address, regex=True)

    individual_mask = (df['Contact Type'].isin(['INDIVIDUAL', 'COMBINED INDIVIDUALS']))
    two_contact_mask = (df['owner_copy'].str.contains(r' & | AND ', na=False, regex=True))
    df.loc[individual_mask, 'owner_copy'] = (df.loc[individual_mask, 'owner_copy'].replace(substitutions, "", regex=True).str.strip())
    df.loc[individual_mask, 'Last Name'] = df.loc[individual_mask, 'owner_copy'].str.split(" ").apply(get_last_name)
    df.loc[two_contact_mask & individual_mask, 'split_owner'] = df.loc[two_contact_mask & individual_mask, 'owner_copy'].str.split(r' & | AND ')
    owner_exploded_df = df.explode('split_owner')
    owner_exploded_df['split_owner'] = owner_exploded_df.apply(
        lambda x: x['owner_copy'] if pd.isna(x['split_owner']) else x['split_owner'],
        axis=1
    )
    exploded_individual_mask = (owner_exploded_df['Contact Type'].isin(['INDIVIDUAL', 'COMBINED INDIVIDUALS'])) & (owner_exploded_df['split_owner'].isna())
    owner_exploded_df.loc[exploded_individual_mask, 'split_owner'] = (
        owner_exploded_df.loc[exploded_individual_mask, 'owner_copy']
        .str.split()
        .apply(lambda x: " ".join([part.strip() for part in x]))
    )
    owner_exploded_df.loc[individual_mask & owner_exploded_df['split_owner'].notna(), 'split_owner'] = (
        owner_exploded_df.loc[individual_mask & owner_exploded_df['split_owner'].notna()]
        .apply(lambda row: row['split_owner'].replace(row['Last Name'], '').strip(), axis=1)
    )
    tagging_mask = (owner_exploded_df['split_owner'].notna()) & (owner_exploded_df['Contact Type'].isin(['INDIVIDUAL', 'COMBINED INDIVIDUALS']))
    owner_exploded_df.loc[tagging_mask, 'is_parsed'] = 'Y - First Middle Last'

    # Split to get the First Name and Last Name List
    split_names = owner_exploded_df.loc[individual_mask & owner_exploded_df['split_owner'].notna(), 'split_owner'].str.split(" ")

    # Assign First Name
    owner_exploded_df.loc[individual_mask & owner_exploded_df['split_owner'].notna(), 'First Name'] = split_names.apply(get_first_name)

    # Assign Last Name
    owner_exploded_df.loc[individual_mask & owner_exploded_df['split_owner'].notna(), 'Middle Name'] = split_names.apply(get_middle_name)

    process_trust_and_company(owner_exploded_df)
    owner_exploded_df['Zip Code'] = owner_exploded_df['Zip Code']
    owner_exploded_df.drop(columns=['id',
                                        'owner_copy',
                                        'split_owner',], axis=1, inplace=True)
    
    owner_exploded_df = clean_attn(owner_exploded_df)

    return owner_exploded_df

# def read_file(path: str) -> pd.DataFrame:
def read_file(path: str):
    if path.endswith(".csv"):
        return pd.read_csv(path, low_memory=False)
    elif path.endswith(".xlsx"):
        return pd.read_excel(path)
    
def export_file(df: pd.DataFrame, save_path: str, file_name: str) -> None:
    if file_name.endswith(".csv"):
        df.to_csv(f"{save_path}/(Name Parsed) {file_name}", index=False)
    elif file_name.endswith(".xlsx"):
        df.to_excel(f"{save_path}/(Name Parsed) {file_name}", index=False)

def main(files: tuple, save_path: str):
    for path in files:
        df = read_file(path)
        file_name = os.path.basename(path)
        print("Processing ", file_name)
        required_columns = ['Owner', 'First Name', 'Middle Name', 'Last Name']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        df.rename(columns={'Suggested Contact Type': 'Contact Type'}, inplace=True)
        output_df = process_name_parsing(df)
        export_file(output_df, save_path, file_name)


if __name__ == "__main__":
    main()
