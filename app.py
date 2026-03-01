import streamlit as st
import pandas as pd
import json

# --- 1. 頁面藝術化論述與設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景")

# 使用淡藍色 #C4E1FF 作為藝術標題
st.markdown("""
<div style="text-align: center; border-bottom: 0.5px solid #333; padding-bottom: 20px; margin-bottom: 30px;">
<h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 2px; font-family: sans-serif;'>
🌿 台灣蛙鳴環境聲景地圖
</h1>
<p style='color: #888; font-size: 1.1em; font-weight: 200;'>
  每一聲紀錄如晨露般落下，泛起柔和的聲紋漣漪，沒入台灣的夜色中。
</p>
</div>
""", unsafe_allow_html=True)

# --- 2. 資料讀取與時序排序 ---
@st.cache_data
def load_and_process_data():
    def try_read(file_name):
        # 嘗試多種編碼，這對台灣中文字資料非常重要
        for enc in ['utf-8', 'big5', 'cp950', 'utf-8-sig']:
            try:
                return pd.read_csv(file_name, encoding=enc)
            except:
                continue
        return pd.read_csv(file_name, encoding='latin1')

    # 讀取真實 CSV 資料
    df_raw = try_read('raw_data.csv')
    df_verified = try_read('verified_data.csv')
    
    for df in [df_raw, df_verified]:
        # 強制經緯度轉為數字，並移除髒資料
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        # 轉為日期格式以便精確排序
        df['Create Date'] = pd.to_datetime(df['Create Date'], errors='coerce')
    
    # 這是依序滴入的關鍵：按 Create Date 排序
    df_raw_sorted = df_raw.sort_values('Create Date').dropna(subset=['Latitude', 'Longitude', 'Create Date'])
    df_verified_sorted = df_verified.sort_values('Create Date').dropna(subset=['Latitude', 'Longitude', 'Create Date'])
    
    return df_raw_sorted, df_verified_sorted

# 執行資料載入
try:
    raw_data, verified_data = load_and_process_data()
except Exception as e:
    st.error(f"資料讀取失敗，請確認 root 目錄有正確的 CSV 檔案。錯誤: {e}")
    st.stop()

# --- 3. 生成台灣輪廓與依序水滴動畫 HTML/JS ---
def create_immersive_glow_map(df_r, df_v):
    # 準備資料給 JS，注意欄位名稱大小寫要與原本 CSV 一致
    raw_json = df_r[['Latitude', 'Longitude', 'Username']].to_json(orient='records')
    verified_json = df_v[['Latitude', 'Longitude', 'Review Identity']].to_json(orient='records')

    # 台灣經緯度簡單投影，設定投影範圍
    projection_config = {
        'minLat': 21.8, 'maxLat': 25.4,
        'minLon': 119.8, 'maxLon': 122.2,
        'mapWidth': 400, 'mapHeight': 560 # 設定台灣圖形的像素大小
    }

    html_content = f"""
    <div id="glow-container">
        </div>

    <style>
        body, html {{ margin: 0; padding: 0; background-color: #010101; overflow: hidden; }}
        
        #glow-container {{
            position: relative;
            width: {projection_config['mapWidth']}px;
            height: {projection_config['mapHeight']}px;
            background-color: #010101; /* 極黑背景 */
            margin: 0 auto; /* 居中 */
            overflow: hidden;
        }}

        /* 台灣輪廓樣式：使用淡淡的色號 #2C4B4B 勾勒 */
        #taiwan-outline {{
            position: absolute; width: 100%; height: 100%;
            fill: none; stroke: #2C4B4B; stroke-width: 1px;
            opacity: 0.6; z-index: 1; /* 地圖輪廓層 */
        }}

        /* 抽象聲紋光暈樣式 */
        .glow-pool {{
            position: absolute;
            border-radius: 50%;
            /* 強力柔焦，徹底消融線條感 */
            filter: blur(20px); 
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.2); /* 中心對齊 */
            
            /* 動態效果：脈動、擴張、淡出，模擬水滴滴入 */
            animation: glow-pulse 6s ease-out forwards;
            z-index: 5; /* 資料點在輪廓層之上 */
        }}

        /* 民眾紀錄：使用您指定的色號 #C4E1FF */
        .type-raw {{
            background: radial-gradient(circle, rgba(196, 225, 255, 0.8) 0%, rgba(196, 225, 255, 0.1) 50%, rgba(196, 225, 255, 0) 80%);
        }}

        /* 專家紀錄：#f1c40f 金色 */
        .type-verified {{
            background: radial-gradient(circle, rgba(241, 196, 15, 0.6) 0%, rgba(241, 196, 15, 0.1) 50%, rgba(241, 196, 15, 0) 80%);
        }}

        @keyframes glow-pulse {{
            0% {{ transform: translate(-50%, -50%) scale(0.2); opacity: 0; filter: blur(25px); }}
            15% {{ transform: translate(-50%, -50%) scale(1); opacity: 1; filter: blur(20px); }} /* 滴入瞬間 */
            60% {{ opacity: 0.4; }}
            100% {{ transform: translate(-50%, -50%) scale(3); opacity: 0; filter: blur(35px); }} /* 緩慢擴散並彻底融合 */
        }}
    </style>

    <script>
        const rawData = {raw_json};
        const verifiedData = {verified_json};
        const config = {json.dumps(projection_config)};
        const container = document.getElementById('glow-container');

        // 在 JS 中手動生成一個簡單的台灣島嶼 SVG 路徑 (已優化投影)
        const outlineSVG = '<svg id="taiwan-outline" viewBox="119.8 21.8 2.4 3.6" preserveAspectRatio="xMidYMid meet"><path d="M121.5,21.9 C121.3,22.2 120.9,22.6 120.6,23.3 C120.3,23.9 120.2,24.7 120.3,25.3 C120.5,25.6 120.8,25.7 121.2,25.7 C121.6,25.7 122.0,25.4 122.1,24.7 C122.2,24.0 122.0,23.2 121.8,22.6 C121.7,22.3 121.6,22.1 121.5,21.9 Z" /></svg>';
        container.innerHTML = outlineSVG;

        // 水滴滴入播放函數
        function playDataSequence(data, className) {{
            // 資料已經按 Create Date 排序，這裡按排序順序依序播放
            data.forEach((row, i) => {{
                // 使用 setTimeout 來精確控制滴入時間
                // 每個點位與上一個點位間隔 200ms
                setTimeout(() => {{
                    const el = document.createElement('div');
                    el.className = 'glow-pool ' + className;
                    
                    // 經緯度投影至百分比坐標，設定資料邊距防止光暈超出
                    const x = ((row.Longitude - config.minLon) / (config.maxLon - config.minLon)) * 90 + 5;
                    const y = 100 - (((row.Latitude - config.minLat) / (maxLat - config.minLat)) * 90 + 5);
                    
                    el.style.top = y + '%';
                    el.style.left = x + '%';
                    
                    // 設定光暈的視覺範圍 (動畫會從 scale(0.2) 開始擴張)
                    el.style.width = '70px';
                    el.style.height = '70px';
                    
                    container.appendChild(el);
                }}, i * 200); // 這是「依照順序滴入」的時序設定
            }});
        }}

        // 啟動資料播放
        playDataSequence(rawData, 'type-raw');
        
        // 為了讓專業點位看起來更有層次，專業點位延遲 5 秒後啟動依序滴入
        setTimeout(() => {{
            playDataSequence(verifiedData, 'type-verified');
        }}, 5000);
    </script>
    """
    return html_content

# --- 4. 在 Streamlit Components 中呈現藝術論述地圖 ---
# 將高度從原本的 620 稍微調大到 680，以呈現完整的投影地圖
st.components.v1.html(create_immersive_glow_map(raw_data, verified_data), height=680, scrolling=False)

# 在底部加入重新播放按鈕與統計資訊
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("""
<div style="font-size: 0.9em; color: #666; font-family: sans-serif;">
統計：民眾紀錄（#C4E1FF）與專家鑑定（#f1c40f）的數據轉譯感官體驗。
</div>
""", unsafe_allow_html=True)

with col2:
    # 加入一個按鈕來重新觸發 JS 動畫
    if st.button('Restart Scene (重新撥放)'):
        st.rerun()
