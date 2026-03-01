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

    try:
        df_raw = try_read('raw_data.csv')
        df_verified = try_read('verified_data.csv')
        
        for df in [df_raw, df_verified]:
            df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
            df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
            df['Create Date'] = pd.to_datetime(df['Create Date'], errors='coerce')
        
        # 按時間排序
        df_raw = df_raw.sort_values('Create Date').dropna(subset=['Latitude', 'Longitude'])
        df_verified = df_verified.sort_values('Create Date').dropna(subset=['Latitude', 'Longitude'])
        
        return df_raw, df_verified
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

try:
    raw_data, verified_data = load_and_process_data()

    # --- 3. 沉浸式水滴地圖 HTML/JS ---
    def create_water_drop_map(df_r, df_v):
        raw_json = df_r.to_json(orient='records')
        verified_json = df_v.to_json(orient='records')

        # 這裡使用了更完整的台灣地圖 SVG 路徑與地理投影設定
        html_content = f"""
        <div id="art-container">
            <svg id="taiwan-svg" viewBox="119.5 21.5 3.0 4.0" preserveAspectRatio="xMidYMid meet">
                <path d="M121.5,21.8C121.4,21.8,121.3,21.9,121.2,21.9C121.1,22,121,22.1,120.9,22.2C120.7,22.5,120.5,22.8,120.4,23.1C120.2,23.5,120.1,23.9,120.1,24.3C120.1,24.7,120.2,25.1,120.4,25.4C120.6,25.6,121,25.7,121.3,25.7C121.7,25.7,122.1,25.5,122.2,25.1C122.4,24.7,122.4,24.3,122.3,23.8C122.2,23.2,122,22.6,121.7,22.1C121.6,21.9,121.5,21.8,121.5,21.8Z" 
                      fill="none" stroke="#2D4F4F" stroke-width="0.015" />
                <path d="M120.2,25.2 L120.4,25.5 L120.8,25.7 L121.5,25.7 L122.1,25.4 L122.4,24.8 L122.5,24.1 L122.3,23.2 L121.8,22.1 L121.4,21.7" 
                      fill="none" stroke="#1A3A3A" stroke-width="0.008" stroke-dasharray="0.02, 0.02" />
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
                position: absolute; width: 450px; height: 600px; opacity: 0.6;
                filter: drop-shadow(0 0 8px #1A3A3A);
            }}
            #drop-layer {{ 
                position: absolute; width: 450px; height: 600px; 
                /* 確保 drop-layer 與 SVG 的座標範圍對齊 */
            }}

            .drop-point {{
                position: absolute; width: 6px; height: 6px; border-radius: 50%;
                transform: translate(-50%, -50%); opacity: 0;
                animation: drop-in 0.8s cubic-bezier(0.24, 0, 0.64, 1) forwards;
            }}

            .ripple {{
                position: absolute; border-radius: 50%; border: 0.8px solid;
                transform: translate(-50%, -50%) scale(0); opacity: 0;
                animation: ripple-out 4s ease-out forwards;
            }}

            .raw-color {{ background-color: #C4E1FF; box-shadow: 0 0 10px #C4E1FF; border-color: #C4E1FF; }}
            .ver-color {{ background-color: #f1c40f; box-shadow: 0 0 10px #f1c40f; border-color: #f1c40f; }}

            @keyframes drop-in {{
                0% {{ transform: translate(-50%, -200px); opacity: 0; }}
                80% {{ opacity: 1; }}
                100% {{ transform: translate(-50%, -50%); opacity: 1; }}
            }}
            @keyframes ripple-out {{
                0% {{ transform: translate(-50%, -50%) scale(0.2); opacity: 0.8; }}
                100% {{ transform: translate(-50%, -50%) scale(5); opacity: 0; filter: blur(6px); }}
            }}
        </style>

        <script>
            const rawData = {raw_json};
            const verData = {verified_json};
            const layer = document.getElementById('drop-layer');

            // 投影函數：根據 SVG 的 viewBox (119.5 21.5 3.0 4.0) 計算像素位置
            function getPos(lat, lon) {{
                const x = ((lon - 119.5) / 3.0) * 450;
                const y = 600 - (((lat - 21.5) / 4.0) * 600);
                return {{x, y}};
            }}

            function playData(data, colorClass, baseDelay) {{
                data.forEach((row, i) => {{
                    setTimeout(() => {{
                        const pos = getPos(row.Latitude, row.Longitude);
                        
                        const dot = document.createElement('div');
                        dot.className = 'drop-point ' + colorClass;
                        dot.style.left = pos.x + 'px'; dot.style.top = pos.y + 'px';
                        layer.appendChild(dot);

                        const rip = document.createElement('div');
                        rip.className = 'ripple ' + colorClass;
                        rip.style.left = pos.x + 'px'; rip.style.top = pos.y + 'px';
                        rip.style.width = '15px'; rip.style.height = '15px';
                        layer.appendChild(rip);
                    }}, baseDelay + (i * 350)); 
                }});
            }}

            playData(rawData, 'raw-color', 500);
            playData(verData, 'ver-color', 3000); // 專家資料稍後滴入
        </script>
        """
        return html_content

    if not raw_data.empty or not verified_data.empty:
        st.components.v1.html(create_water_drop_map(raw_data, verified_data), height=660)
    else:
        st.warning("等待資料載入中，請確保根目錄有 raw_data.csv")

    # 4. 側邊欄
    st.sidebar.title("🌧️ 聲景撥放器")
    st.sidebar.markdown(f"**民眾紀錄：** {len(raw_data)} 筆")
    st.sidebar.markdown(f"**專家驗證：** {len(verified_data)} 筆")
    st.sidebar.write("---")
    if st.sidebar.button("重新播放水滴動畫"):
        st.rerun()

except Exception as e:
    st.error(f"地圖啟動失敗：{e}")
