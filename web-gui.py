import streamlit as st
import random
import itertools
import statistics
import math
import pandas as pd

# ==========================================
# 1. CORE LOGIC
# ==========================================

def simulate_battle(attack_order, rewards_map, hp_map, base_dmg, base_crit):
    # Convert input stats to logic stats
    crit_rate = base_crit / 100.0
    crit_dmg_bonus = 1.00 # Base Crit Dmg is +100% (x2 Total)
    dmg_bonus_pct = 0.0
    total_hits = 0

    # Create a local copy of HP map to avoid modifying the original during simulation loops
    current_hp_map = hp_map.copy()

    for part_name in attack_order:
        current_hp = current_hp_map[part_name]
        
        while current_hp > 0:
            total_hits += 1
            is_crit = random.random() < crit_rate
            hit_dmg = base_dmg * (1 + dmg_bonus_pct)
            
            if is_crit:
                multiplier = 1 + crit_dmg_bonus
                hit_dmg *= multiplier
            current_hp -= hit_dmg
        
        # Apply Reward after destroying part
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
# 2. WEB INTERFACE CONFIG
# ==========================================

st.set_page_config(page_title="Kraken Optimizer", layout="wide", page_icon="🦑")

st.title("🦑 Mechanical Kraken Strategy Optimizer")
st.markdown("Calculate the most efficient attack order based on part rewards and your stats.")

# ==========================================
# 3. SIDEBAR: SETTINGS & INPUTS
# ==========================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # --- GROUP 1: PLAYER STATS ---
    with st.expander("1. Player Stats", expanded=True):
        user_dmg = st.number_input("Base Damage (per hit)", value=2600, step=100)
        user_crit = st.number_input("Base Crit Rate (%)", value=20.0, step=1.0)
    
    # --- GROUP 2: AMMO LIMIT ---
    with st.expander("2. Ammo Budget", expanded=True):
        ammo_limit = st.number_input("Your Ammo Limit", value=60, step=1, help="Used to calculate Win Rate %")
        win_rate_label = f"Win Rate (w/ {ammo_limit} Ammo)" # Dynamic Label

    # --- GROUP 3: ENEMY HP (EDITABLE) ---
    with st.expander("3. Enemy HP Config", expanded=True):
        st.caption("Edit these values if the boss HP changes.")
        hp_head = st.number_input("Head HP", value=60000, step=1000)
        hp_sh1  = st.number_input("Shoulder 1 HP", value=30000, step=1000)
        hp_sh2  = st.number_input("Shoulder 2 HP", value=30000, step=1000)
        hp_leg1 = st.number_input("Leg 1 HP", value=40000, step=1000)
        hp_leg2 = st.number_input("Leg 2 HP", value=40000, step=1000)

        # Pack into dictionary
        parts_hp = {
            "Head":       hp_head,
            "Shoulder 1": hp_sh1,
            "Shoulder 2": hp_sh2,
            "Leg 1":      hp_leg1,
            "Leg 2":      hp_leg2
        }

    # --- GROUP 4: SIMULATION SETTINGS ---
    with st.expander("4. Advanced Options", expanded=False):
        top_n = st.slider("Show Top Results", 1, 50, 15)
        sim_count = st.select_slider("Simulation Precision (Runs per Strategy)", options=[500, 1000, 2000, 5000], value=1000)

# ==========================================
# 4. MAIN SCREEN: REWARD SELECTION
# ==========================================

st.subheader("🔍 Step 1: Input Part Rewards")
st.caption("Select the buff visible on each part of the Kraken.")

col1, col2, col3, col4, col5 = st.columns(5)

reward_display = ["DMG (+10%)", "CRIT_DMG (+50%)", "CRIT_RATE (+20%)"]
code_map = {"DMG (+10%)": "DMG", "CRIT_DMG (+50%)": "CRIT_DMG", "CRIT_RATE (+20%)": "CRIT_RATE"}

with col1:
    r_head = st.selectbox("Head", reward_display, index=1)
with col2:
    r_sh1 = st.selectbox("Shoulder 1", reward_display, index=0)
with col3:
    r_sh2 = st.selectbox("Shoulder 2", reward_display, index=2)
with col4:
    r_leg1 = st.selectbox("Leg 1", reward_display, index=0)
with col5:
    r_leg2 = st.selectbox("Leg 2", reward_display, index=1)

rewards_map = {
    "Head": code_map[r_head],
    "Shoulder 1": code_map[r_sh1],
    "Shoulder 2": code_map[r_sh2],
    "Leg 1": code_map[r_leg1],
    "Leg 2": code_map[r_leg2]
}

# ==========================================
# 5. EXECUTION & RESULTS
# ==========================================

st.divider()

if st.button("🚀 ANALYZE STRATEGIES", type="primary", use_container_width=True):
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    part_names = list(rewards_map.keys())
    all_orders = list(itertools.permutations(part_names))
    total_scenarios = len(all_orders)
    
    analyzed_results = []
    
    status_text.text(f"Simulating {total_scenarios} scenarios x {sim_count} runs... Please wait.")
    
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
        
        # Abbreviate names for cleaner table
        short_order = [p.replace("Shoulder", "Sh").replace("Head", "Hd").replace("Leg", "Lg") for p in order]
        order_str = " ➜ ".join(short_order)
        
        analyzed_results.append({
            "Strategy Path": order_str,
            "Median Hits": median_hits,
            "Avg Hits": round(avg_hits, 2),
            "Risk (Std)": round(stdev_hits, 2),
            "Worst Case (95%)": worst_case_95,
            win_rate_label: round(win_rate, 1) # Dynamic column name
        })
        
        # Update progress
        if i % 10 == 0:
            progress_bar.progress((i + 1) / total_scenarios)

    progress_bar.progress(100)
    status_text.empty()
    
    # SORTING: Primary = Win Rate (Desc), Secondary = Median (Asc)
    analyzed_results.sort(key=lambda x: (-x[win_rate_label], x["Median Hits"], x["Avg Hits"]))
    
    # Create DataFrame
    final_df = pd.DataFrame(analyzed_results[:top_n])
    
    # --- DISPLAY RESULTS ---
    st.success("Analysis Complete! Best strategies are listed below.")
    
    st.subheader(f"🏆 Top {top_n} Optimal Strategies")
    
    # Display Dataframe with Gradient on Win Rate
    st.dataframe(
        final_df.style.background_gradient(subset=[win_rate_label], cmap="Greens")
                 .format({win_rate_label: "{:.1f}%", "Avg Hits": "{:.2f}", "Risk (Std)": "{:.2f}"}),
        use_container_width=True,
        height=600
    )

    # --- METRIC GUIDE ---
    st.info(f"""
    **📊 Metrics Guide:**
    * **{win_rate_label}:** The probability of completing the stage within your budget of **{ammo_limit}** hits. (Higher is better).
    * **Median Hits:** Realistic expectation. 50% of attempts will be this number or lower.
    * **Worst Case (95%):** The "Safety Cap". You are 95% likely to finish within this number of hits.
    * **Risk (Std):** Lower number means the strategy is more consistent/predictable.
    """)
