import streamlit as st
import pandas as pd
import json

# --- 1. 頁面與藝術論述設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴聲景：沉浸式光暈地圖")

st.markdown("""
    <h1 style='text-align: center; color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>
        🌿 台灣蛙鳴環境聲景：抽象光暈地圖
    </h1>
    <p style='text-align: center; color: #888; font-size: 1.1em; font-family: sans-serif;'>
        這不是一張導航地圖，而是一個生態感官場域。<br>
        每一聲紀錄都是夜色中浮現的柔和光暈，沒有冰冷的邊緣，只有能量的交會。
    </p>
""", unsafe_allow_html=True)

# --- 2. 核心資料讀取函數 (對接你的真實 CSV) ---
@st.cache_data
def load_data():
    def try_read(file_name):
        for enc in ['utf-8', 'big5', 'cp950', 'utf-8-sig']:
            try:
                return pd.read_csv(file_name, encoding=enc)
            except:
                continue
        return pd.read_csv(file_name, encoding='latin1')

    df_raw = try_read('raw_data.csv')
    df_verified = try_read('verified_data.csv')
    
    # 數值清洗
    for df in [df_raw, df_verified]:
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    return df_raw.dropna(subset=['Latitude', 'Longitude']), \
           df_verified.dropna(subset=['Latitude', 'Longitude'])

try:
    raw_data, verified_data = load_data()

    # --- 3. 生成沉浸式 HTML/JS 藝術地圖 ---
    def create_immersive_map(df_r, df_v):
        # 準備資料給 JS
        raw_json = df_r[['Latitude', 'Longitude', 'Username']].to_json(orient='records')
        verified_json = df_v[['Latitude', 'Longitude', 'Review Identity']].to_json(orient='records')

        html_content = f"""
        <div id="glow-container"></div>

        <style>
            body, html {{ margin: 0; padding: 0; background-color: #010101; overflow: hidden; }}
            
            #glow-container {{
                position: relative;
                width: 100%;
                height: 600px;
                background-color: #010101; /* 極黑背景 */
                border-radius: 15px;
                overflow: hidden;
            }}

            /* 抽象聲紋光暈樣式 */
            .glow-pool {{
                position: absolute;
                border-radius: 50%;
                filter: blur(18px); /* 強力柔焦，消融線條 */
                opacity: 0;
                transform: translate(-50%, -50%) scale(0);
                animation: glow-pulse 7s ease-out forwards;
            }}

            /* 民眾紀錄：#C4E1FF 螢光藍 */
            .type-raw {{
                background: radial-gradient(circle, rgba(196, 225, 255, 0.7) 0%, rgba(196, 225, 255, 0.1) 50%, rgba(196, 225, 255, 0) 80%);
            }}

            /* 專家紀錄：#f1c40f 霓虹金 */
            .type-verified {{
                background: radial-gradient(circle, rgba(241, 196, 15, 0.6) 0%, rgba(241, 196, 15, 0.1) 50%, rgba(241, 196, 15, 0) 80%);
            }}

            @keyframes glow-pulse {{
                0% {{ transform: translate(-50%, -50%) scale(0.2); opacity: 0; }}
                20% {{ transform: translate(-50%, -50%) scale(1); opacity: 0.9; }}
                60% {{ opacity: 0.4; }}
                100% {{ transform: translate(-50%, -50%) scale(4); opacity: 0; }}
            }}
        </style>

        <script>
            const rawData = {raw_json};
            const verifiedData = {verified_json};
            const container = document.getElementById('glow-container');

            // 台灣經緯度簡單投影 (約略範圍)
            const minLat = 21.8, maxLat = 25.4;
            const minLon = 119.8, maxLon = 122.2;

            function createGlow(data, className) {{
                data.forEach((row, i) => {{
                    const el = document.createElement('div');
                    el.className = 'glow-pool ' + className;
                    
                    // 投影至百分比坐標
                    const top = 100 - (((row.Latitude - minLat) / (maxLat - minLat)) * 100);
                    const left = ((row.Longitude - minLon) / (maxLon - minLon)) * 100;
                    
                    el.style.top = top + '%';
                    el.style.left = left + '%';
                    
                    // 隨機延遲，模擬自然發生的序列感
                    el.style.animationDelay = (Math.random() * 10) + 's';
                    el.style.width = '60px';
                    el.style.height = '60px';
                    
                    container.appendChild(el);
                }});
            }}

            createGlow(rawData, 'type-raw');
            createGlow(verifiedData, 'type-verified');
        </script>
        """
        return html_content

    # 顯示地圖
    st.components.v1.html(create_immersive_map(raw_data, verified_data), height=620)

    # --- 4. 側邊欄統計與論述 ---
    st.sidebar.title("📊 數據轉譯統計")
    st.sidebar.metric("活躍聲紋 (民眾紀錄)", len(raw_data))
    st.sidebar.metric("穩定光場 (專家紀錄)", len(verified_data))
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("✨ 藝術化設計觀點"):
        st.write("""
            本網頁深受 **Ars Electronica** 啟發，將環境數據轉化為感官體驗：
            - **消融邊界**：使用高斯模糊 (Blur) 技術，讓數據不再是「點」，而是「場」。
            - **交會融合**：當兩個光暈重疊，代表不同物種在棲地中的共鳴。
            - **動態衰減**：模擬聲音在空氣中傳播、擴散、最後歸於寂靜的物理過程。
        """)

except Exception as e:
    st.error(f"地圖渲染失敗：{e}")
    st.info("請確認 GitHub 上的 CSV 檔案包含正確的 Latitude 與 Longitude 欄位。")
