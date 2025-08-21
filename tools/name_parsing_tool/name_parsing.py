import os
import pandas as pd

last_name_first = True

companies = ["LLC", "PARTNRSHP", "LIMITED", "ROYALT", " FUND ", "FOUNDATION", "PROPERT", "COMPANY", 
             "ENTERPRISE", "LLP", " LP", " OIL", "UNIVERSITY", "ENERGY", "LP.", "LTD", "INTERNATIONAL", "AGENCY", 
             "CITY ", " STATE", "CHURCH", " INC", "PARTNER", " CO.", "CORP", "MINERALS", "INVESTORS", "INVESTMENT"]
substitutions = [" ESTATE ", " ET AL", " ET UX ", " ETAL ", " ETUX ", " JR. ", " SR. ", " JR ", " SR ", " TRUSTEE ", 
                 "THE ESTATE OF ", "ESTATE OF ", " LIFE ", " EST ", " III ", " II ", " IV ", " V ", " VI ", " VII ",
                 " DR "," SR "," MRS "," MD "]
trust_changer = [{"old": " IRR ", "new": " IRREVOCABLE "}, 
                 {"old": " TR ", "new": " TRUST "}, 
                 {"old": " TRST ", "new": " TRUST "},
                 {"old": " REV ", "new": " REVOCABLE "},
                 {"old": " REVOC ", "new": " REVOCABLE "},
                 {"old": " REVC ", "new": " REVOCABLE "},
                 {"old": " LIV ", "new": " LIVING "},
                 {"old": " LVG ", "new": " LIVING "},
                 {"old": " FAM ", "new": " FAMILY "}]

def read_file(path: str):
    if path.endswith('.csv'):
        return pd.read_csv(path, low_memory=False)
    elif path.endswith('.xlsx'):
        return pd.read_excel(path)
    else:
        raise RuntimeError("Invalid file format")

def check_is_trust(name, contact_type):
    if name:
        name = " " + name.strip() + " "
        for changer in trust_changer:
            if changer["old"] in name:
                name = name.replace(changer["old"], changer["new"])
        if contact_type in ['TRUST', 'RELIGIOUS INSTITUTION']:
            return True
    return False

def check_is_company(name, contact_type):
    if name:
        name = " " + name.strip() + " "
        if contact_type == 'COMPANY':
            return True
    return False

def name_parser(row: pd.Series):
    name:str = row.get('Owner', "")
    contact_type = row.get('Suggested Contact Type', "")
    is_trust = check_is_trust(name, contact_type)
    is_company = check_is_company(name, contact_type)
    if is_company:
        return "", "", ""
    elif is_trust:
        name = " " + name.strip() + " "
        for changer in trust_changer:
            if changer["old"] in name:
                name = name.replace(changer["old"], changer["new"])
        return name.strip(), "", ""
    else:
        if name:
            name = name.strip() + " "
            for sub in substitutions:
                name = name.replace(sub, "")
            name = name.strip()
            if last_name_first:
                split_name = name.split(" ", 1)
                if len(split_name) == 1:
                    return name, "", ""
                second_split = split_name[1].split(" ", 1)
                second_split = [second_split[0], ""] if len(second_split) == 1 else second_split
                return second_split[0], second_split[1], split_name[0]
            else:
                split_name = name.split(" ", 1)
                if len(split_name) == 1:
                    return name, "", ""
                second_split = split_name[1].rsplit(" ", 1)
                second_split = ["", second_split[0]] if len(second_split) == 1 else second_split
                return split_name[0], second_split[0], second_split[1]
        return "", "", ""

def export_file(df: pd.DataFrame, save_path: str, file: str):

    filename = os.path.basename(file)
    if filename.endswith('.csv'):
        df.to_csv(f"{save_path}/(Name Parsed) {filename}", index=False)
    
    elif filename.endswith('.xlsx'):
        df.to_excel(f"{save_path}/(Name Parsed) {filename}", index=False)

def main(files: tuple, save_path: str):

    try:
        for file in files:

            print(f"Processing {os.path.basename(file)}")

            df = read_file(file)
            required_columns = ['Owner', 'First Name', 'Middle Name', 'Last Name']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ""

            # Apply name parsing
            parsed_names = df.astype(str).apply(name_parser, axis=1)
            df[['First Name', 'Middle Name', 'Last Name']] = pd.DataFrame(parsed_names.tolist(), index=df.index)
            export_file(df, save_path, file)

        print("Successfully Processed All Files")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise RuntimeError
    
if __name__ == "__main__":
    main()
