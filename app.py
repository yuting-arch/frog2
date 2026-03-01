import streamlit as st
import pandas as pd
import json

# --- 1. 頁面設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴聲景：水滴沉浸地圖")

st.markdown("""
    <h1 style='text-align: center; color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>
        💧 台灣蛙鳴：時序水滴沉浸地圖
    </h1>
    <p style='text-align: center; color: #666; font-size: 1em;'>
        每一聲紀錄如雨滴般落下，泛起 #C4E1FF 的漣漪，沒入台灣的夜色中。
    </p>
""", unsafe_allow_html=True)

# --- 2. 資料讀取與時序排序 ---
@st.cache_data
def load_and_process_data():
    def try_read(file_name):
        for enc in ['utf-8', 'big5', 'cp950', 'utf-8-sig']:
            try:
                return pd.read_csv(file_name, encoding=enc)
            except:
                continue
        return pd.read_csv(file_name, encoding='latin1')

    df_raw = try_read('raw_data.csv')
    df_verified = try_read('verified_data.csv')
    
    for df in [df_raw, df_verified]:
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        # 轉為日期格式以便排序
        df['Create Date'] = pd.to_datetime(df['Create Date'], errors='coerce')
    
    # 按時間排序，這決定了「滴入」的順序
    df_raw = df_raw.sort_values('Create Date').dropna(subset=['Latitude', 'Longitude'])
    df_verified = df_verified.sort_values('Create Date').dropna(subset=['Latitude', 'Longitude'])
    
    return df_raw, df_verified

try:
    raw_data, verified_data = load_and_process_data()

    # --- 3. 沉浸式水滴地圖 HTML/JS ---
    def create_water_drop_map(df_r, df_v):
        raw_json = df_r.to_json(orient='records')
        verified_json = df_v.to_json(orient='records')

        html_content = f"""
        <div id="art-container">
            <svg id="taiwan-svg" viewBox="119.3 21.7 3.2 3.8" preserveAspectRatio="xMidYMid meet">
                <path d="M121.5,21.9 C121.2,22.1 120.8,22.5 120.5,23.1 C120.2,23.7 120.1,24.5 120.3,25.1 C120.5,25.4 120.8,25.5 121.2,25.5 C121.6,25.5 122.0,25.2 122.1,24.5 C122.2,23.8 122.0,23.0 121.8,22.4 C121.7,22.1 121.6,21.9 121.5,21.9 Z" 
                      fill="none" stroke="#1A3A3A" stroke-width="0.01" />
            </svg>
            <div id="drop-layer"></div>
        </div>

        <style>
            body, html {{ margin: 0; padding: 0; background-color: #010101; overflow: hidden; }}
            #art-container {{
                position: relative; width: 100%; height: 650px;
                background-color: #010101; display: flex; justify-content: center; align-items: center;
            }}
            #taiwan-svg {{
                position: absolute; width: 450px; height: 600px; opacity: 0.4;
                filter: drop-shadow(0 0 5px #1A3A3A);
            }}
            #drop-layer {{ position: absolute; width: 450px; height: 600px; }}

            /* 核心 6px 水滴點 */
            .drop-point {{
                position: absolute; width: 6px; height: 6px; border-radius: 50%;
                transform: translate(-50%, -50%); opacity: 0;
                animation: drop-in 1s ease-in forwards;
            }}
            /* 藝術漣漪：往外淡化 */
            .ripple {{
                position: absolute; border-radius: 50%; border: 0.5px solid;
                transform: translate(-50%, -50%) scale(0); opacity: 0;
                animation: ripple-out 4s ease-out forwards;
            }}

            .raw-color {{ background-color: #C4E1FF; box-shadow: 0 0 8px #C4E1FF; border-color: #C4E1FF; }}
            .ver-color {{ background-color: #f1c40f; box-shadow: 0 0 8px #f1c40f; border-color: #f1c40f; }}

            @keyframes drop-in {{
                0% {{ transform: translate(-50%, -150%); opacity: 0; }}
                100% {{ transform: translate(-50%, -50%); opacity: 1; }}
            }}
            @keyframes ripple-out {{
                0% {{ transform: translate(-50%, -50%) scale(0.5); opacity: 0.8; }}
                100% {{ transform: translate(-50%, -50%) scale(5); opacity: 0; filter: blur(5px); }}
            }}
        </style>

        <script>
            const rawData = {raw_json};
            const verData = {verified_json};
            const layer = document.getElementById('drop-layer');

            // 投影函數
            function getPos(lat, lon) {{
                const x = ((lon - 119.3) / 3.2) * 450;
                const y = 600 - (((lat - 21.7) / 3.8) * 600);
                return {{x, y}};
            }}

            function playData(data, colorClass) {{
                data.forEach((row, i) => {{
                    setTimeout(() => {{
                        const pos = getPos(row.Latitude, row.Longitude);
                        
                        // 建立水滴核心
                        const dot = document.createElement('div');
                        dot.className = 'drop-point ' + colorClass;
                        dot.style.left = pos.x + 'px'; dot.style.top = pos.y + 'px';
                        layer.appendChild(dot);

                        // 建立擴散漣漪
                        const rip = document.createElement('div');
                        rip.className = 'ripple ' + colorClass;
                        rip.style.left = pos.x + 'px'; rip.style.top = pos.y + 'px';
                        rip.style.width = '20px'; rip.style.height = '20px';
                        layer.appendChild(rip);
                    }}, i * 300); // 每 0.3 秒滴入一筆
                }});
            }}

            playData(rawData, 'raw-color');
            setTimeout(() => playData(verData, 'ver-color'), 2000);
        </script>
        """
        return html_content

    st.components.v1.html(create_water_drop_map(raw_data, verified_data), height=660)

    # 4. 側邊欄
    st.sidebar.title("🌧️ 聲景撥放器")
    st.sidebar.write("資料已根據錄製時間排序。")
    if st.sidebar.button("重新播放動畫"):
        st.rerun()

except Exception as e:
    st.error(f"資料處理出錯：{e}")
