import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import json

# --- 1. 頁面藝術化設定 ---
st.set_page_config(layout="wide", page_title="台灣蛙鳴環境聲景地圖")

st.markdown("""
    <div style="text-align: center; margin-bottom: 10px;">
        <h1 style='color: #C4E1FF; font-weight: 200; letter-spacing: 3px;'>🌿 台灣蛙鳴環境聲景：分離層沉浸地圖</h1>
        <p style='color: #888; font-size: 1.1em;'>底圖與動畫分離：底圖靜止呈現，動畫於上方依時序泛起漣漪。</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. 核心資料讀取與排序 ---
@st.cache_data
def load_and_process_data():
    def try_read(file_name):
        for enc in ['utf-8', 'big5', 'cp950', 'utf-8-sig']:
            try:
                return pd.read_csv(file_name, encoding=enc)
            except:
                continue
        return None

    df_raw = try_read('raw_data.csv')
    df_verified = try_read('verified_data.csv')
    
    def finalize(df):
        if df is not None:
            df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
            df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
            df['Create Date'] = pd.to_datetime(df['Create Date'], errors='coerce')
            return df.dropna(subset=['Latitude', 'Longitude']).sort_values('Create Date')
        return pd.DataFrame()

    return finalize(df_raw), finalize(df_verified)

raw_data, verified_data = load_and_process_data()

# --- 3. 建立畫面 ---
if not raw_data.empty:
    # 建立容器
    container = st.container()
    
    with container:
        # 第一層：底圖層 (Folium)
        # 設定地圖不可拖動與縮放，確保它像「貼紙」一樣固定
        m = folium.Map(
            location=[23.6, 120.8], 
            zoom_start=7.5, 
            tiles="cartodbdarkmatter",
            zoom_control=False,
            scrollWheelZoom=False,
            dragging=False
        )
        
        # 準備動畫數據
        raw_list = raw_data[['Latitude', 'Longitude']].to_dict(orient='records')
        
        # 第二層：透明動畫層 (HTML/JS)
        # 我們計算台灣經緯度到網頁像素的投影
        animation_html = f"""
        <div id="animation-overlay"></div>
        <style>
            #animation-overlay {{
                position: absolute;
                top: 0; left: 0;
                width: 100%; height: 650px;
                pointer-events: none; /* 讓滑鼠可以穿透 */
                z-index: 999;
                overflow: hidden;
            }}
            @keyframes ripple-effect {{
                0% {{ transform: translate(-50%, -50%) scale(0.2); opacity: 0; }}
                20% {{ opacity: 0.8; }}
                100% {{ transform: translate(-50%, -50%) scale(4); opacity: 0; filter: blur(4px); }}
            }}
            .ripple {{
                position: absolute;
                width: 15px; height: 15px;
                border: 1px solid #C4E1FF;
                border-radius: 50%;
                animation: ripple-effect 4s ease-out forwards;
            }}
            .dot {{
                position: absolute;
                width: 6px; height: 6px;
                background-color: #C4E1FF;
                border-radius: 50%;
                box-shadow: 0 0 8px #C4E1FF;
                transform: translate(-50%, -50%);
            }}
        </style>
        <script>
            const data = {json.dumps(raw_list)};
            const overlay = document.getElementById('animation-overlay');
            
            // 台灣座標投影函數 (針對 Folium zoom 7.5 的位置微調)
            function project(lat, lon) {{
                const mapWidth = 1100;
                const mapHeight = 650;
                const minLon = 118.5, maxLon = 123.0;
                const minLat = 21.5, maxLat = 25.8;
                
                const x = ((lon - minLon) / (maxLon - minLon)) * mapWidth;
                const y = mapHeight - (((lat - minLat) / (maxLat - minLat)) * mapHeight);
                return {{x, y}};
            }}

            data.forEach((p, i) => {{
                setTimeout(() => {{
                    const pos = project(p.Latitude, p.Longitude);
                    
                    // 畫核心點
                    const dot = document.createElement('div');
                    dot.className = 'dot';
                    dot.style.left = pos.x + 'px';
                    dot.style.top = pos.y + 'px';
                    overlay.appendChild(dot);

                    // 畫漣漪
                    const ripple = document.createElement('div');
                    ripple.className = 'ripple';
                    ripple.style.left = pos.x + 'px';
                    ripple.style.top = pos.y + 'px';
                    overlay.appendChild(ripple);
                }}, i * 400); // 依序滴入
            }});
        </script>
        """

        # 先放地圖，再疊加動畫
        folium_static(m, width=1100, height=650)
        st.components.v1.html(animation_html, height=650)

    st.sidebar.info(f"當前模式：分離層時序動畫")
    st.sidebar.write(f"底圖已固定，動畫正在依序呈現...")
    if st.sidebar.button("🔄 重新播放"):
        st.rerun()
else:
    st.warning("請檢查 CSV 資料內容。")
