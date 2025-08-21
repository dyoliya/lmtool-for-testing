import pandas as pd

def search_phone_number(df: pd.DataFrame,
                        pipedrive_df: pd.DataFrame) -> 'tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]':

    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].fillna('')
    pipedrive_df = pipedrive_df[pipedrive_df['phone_number'].str.strip() != '']
    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].str.split(',')
    pipedrive_df['phone_number'] = pipedrive_df['phone_number'].apply(lambda x: sorted(set(x), key=x.index))
    df_exploded = pipedrive_df.explode('phone_number').reset_index(drop=True)

    merged_df = df.merge(df_exploded,
                         left_on='From',
                         right_on='phone_number',
                         how='left')
    fu_df = merged_df[merged_df['Deal - ID'].notna()][['From', 'To', 'Text', 'Deal Created Date', 'Deal - ID']]
    no_deals_df = merged_df[merged_df['Deal - ID'].isna()].drop(columns=['phone_number'], axis=1)

    return fu_df, no_deals_df, df_exploded

def get_cm_db_deals(no_deals_df: pd.DataFrame,
                    phone_number_df: pd.DataFrame,
                    df_exploded: pd.DataFrame,
                    cm_db_df: pd.DataFrame):

    phone_number_df['phone_number'] = phone_number_df['phone_number'].astype(str)
    cm_check = no_deals_df.merge(phone_number_df,
                                left_on='From',
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
    no_deal_id_final = no_deal_id[~no_deal_id['From'].isin(deal_id_exist_final['From'])]

    merge_pd_deal_id_df = deal_id_exist_final.merge(df_exploded,
                                                    left_on='deal_id',
                                                    right_on='Deal - ID',
                                                    how='left')
    merge_pd_deal_id_df.drop(columns=['id'], axis=1, inplace=True)
    merge_pd_deal_id_df.rename(columns={'deal_id': 'Deal - ID'}, inplace=True)
    cm_deals_final_df = merge_pd_deal_id_df[['From', 'To', 'Text', 'Deal Created Date', 'Deal - ID']]

    return cm_deals_final_df, no_deal_id_final, cm_db_not_exist

def export_fu(fu_df: pd.DataFrame,
              cm_deals_final_df: pd.DataFrame,
              save_path: str,
              i: int,
              output_type: str) -> None:

    fu_final_df = pd.concat([fu_df, cm_deals_final_df])
    fu_final_df['Assigned to user'] = 'Keena'
    fu_final_df['Done'] = 'Done'
    fu_final_df['Type'] = 'Text'
    fu_final_df['Subject'] = fu_final_df.apply(
        lambda x: f"Text from {x['From']} to {x['To']}",
        axis=1
    )
    fu_final_df['Due date'] = fu_final_df['Deal Created Date']
    rename_df = fu_final_df.rename(columns={
        'Text': 'Activity note',
        'Deal Created Date': 'Activity creation date',
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
    ]].to_excel(f'{save_path}/{i}. ({output_type}) FU - Missing Deals Text.xlsx', index=False)


def process_fu(df: pd.DataFrame,
               pipedrive_df: pd.DataFrame,
               phone_number_df: pd.DataFrame,
               cm_db_df: pd.DataFrame,
               save_path: str,
               i: int,
               output_type: str) -> pd.DataFrame:
    
    print("Creating Follow up")
    
    df['From'] = df['From'].astype(str).apply(lambda x: x[1:])
    df['To'] = df['To'].astype(str).apply(lambda x: x[1:])
    fu_df, no_deals_df, df_exploded = search_phone_number(df, pipedrive_df)
    cm_deals_final_df, no_deal_id_final, cm_db_not_exist = get_cm_db_deals(no_deals_df,
                                                                           phone_number_df,
                                                                           df_exploded,
                                                                           cm_db_df)
    export_fu(fu_df, cm_deals_final_df, save_path, i, output_type)

    return no_deal_id_final, cm_db_not_exist
    
if __name__ == "__main__":
    process_fu()
