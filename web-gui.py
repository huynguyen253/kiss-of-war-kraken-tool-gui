import streamlit as st
import random
import itertools
import statistics
import math
import pandas as pd # Thư viện xử lý bảng cực mạnh cho web

# ==========================================
# 1. CORE LOGIC (GIỮ NGUYÊN)
# ==========================================

parts_hp = {
    "Head":       60000,
    "Shoulder 1": 30000,
    "Shoulder 2": 30000,
    "Leg 1":      40000,
    "Leg 2":      40000
}

def simulate_battle(attack_order, rewards_map, hp_map, base_dmg, base_crit):
    crit_rate = base_crit / 100.0
    crit_dmg_bonus = 1.00
    dmg_bonus_pct = 0.0
    total_hits = 0

    for part_name in attack_order:
        current_hp = hp_map[part_name]
        while current_hp > 0:
            total_hits += 1
            is_crit = random.random() < crit_rate
            hit_dmg = base_dmg * (1 + dmg_bonus_pct)
            
            if is_crit:
                multiplier = 1 + crit_dmg_bonus
                hit_dmg *= multiplier
            current_hp -= hit_dmg
        
        reward = rewards_map[part_name]
        if reward == "DMG": dmg_bonus_pct += 0.10
        elif reward == "CRIT_DMG": crit_dmg_bonus += 0.50
        elif reward == "CRIT_RATE": crit_rate += 0.20

    return total_hits

def get_percentile(data, percentile):
    size = len(data)
    if size == 0: return 0
    return sorted(data)[int(math.ceil((size * percentile) / 100)) - 1]

# ==========================================
# 2. WEB INTERFACE (STREAMLIT)
# ==========================================

st.set_page_config(page_title="Kraken Optimizer", layout="wide")

st.title("🦑 Mechanical Kraken Strategy Optimizer")
st.markdown("Công cụ tối ưu hóa chiến thuật tiêu diệt Kraken - Kiss of War")

# --- SIDEBAR: CẤU HÌNH ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("1. Player Stats")
    user_dmg = st.number_input("Base Damage", value=2600, step=100)
    user_crit = st.number_input("Base Crit Rate (%)", value=20.0, step=1.0)
    
    st.subheader("2. Your Ammo")
    ammo_limit = st.number_input("Ammo Limit", value=60, step=1)
    
    st.subheader("3. Options")
    top_n = st.slider("Show Top Results", 1, 50, 10)
    sim_count = st.select_slider("Simulation Precision", options=[500, 1000, 2000, 5000], value=1000)

# --- MAIN SCREEN: NHẬP REWARDS ---
st.header("🔍 Step 1: Input Part Rewards")
col1, col2, col3, col4, col5 = st.columns(5)

reward_options = ["DMG (+10%)", "CRIT_DMG (+50%)", "CRIT_RATE (+20%)"]
# Mapping lại cho đúng logic code
code_map = {"DMG (+10%)": "DMG", "CRIT_DMG (+50%)": "CRIT_DMG", "CRIT_RATE (+20%)": "CRIT_RATE"}

with col1:
    r_head = st.selectbox("Head", reward_options, index=1)
with col2:
    r_sh1 = st.selectbox("Shoulder 1", reward_options, index=0)
with col3:
    r_sh2 = st.selectbox("Shoulder 2", reward_options, index=2)
with col4:
    r_leg1 = st.selectbox("Leg 1", reward_options, index=0)
with col5:
    r_leg2 = st.selectbox("Leg 2", reward_options, index=1)

# Tạo map phần thưởng
rewards_map = {
    "Head": code_map[r_head],
    "Shoulder 1": code_map[r_sh1],
    "Shoulder 2": code_map[r_sh2],
    "Leg 1": code_map[r_leg1],
    "Leg 2": code_map[r_leg2]
}

# --- NÚT CHẠY ---
if st.button("🚀 RUN ANALYSIS (Start Simulation)", type="primary"):
    
    # Hiển thị thanh tiến trình
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    part_names = list(rewards_map.keys())
    all_orders = list(itertools.permutations(part_names))
    total_scenarios = len(all_orders)
    
    analyzed_results = []
    
    status_text.text("Simulating battles... Please wait.")
    
    # Chạy mô phỏng
    for i, order in enumerate(all_orders):
        results_history = []
        for _ in range(sim_count):
            hits = simulate_battle(order, rewards_map, parts_hp, user_dmg, user_crit)
            results_history.append(hits)
            
        avg_hits = statistics.mean(results_history)
        median_hits = statistics.median(results_history)
        stdev_hits = statistics.stdev(results_history)
        worst_case_95 = get_percentile(results_history, 95)
        wins = sum(1 for h in results_history if h <= ammo_limit)
        win_rate = (wins / sim_count) * 100
        
        # Format lại tên chiến thuật cho đẹp (viết tắt)
        short_order = [p.replace("Shoulder", "Sh").replace("Head", "Hd").replace("Leg", "Lg") for p in order]
        order_str = " ➜ ".join(short_order)
        
        analyzed_results.append({
            "Strategy Path": order_str,
            "Median Hits": median_hits,
            "Avg Hits": round(avg_hits, 2),
            "Risk (Std)": round(stdev_hits, 2),
            "Worst 5%": worst_case_95,
            "Win Rate (%)": round(win_rate, 1)
        })
        
        # Cập nhật thanh tiến trình
        progress_bar.progress((i + 1) / total_scenarios)

    # Sắp xếp kết quả
    analyzed_results.sort(key=lambda x: (-x["Win Rate (%)"], x["Median Hits"], x["Avg Hits"]))
    
    # Cắt lấy Top N
    final_df = pd.DataFrame(analyzed_results[:top_n])
    
    # Làm đẹp bảng kết quả
    st.success("Analysis Complete!")
    status_text.empty()
    progress_bar.empty()
    
    st.subheader(f"🏆 Top {top_n} Best Strategies")
    
    # Highlight Win Rate cao nhất
    st.dataframe(
        final_df.style.background_gradient(subset=["Win Rate (%)"], cmap="Greens").format({"Win Rate (%)": "{:.1f}%"}),
        use_container_width=True,
        height=500
    )

    st.info("""
    **Guide:**
    * **Median Hits:** Kỳ vọng thực tế nhất (50% cơ hội).
    * **Win Rate:** Tỷ lệ thắng với số đạn bạn nhập bên trái.
    * **Risk:** Chỉ số càng thấp càng ổn định (ít may rủi).
    """)