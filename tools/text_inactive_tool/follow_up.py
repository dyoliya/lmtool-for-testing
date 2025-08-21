import pandas as pd

def format_phone(row: str) -> str:
    if row[7] == '1':
        return row[8:18]

    else:
        return row[8:11] + row[13:16] + row[17:21]

def format_not_phone_number(df: pd.DataFrame):
    pd.options.mode.chained_assignment = None
    df['Phone'] = df.apply(
        lambda row: format_phone(row['Note']) if not str(row['Phone']).isdigit() else row['Phone'],
        axis=1)
    df['Phone'] = df['Phone'].astype(str)

def search_phone_number(df: pd.DataFrame,
                        pipedrive_df: pd.DataFrame) -> 'tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]':

    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].fillna('')
    pipedrive_df = pipedrive_df[pipedrive_df['phone_number'].str.strip() != '']
    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].str.split(',')
    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].apply(lambda x: sorted(set(x), key=x.index))
    df_exploded = pipedrive_df.explode('phone_number').reset_index(drop=True)
    # deal_ids = df_exploded.groupby('phone_number')['Deal - ID']\
    #     .agg(lambda x: " | ".join(map(str, pd.unique(x))))
    # df_exploded['all_deal_id'] = df_exploded['phone_number'].map(deal_ids)

    merged_df = df.merge(df_exploded,
                         left_on='Phone',
                         right_on='phone_number',
                         how='left')
    fu_df = merged_df[merged_df['Deal - ID'].notna()][['Note', 'Activity - Subject', 'Activity - Due date', 'Deal - ID']]
    no_deals_df = merged_df[merged_df['Deal - ID'].isna()].drop(columns=['phone_number'], axis=1)

    return fu_df, no_deals_df, df_exploded

def get_cm_db_deals(no_deals_df: pd.DataFrame,
                    phone_number_df: pd.DataFrame,
                    df_exploded: pd.DataFrame,
                    cm_db_df: pd.DataFrame):

    phone_number_df['phone_number'] = phone_number_df['phone_number'].astype(str)
    cm_check = no_deals_df.merge(phone_number_df,
                                left_on='Phone',
                                right_on='phone_number',
                                how='left')
    cm_db_exist = cm_check[cm_check['id'].notnull()]
    cm_db_not_exist = cm_check[cm_check['id'].isna()]
    cm_db_not_exist['Deal - Deal Summary'] = 'No Information in Email'

    # Filter contacts that has deal id
    filter_deal_id_df = cm_db_df[cm_db_df['deal_id'].notnull()][['id', 'deal_id']]

    # Add Deal ID Column to existing ANI Numbers
    get_deal_id_df = cm_db_exist.merge(filter_deal_id_df,
                                    on='id',
                                    how='left')
    deal_id_exist = get_deal_id_df[get_deal_id_df['deal_id'].notnull()]
    deal_id_exist['deal_id'] = deal_id_exist['deal_id'].astype('int64')
    deal_id_exist_final = deal_id_exist[deal_id_exist['deal_id'].isin(df_exploded['Deal - ID'])]
    no_deal_id = get_deal_id_df[get_deal_id_df['deal_id'].isna()].drop(columns='deal_id', axis=1)
    no_deal_id_final = no_deal_id[~no_deal_id['Phone'].isin(deal_id_exist_final['Phone'])]

    merge_pd_deal_id_df = deal_id_exist_final.merge(df_exploded,
                                                    left_on='deal_id',
                                                    right_on='Deal - ID',
                                                    how='left')
    # merge_pd_deal_id_df['all_deal_id'] = merge_pd_deal_id_df.groupby('Phone')['deal_id'].transform(
    #     lambda x: " | ".join(x.astype(str).unique()) if x.nunique() > 1 else str(x.iloc[0])
    # )
    merge_pd_deal_id_df.drop(columns=['id'], axis=1, inplace=True)
    merge_pd_deal_id_df.rename(columns={'deal_id': 'Deal - ID'}, inplace=True)
    cm_deals_final_df = merge_pd_deal_id_df[['Note', 'Activity - Subject', 'Activity - Due date', 'Deal - ID']]

    return cm_deals_final_df, no_deal_id_final, cm_db_not_exist

def export_fu(fu_df: pd.DataFrame,
              cm_deals_final_df: pd.DataFrame,
              save_path: str,
              i: int) -> None:

    fu_final_df = pd.concat([fu_df, cm_deals_final_df])
    fu_final_df['Assigned to user'] = 'Data Team'
    fu_final_df['Done'] = 'Done'
    fu_final_df['Type'] = 'Text'
    rename_df = fu_final_df.rename(columns={
        'Note': 'Activity note',
        'Activity - Subject': 'Subject',
        'Activity - Due date': 'Due date',
        'Deal - ID': 'Deal ID'})
    drop_dupes_df = rename_df.drop_duplicates(subset=['Activity note', 'Deal ID'])
    drop_dupes_df[[
        'Activity note',
        'Assigned to user',
        'Done',
        'Subject',
        'Type',
        'Due date',
        'Deal ID'
    ]].to_excel(f'{save_path}/{i}. FU - Text Inactive.xlsx', index=False)


def process_fu(df: pd.DataFrame,
               pipedrive_df: pd.DataFrame,
               phone_number_df: pd.DataFrame,
               cm_db_df: pd.DataFrame,
               save_path: str,
               i: int) -> pd.DataFrame:
    
    print("Creating Follow up")
    
    format_not_phone_number(df)
    fu_df, no_deals_df, df_exploded = search_phone_number(df, pipedrive_df)
    cm_deals_final_df, no_deal_id_final, cm_db_not_exist = get_cm_db_deals(no_deals_df,
                                                                           phone_number_df,
                                                                           df_exploded,
                                                                           cm_db_df)
    export_fu(fu_df, cm_deals_final_df, save_path, i)

    return no_deal_id_final, cm_db_not_exist
    
if __name__ == "__main__":
    process_fu()
