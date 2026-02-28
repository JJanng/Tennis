import streamlit as st
import re
import pandas as pd

# 1. [데이터] 기본 회원 명단 (유명 선수 포함)
DEFAULT_MEMBERS = (
"강수정,강정이,강현석,고경주,고성종,김기호,김길우,김동규,김민균,김민재,김민철,김민한,김보배,김상훈,김서영,김시우,김연중,김용석,김이섭,김재승, "
"김재형,김주수,김주연,김지은,김지훈,김진석,김진환,김창현,김태연,김태완,김혜진,박병규,박상배,박성진,박소혜,박영순,박종진,백영훈,송미희,안경화, "
"오영식,오은경,오창호,이도현,이례아,이상덕,이상우,이수아,이유석,이준,이채임,이풍영,임장영,전정민,정대성,정영철,정주석,조진훈,최민숙,최영주, "
"최원영,최은선,최은애,최재영,최학철,최헌영,한주현,한희진,홍상혁"
)

# 2. 대진표 데이터베이스 (AA, AB, TEAM 통합)
HANUL_AA_DATA = {
    5: ["12:34", "13:25", "14:35", "15:24", "23:45"],
    6: ["12:34", "15:46", "23:56", "14:25", "24:36", "16:35"],
    7: ["12:34", "56:17", "35:24", "14:67", "23:57", "16:25", "46:37"],
    8: ["12:34", "56:78", "13:57", "24:68", "37:48", "15:26", "16:38", "25:47"],
    9: ["12:34", "56:78", "19:57", "23:68", "49:38", "15:26", "17:89", "36:45", "24:79"],
    10: ["12:34", "56:78", "23:6A", "19:58", "3A:45", "27:89", "4A:68", "13:79", "46:59", "17:2A"],
    11: ["12:34", "56:78", "1B:9A", "23:68", "4A:57", "26:9B", "13:5B", "49:8A", "17:28", "5A:6B", "39:47"],
    12: ["12:34", "56:78", "9A:BC", "37:48", "29:5A", "1B:6C", "13:57", "24:9B", "68:AC", "17:2B", "35:6A", "49:8C"],
    13: ["12:34", "56:78", "9A:BC", "1D:25", "37:4A", "68:9B", "CD:13", "26:5A", "47:8B", "9C:2D", "15:AB", "3C:67", "48:9D"],
    14: ["12:34", "56:78", "9A:BC", "DE:FG", "13:57", "24:9B", "68:AC", "DF:EG", "15:9C", "2D:3A", "4G:6E", "1F:7B", "8D:BC", "2G:45"],
    15: ["12:34", "56:78", "9A:BC", "DE:FG", "1H:23", "45:67", "89:AB", "CD:EF", "GH:12", "34:56", "78:9A", "BC:DE", "FG:1H", "23:45", "67:89"],
    16: ["12:34", "56:78", "9A:BC", "DE:FG", "13:57", "24:68", "9B:AD", "CE:FH", "15:26", "37:48", "9C:AF", "BD:EG", "1G:2H", "3D:4C", "5B:6A", "7F:8E"]
}

HANUL_AB_DATA = {
    8: ["1A:2B", "3C:4D", "1B:3D", "2A:4C", "1C:4B", "2D:3A", "1D:4A", "3B:2C"],
    10: ["1A:2B", "3C:4D", "5E:1B", "2A:3D", "4C:5B", "1E:3A", "2D:4B", "3E:5C", "1D:4E", "2C:5A"],
    12: ["1A:2B", "3C:4D", "5E:6F", "1B:3D", "2A:5F", "4C:6E", "1C:5A", "3F:6B", "2D:4E", "3B:5C", "1D:4F", "2E:6A"],
    14: ["1A:2B", "3C:4D", "5E:6F", "7G:1B", "2A:3D", "4C:5F", "6E:7A", "1G:5C", "2D:4F", "3G:6B", "7E:2C", "1F:4A", "5G:3E", "6D:7B"],
    16: ["1A:2B", "3C:4D", "5E:6F", "7G:8H", "1B:3D", "2A:5F", "4C:7H", "6E:8G", "1C:5A", "3F:7B", "2D:6H", "4B:8E", "1E:7A", "3G:5B", "2H:4F", "6D:8C"]
}

HANUL_TEAM_DATA = {
    5: ["1:2", "3:4", "1:3", "2:5", "1:4", "3:5", "1:5", "2:4", "2:3", "4:5"],
    6: ["1:2", "3:4", "1:5", "4:6", "2:3", "5:6", "1:4", "2:5", "2:4", "3:6", "1:6", "3:5"],
    7: ["1:2", "3:4", "5:6", "1:7", "3:5", "2:4", "1:4", "6:7", "2:3", "5:7", "1:6", "2:5", "4:6", "3:7"],
    8: ["1:2", "3:4", "5:6", "7:8", "1:3", "5:7", "2:4", "6:8", "1:5", "2:6", "3:7", "4:8", "1:6", "3:8", "2:5", "4:7"],
    9: ["1:2", "3:4", "5:6", "7:8", "1:9", "5:7", "2:3", "6:8", "4:9", "3:8", "1:5", "2:6", "7:9", "2:4", "3:6", "4:5", "1:7", "8:9"],
    10: ["1:2", "3:4", "5:6", "7:8", "2:3", "6:A", "1:9", "5:8", "3:A", "4:5", "2:7", "8:9", "4:A", "6:8", "1:3", "7:9", "4:6", "5:9", "1:7", "2:A"],
    11: ["1:2", "3:4", "5:6", "7:8", "1:B", "9:A", "2:3", "6:8", "4:A", "5:7", "2:6", "9:B", "1:3", "5:B", "4:9", "8:A", "1:7", "2:8", "5:A", "6:B", "3:9", "4:7"],
    12: ["1:2", "3:4", "5:6", "7:8", "9:A", "B:C", "1:3", "5:7", "2:4", "6:8", "9:B", "1:5", "A:C", "2:3", "4:8", "7:B", "6:A", "1:9", "2:C", "5:B", "3:6", "8:A", "9:C", "4:7"],
    13: ["1:2", "3:4", "5:6", "7:8", "9:A", "B:C", "1:D", "2:3", "4:5", "6:7", "8:9", "A:B", "C:D", "1:7", "2:8", "3:9", "4:A", "5:B", "6:C", "D:2", "1:4", "3:5", "6:8", "7:9", "A:C", "B:D"]
}

# --- 로직 함수들 ---
def optimize_schedule(schedule, p_count, mode):
    if p_count in [9, 10, 11, 12] and "AA" in mode: return schedule
    if not schedule: return []
    optimized = []; remaining = list(schedule)
    all_keys = [str(i+1) if i < 9 else chr(65 + (i-9)) for i in range(p_count)]
    stats = {k: {"play": 0, "rest": 0} for k in all_keys}
    while remaining:
        best_match_idx = 0; max_priority_score = -999999
        for i, match_str in enumerate(remaining):
            current_players = set(re.findall(r'[1-9A-H]', match_str))
            priority_score = sum((stats[p]["rest"] ** 2) for p in current_players)
            if any(stats[p]["play"] >= 2 for p in current_players): priority_score -= 1000
            if priority_score > max_priority_score: max_priority_score = priority_score; best_match_idx = i
        match = remaining.pop(best_match_idx); current_players = set(re.findall(r'[1-9A-H]', match))
        optimized.append(match)
        for k in all_keys:
            if k in current_players: stats[k]["play"] += 1; stats[k]["rest"] = 0
            else: stats[k]["play"] = 0; stats[k]["rest"] += 1
    return optimized

# --- 로직 함수들 ---
def get_match_players(schedule_str, player_list, mode):
    mapping = {}; alphabet = "ABCDEFGH"
    if "AB" in mode:
        half = len(player_list) // 2
        for i in range(half): mapping[str(i+1)] = player_list[i]; mapping[alphabet[i]] = player_list[half + i]
    else:
        for i, name in enumerate(player_list):
            if i < 9: mapping[str(i+1)] = name
            else: mapping[alphabet[i-9]] = name
    parts = schedule_str.replace(" ", "").split(":")
    return [mapping.get(k, k) for k in list(parts[0])], [mapping.get(k, k) for k in list(parts[1])]

st.set_page_config(page_title="서울산 테니스클럽", layout="wide")

st.markdown("""
    <style>
    /* 1. 테이블 중앙 정렬 및 ● 기호 가시성 극대화 */
    .stTable td, .stTable th { 
        text-align: center !important; 
        vertical-align: middle !important; 
        font-size: 17px !important; 
        color: #000000 !important; 
    }
    .stTable td { font-weight: 700 !important; line-height: 1.2 !important; }

    /* 2. 좌측 사이드바 설정 (글자 크기 및 너비) */
    section[data-testid="stSidebar"] { width: 350px !important; }
    section[data-testid="stSidebar"] .stText, 
    section[data-testid="stSidebar"] .stMarkdown p { font-size: 16px !important; line-height: 1.5; }
    section[data-testid="stSidebar"] h2, h3 { font-size: 20px !important; font-weight: bold; }
    section[data-testid="stSidebar"] label p { font-size: 15px !important; font-weight: 600; }

    /* 3. 선택된 선수 이름 태그 (파란색) */
    span[data-baseweb="tag"] {
        background-color: #1E88E5 !important; 
        color: white !important; 
        border-radius: 5px !important;
        font-weight: 700 !important;
    }
    span[data-baseweb="tag"] svg { fill: white !important; }

    /* 4. 그룹(익스팬더) 카드 디자인 - 구분력 강화 */
    .streamlit-expanderHeader {
        border: 2px solid #D1D5DB !important;
        border-radius: 12px 12px 0 0 !important;
        background-color: #F3F4F6 !important;
        padding: 12px 18px !important;
    }
    .streamlit-expanderHeader p { font-size: 18px !important; font-weight: 800 !important; color: #111827 !important; }
    .streamlit-expanderContent { 
        background-color: #FFFFFF !important; 
        border: 6px solid #E5E7EB !important; 
        border-top: none !important; 
        border-radius: 0 0 18px 18px !important; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important; 
        margin-bottom: 50px !important; 
        padding: 25px !important;
    }

    /* 5. 설정 열(왼쪽 카드) 디자인 보강 및 폭 최소화 여백 조정 */
    [data-testid="column"]:nth-of-type(1) [data-testid="stVerticalBlock"] { 
        background-color: #F9FAFB !important; 
        padding: 12px !important; /* 패딩 축소로 폭 최적화 */
        border-radius: 12px !important; 
        border: 2px solid #E5E7EB !important;
        border-left: 14px solid #2E7D32 !important; 
    }
    
    /* 6. 📢 확정 명단 캡션 박스 강화 */
    .stCaption {
        font-size: 16px !important;
        color: #000000 !important;
        font-weight: 800 !important;
        background-color: #ECFDF5 !important;
        border: 3px solid #10B981 !important; 
        padding: 14px !important;
        border-radius: 10px !important;
        margin-top: 20px !important;
        display: block !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05) !important;
    }

    /* 7. 팀전 선택창(Selectbox) 강조 */
    div[data-testid="stSelectbox"] > div { border: 2px solid #1E88E5 !important; border-radius: 6px !important; }

    /* 8. 순위 리포트 테이블 디자인 */
    .stTable {
        border: 3px solid #2E7D32 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
        overflow: hidden !important;
    }
    .stTable thead tr th { background-color: #2E7D32 !important; color: white !important; font-weight: 800 !important; }
    
    /* 9. 그룹별 헤더 타이틀 박스 디자인 */
    .group-header-box {
        background-color: #f1f8f1 !important; 
        padding: 12px 18px !important; 
        border-radius: 10px !important; 
        border-left: 8px solid #2E7D32 !important; 
        margin: 20px 0px 15px 0px !important;
        display: flex !important;
        align-items: center !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05) !important;
    }
    .group-header-title {
        font-size: 19px !important; 
        font-weight: 800 !important; 
        color: #1B5E20 !important; 
        letter-spacing: -0.5px !important;
    }
    .group-header-mode {
        font-size: 15px !important; 
        color: #666 !important; 
        font-weight: 500 !important;
    }

    /* 10. [추가] 입력란 폭 및 여백 최소화 */
    div[data-testid="stWidgetLabel"] p {
        margin-bottom: -5px !important;
        font-size: 14px !important;
    }
    div[data-testid="stSelectbox"], div[data-testid="stNumberInput"], div[data-testid="stSlider"] {
        margin-bottom: -10px !important;
    }

    /* 11. [추가] 경기 시작 버튼(전체 대진표 작성) 강력 강조 */
    div.stButton > button {
        width: 100% !important; 
        height: 65px !important; 
        background-color: #2E7D32 !important; 
        color: white !important; 
        font-size: 24px !important; 
        font-weight: 900 !important; 
        border-radius: 15px !important; 
        border: 2px solid #1B5E20 !important; 
        box-shadow: 0 8px 16px rgba(0,0,0,0.2) !important; 
        transition: all 0.3s ease !important; 
        margin: 20px 0px !important;
    }
    div.stButton > button:hover {
        background-color: #1B5E20 !important; 
        transform: translateY(2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }

    /* 입력창 여백 보정 */
    div[data-testid="stNumberInput"] { margin-top: -10px !important; margin-bottom: -10px !important; }
    hr { margin: 5px 0px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='font-size: 18px; text-align: left;'>🎾 서울산 테니스클럽 대회 운영 시스템</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 시스템 설정")
    member_text = st.text_area("전체 회원 명단 (콤마 구분)", value=DEFAULT_MEMBERS, height=200)
    CLUB_MEMBERS = sorted([m.strip() for m in member_text.split(",") if m.strip()])
    st.success(f"현재 총 {len(CLUB_MEMBERS)}명의 회원이 등록되었습니다.")
    st.divider()
    num_groups = st.number_input("월례대회 총 그룹 수", 1, 10, 2)
    st.sidebar.info("""
    **1. 한울 AA (개인)**
    * 매 경기 파트너와 상대가 바뀜
    * 개인별 승률 및 득실 계산 결정

    **2. 한울 AB (혼복/그룹)**
    * 에이스(A)와 라이징 스타(B)가 한 팀
    * 회원 간의 실력 균형을 맞춤

    **3. 한울 TEAM (팀전)**
    * 파트너가 고정된 '팀' 단위 대결
    * 팀 대 팀으로 승패 결정

    **🏆 승점 산정 기준**
    * **승리**: 2점 / **패배**: 0점
    * **무승부**: 1점 (예: 5:5 종료 시)
    * **순위결정**: 승점 > 득실차 > 다득점
    """)

# --- [수정 핵심] 세션 관리 로직 ---
# 버튼 클릭 시 새로운 대진표 생성을 보장하기 위해 사용
if "current_group_data" not in st.session_state:
    st.session_state["current_group_data"] = {}

# --- 메인 로직 ---
group_inputs = {}
global_used_individuals = set()

for i in range(1, num_groups + 1):
    with st.expander(f"📍 {i}그룹 명단 확정", expanded=True):
        # 기존 [1, 4]에서 [0.8, 4.2] 정도로 비율 조정 (더 슬림하게)
        col_cfg, col_select = st.columns([0.6, 4.4])
        with col_cfg:
            g_mode = st.selectbox("방식", ["한울 AA (개인)", "한울 AB (혼복/그룹)", "한울 TEAM (팀전)"], key=f"md_{i}")
            if "AA" in g_mode: p_target = st.number_input(f"인원(5~16)", 5, 16, 10, key=f"target_{i}")
            elif "AB" in g_mode: p_target = st.select_slider(f"인원(짝수)", options=[8, 10, 12, 14, 16], value=10, key=f"target_{i}")
            else: p_target = st.number_input(f"팀 수(5~13)", 5, 13, 8, key=f"target_{i}")

        with col_select:
            available = [m for m in CLUB_MEMBERS if m not in global_used_individuals]
            final_group_names = []
            if "TEAM" in g_mode:
                st.write(f"👥 {i}그룹 복식 팀 구성")
                current_group_used = set()
                for t_idx in range(p_target):
                    t_col1, t_col2 = st.columns(2)
                    realtime_available = [m for m in available if m not in current_group_used]
                    with t_col1:
                        p1 = st.selectbox(f"{t_idx+1}팀-선수1", ["선택안함"] + realtime_available, key=f"g{i}_t{t_idx}_p1")
                        if p1 != "선택안함": current_group_used.add(p1)
                    with t_col2:
                        p2_opts = [m for m in realtime_available if m != p1]
                        p2 = st.selectbox(f"{t_idx+1}팀-선수2", ["선택안함"] + p2_opts, key=f"g{i}_t{t_idx}_p2")
                        if p2 != "선택안함": current_group_used.add(p2)
                    if p1 != "선택안함" and p2 != "선택안함": final_group_names.append(f"{p1}+{p2}")
                for p in current_group_used: global_used_individuals.add(p)
            else:
                selected = st.multiselect(f"👥 회원 선택", options=available, max_selections=p_target, key=f"sel_{i}")
                for p in selected: global_used_individuals.add(p)
                final_group_names = list(selected)
                while len(final_group_names) < p_target: final_group_names.append(f"미배정{len(final_group_names)+1}")
            
            st.caption(f"📢 확정: {', '.join(final_group_names[:p_target])}")
        
        group_inputs[i] = {"count": p_target, "names": final_group_names[:p_target], "mode": g_mode}

# --- [수정 핵심] 버튼 클릭 시 데이터 업데이트 ---
if st.button("🚀 전체 대진표 생성 및 경기 시작"):
    # 현재 설정된 group_inputs를 세션에 저장하여 고정시킴
    st.session_state["current_group_data"] = group_inputs
    st.session_state["generated"] = True
    # 새로운 대진표 생성을 위해 결과를 리셋하고 싶다면 여기서 점수 입력 세션을 지울 수도 있습니다.

# 생성된 데이터가 있을 때만 출력
if st.session_state.get("generated"):
    # 버튼 클릭 당시 저장된 데이터를 불러옴
    display_data = st.session_state["current_group_data"]
    
    for g_id, data in display_data.items():

        # 기존 st.header 자리에 넣을 코드
        st.markdown(f"""
            <div class="group-header-box">
                <span style="font-size: 20px; margin-right: 12px;">🏆</span>
                <span class="group-header-title">
                    {g_id}그룹 경기 운영 상황 <span class="group-header-mode">| {data['mode']}</span>
                </span>
            </div>
        """, unsafe_allow_html=True)

        # 모드별 대진 데이터 선택
        if "AA" in data['mode']: raw = HANUL_AA_DATA.get(data['count'])
        elif "AB" in data['mode']: raw = HANUL_AB_DATA.get(data['count'])
        else: raw = HANUL_TEAM_DATA.get(data['count'])
        
        if not raw:
            st.warning(f"데이터 부족")
            continue

        # --- 출전 현황 테이블 ---
        st.subheader("📊 선수별 출전 현황")
        # 
        sched_dict = {name: ["●" if name in sum(get_match_players(m, data['names'], data['mode']), []) else "○" for m in raw] for name in data['names']}
        st.table(pd.DataFrame(sched_dict).T.rename(columns=lambda x: f"게임 {x+1}"))
        st.divider()

        # --- 결과 입력 섹션 (점수 최대 6점 제한) ---
        scores_data = []
        for idx, match_str in enumerate(raw):
            team_a, team_b = get_match_players(match_str, data['names'], data['mode'])
            
            # 중앙 정렬을 위한 스타일
            flex_style = "display: flex; align-items: center; justify-content: center; height: 100%; min-height: 45px;"
            
            # 레이아웃 구성 (게임 번호, 팀A, 점수A, vs, 점수B, 팀B)
            c0, c1, c2, c3, c4, c5 = st.columns([1.2, 3.5, 1.5, 0.5, 1.5, 3.5])
            
            with c0: 
                st.markdown(f"<div style='{flex_style} font-weight: bold;'>게임 {idx+1}</div>", unsafe_allow_html=True)
            
            with c1: 
                st.markdown(f"<div style='{flex_style} justify-content: flex-end;'>{'+'.join(team_a)}</div>", unsafe_allow_html=True)
            
            with c2: 
                st.markdown("<div style='display: flex; justify-content: center; align-items: center; padding-top: 5px;'>", unsafe_allow_html=True)
                # 🔥 max_value=6으로 수정하여 6점까지만 입력 가능하게 제한
                s_a = st.number_input("s_a", 0, 6, key=f"s_a_{g_id}_{idx}", label_visibility="collapsed", step=1)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with c3: 
                st.markdown(f"<div style='{flex_style} color: #888;'>vs</div>", unsafe_allow_html=True)
            
            with c4: 
                st.markdown("<div style='display: flex; justify-content: center; align-items: center; padding-top: 5px;'>", unsafe_allow_html=True)
                # 🔥 max_value=6으로 수정하여 6점까지만 입력 가능하게 제한
                s_b = st.number_input("s_b", 0, 6, key=f"s_b_{g_id}_{idx}", label_visibility="collapsed", step=1)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with c5: 
                st.markdown(f"<div style='{flex_style} justify-content: flex-start;'>{'+'.join(team_b)}</div>", unsafe_allow_html=True)
            
            # 데이터 저장
            scores_data.append({"team_a": team_a, "team_b": team_b, "s_a": s_a, "s_b": s_b})
            
            # 경기 간 구분선
            st.markdown("<hr style='margin: 5px 0px; border: 0.2px solid #eee;'>", unsafe_allow_html=True)

        stats = {name: {"승점": 0, "승": 0, "무": 0, "패": 0, "득": 0, "실": 0} for name in data['names']}
        for m in scores_data:
            sa, sb = m['s_a'], m['s_b']
            for p in m['team_a']: stats[p]["득"] += sa; stats[p]["실"] += sb
            for p in m['team_b']: stats[p]["득"] += sb; stats[p]["실"] += sa
            if sa == 0 and sb == 0: continue
            if sa > sb:
                for p in m['team_a']: stats[p]["승점"] += 2; stats[p]["승"] += 1
                for p in m['team_b']: stats[p]["패"] += 1
            elif sb > sa:
                for p in m['team_b']: stats[p]["승점"] += 2; stats[p]["승"] += 1
                for p in m['team_a']: stats[p]["패"] += 1
            else:
                for p in (m['team_a'] + m['team_b']): stats[p]["승점"] += 1; stats[p]["무"] += 1
        df = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index': '성명'})
        df['득실차'] = df['득'] - df['실']
        df = df.sort_values(by=['승점', '득실차', '득'], ascending=False).reset_index(drop=True)
        df['순위'] = df.index + 1

        # --- 순위 리포트 출력부 ---
        st.subheader("🏆 실시간 순위 리포트")

        # 데이터프레임 가공 (기존 로직 유지)
        df = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index': '성명'})
        df['득실차'] = df['득'] - df['실']
        df = df.sort_values(by=['승점', '득실차', '득'], ascending=False).reset_index(drop=True)
        df['순위'] = df.index + 1
        
        # 표시할 컬럼 순서 정리
        report_df = df[['순위', '성명', '승점', '승', '무', '패', '득', '실', '득실차']]

        # [디자인 적용] 1등은 금색, 나머지는 줄무늬 효과
        def highlight_winner(s):
            return ['background-color: #FFF9C4; font-weight: bold;' if s.name == 0 else '' for _ in s]

        # 스타일이 적용된 테이블 출력
        styled_df = report_df.style.apply(highlight_winner, axis=1)
        
        # 돋보이게 만들기 위해 컨테이너박스 사용
        with st.container():
            st.table(styled_df)
