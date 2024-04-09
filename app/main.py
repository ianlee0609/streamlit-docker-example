import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from itertools import product
import db_config



def get_ratio_info():
    bdcd_igs_ratio_df = pd.read_sql("""SELECT
                                    igs,igs_zh,ratio as igs_ratio
                                FROM
                                    igs_ratio
                                WHERE
                                    updated_at = (
                                        SELECT
                                            max(updated_at)
                                        FROM
                                            igs_ratio)
                                    and igs<20
                                    and uu>0           """, bdcd_superset_engine)

    bdcd_igs_demo_ratio_df = pd.read_sql("""SELECT
                                                igs_zh,demo,demo_ratio
                                            FROM
                                                demo_igs_ratio
                                            WHERE
                                                updated_at = (
                                                    SELECT
                                                        max(updated_at)
                                                    FROM
                                                        demo_igs_ratio)
                                                    AND igs < 20
                                                    AND demo NOT in('15-17F', '15-17M')  """, bdcd_superset_engine)

    city_mapping_dict = {1: '北部', 2:'中部' ,3: '南部',4:'東部', 6:'六都', 7:'非六都'}

    gsp_city_info_df = pd.read_sql("""
                                    SELECT
                                        id AS city_id,city_tw,
                                        region_id as hhid_region_id
                                    FROM
                                        cities
                                    WHERE
                                        region_id != 5
                                    UNION
                                    SELECT
                                        id AS city_id,
                                        city_tw,
                                        CASE WHEN municipality = 1 THEN
                                            6
                                        ELSE
                                            7
                                        END AS hhid_region_id
                                    FROM
                                        cities
                                    WHERE
                                        region_id != 5""", gspadmin_engine)

    gsp_city_ratio_df = pd.read_sql(""" SELECT
                                            feature_name AS city_id,
                                            ratio AS city_ratio
                                        FROM
                                            qp_feature_ratios
                                        WHERE
                                            feature_type = 'city'""", gspadmin_engine)
    
    gsp_city_ratio_df['city_id'] = gsp_city_ratio_df['city_id'].astype(int)
    gsp_city_ratio_merge_df = pd.merge(gsp_city_ratio_df,gsp_city_info_df,on='city_id')
    gsp_city_ratio_merge_df['hhid_region'] = gsp_city_ratio_merge_df['hhid_region_id'].map(city_mapping_dict)

    # 轉成選項
    igs_zh_list = bdcd_igs_ratio_df.sort_values(by='igs')['igs_zh'].to_numpy()
    demo_list = bdcd_igs_demo_ratio_df['demo'].unique()
    city_list = gsp_city_ratio_merge_df.sort_values(by='hhid_region_id')['hhid_region'].unique()

    merge_ratio_df = pd.merge(bdcd_igs_demo_ratio_df,
                            bdcd_igs_ratio_df, on='igs_zh')
    merge_ratio_df['product_ratio'] = merge_ratio_df['igs_ratio'] * merge_ratio_df['demo_ratio'] / 10000



    return igs_zh_list,demo_list,city_list,merge_ratio_df,gsp_city_ratio_merge_df





def produce_st_element():

    st.title("HHID 量體預估工具")
    # st.write("- 因目前母體是用去重複 uu 計算  \n - 興趣議題和年齡總數為140%  \n - 可能會有興趣增加或年齡增加 ratio 不變情況 (屬於正常)")

    # 選單
    selected_igs_list = st.multiselect(
        label='請選擇興趣', options=igs_zh_list, default=['新聞時事','家庭生活','科技3C','房屋地產','運動體育','健康保健','寵物動物']
    )

    selected_demo_list = st.multiselect(
        label='請選擇年齡性別', options=demo_list, default=demo_list
    )

    selected_city_list = st.multiselect(
        label='請選擇地區', options=city_list, default=['六都','北部']
    )

    send = st.button(':point_right: 進行量體預估', type='primary')
    st.divider()
    st.write(f"本次搜尋結果")
    return selected_igs_list,selected_demo_list,selected_city_list,send

def click_caculate_button(send):
    # 開始量體預估
    if send:
        # 使用 itertools 的 product 函数进行交叉连接
        cross_join = list(product(selected_igs_list, selected_demo_list))

        # 轉換為 Pandas DataFrame
        selected_cross_join_df = pd.DataFrame(cross_join, columns=['igs_zh', 'demo'])    
        selected_region_df = pd.DataFrame(selected_city_list, columns=['hhid_region'])


        sum_igs_demo_ratio = pd.merge(selected_cross_join_df, merge_ratio_df, on=[
                            'igs_zh', 'demo'])['product_ratio'].sum()

        # 計算 ratio
        sum_city_ratio = sum(pd.merge(gsp_city_ratio_merge_df,selected_region_df,on='hhid_region')['city_ratio'].unique())/100
        sum_igs_demo_ratio = round(sum_igs_demo_ratio,2)
        sum_city_ratio = round(sum_city_ratio,2)

        # sum ratio 會超過1 因為年齡性別 母體是 distinct uu, 不是直接加總
        if sum_igs_demo_ratio >1:
            sum_igs_demo_ratio=1.0

    
        st.write(f"【量體】  \n **{int(4000000*sum_igs_demo_ratio*sum_city_ratio):,}**")
        print(f"【量體】  \n 4,000,000 x {sum_igs_demo_ratio}(年齡興趣) x {sum_city_ratio}(地區) = **{int(4000000*sum_igs_demo_ratio*sum_city_ratio):,}**")
        st.write(f"【條件】  \n - 興趣：{selected_igs_list}  \n - 年齡：{selected_demo_list}  \n - 地區：{selected_city_list}")

    
if __name__=='__main__':

    st.set_page_config(
    page_title="HHID 量體預估工具",
    page_icon="tv"
        )
    # mysql 連線資訊
    gspadmin_engine = create_engine(db_config.gspadmin_url)
    bdcd_superset_engine = create_engine(db_config.superset_dashboard_url)


    igs_zh_list,demo_list,city_list,merge_ratio_df,gsp_city_ratio_merge_df = get_ratio_info()

    selected_igs_list,selected_demo_list,selected_city_list,send = produce_st_element()
    click_caculate_button(send)