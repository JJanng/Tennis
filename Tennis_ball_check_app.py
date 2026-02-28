import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="테니스 볼 관리자", layout="wide")

# 테마 및 모바일 대응 CSS
st.markdown("""
    <style>
    .main { background-color: #F1F8E9; }
    .main-title {
        font-size: 24px !important;
        color: #2E7D32;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .stButton>button { 
        background-color: #2E7D32; color: white; border-radius: 10px; 
        font-weight: bold; width: 100%;
    }
    h1, h2, h3 { color: #2E7D32; }
    [data-testid="stMetricValue"] { color: #EF6C00; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ballusage.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, member TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS usage (id INTEGER PRIMARY KEY AUTOINCREMENT, member TEXT NOT NULL, date TEXT NOT NULL, quantity INTEGER)")
    conn.commit()
    conn.close()

def load_all_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM usage", conn)
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.normalize()
        df['연월_표시'] = df['date'].dt.strftime('%Y년 %m월')
        df['연월_정렬'] = df['date'].dt.strftime('%Y-%m')
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        df = df.sort_values(by='date')
    return df

def load_members():
    conn = get_connection()
    members = [m[0] for m in conn.execute("SELECT member FROM members ORDER BY member").fetchall()]
    conn.close()
    return members

init_db()

st.markdown('<p class="main-title">🎾 테니스 볼 사용 기록기</p>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 관리 도구")
    is_admin = st.checkbox("관리자 모드 활성화")
    if is_admin:
        admin_pwd = st.text_input("비밀번호", type="password")
        if admin_pwd == "1234" or admin_pwd == "":
            st.success("인증 성공")
            with st.expander("회원 관리"):
                new_member = st.text_input("새 회원 이름")
                if st.button("회원 추가"):
                    if new_member.strip():
                        conn = get_connection()
                        try:
                            conn.execute("INSERT INTO members (member) VALUES (?)", (new_member.strip(),))
                            conn.commit()
                            st.rerun()
                        except: st.error("이미 존재합니다.")
                        finally: conn.close()
                
                members = load_members()
                del_mem = st.selectbox("삭제할 회원", ["선택"] + members)
                if st.button("회원 삭제") and del_mem != "선택":
                    conn = get_connection()
                    conn.execute("DELETE FROM usage WHERE member=?", (del_mem,))
                    conn.execute("DELETE FROM members WHERE member=?", (del_mem,))
                    conn.commit()
                    conn.close()
                    st.rerun()

members_list = load_members()
with st.container():
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        target_member = st.selectbox(
            "회원 선택 (입력 가능)", 
            members_list, 
            index=None, 
            placeholder="이름을 선택해 주세요"
        )
    with col2:
        target_date = st.date_input("날짜", date.today())
    with col3:
        target_qty = st.number_input("수량", min_value=0, value=0, step=1)

    if st.button("🔥 사용 기록 저장"):
        if target_member:
            conn = get_connection()
            conn.execute("INSERT INTO usage (member, date, quantity) VALUES (?, ?, ?)", 
                         (target_member, str(target_date), int(target_qty)))
            conn.commit()
            conn.close()
            st.success(f"{target_member}님 기록 완료!")
            st.rerun()
        else:
            st.warning("먼저 이름을 선택해 주세요.")

st.divider()

tab1, tab2 = st.tabs(["📊 통계 및 그래프", "📝 기록 수정/삭제"])

with tab1:
    df_all = load_all_data()
    if df_all.empty:
        st.info("기록이 없습니다. 첫 데이터를 입력해 보세요!")
    else:
        monthly_summary = df_all.groupby(['연월_정렬', '연월_표시'])['quantity'].sum().reset_index()
        monthly_summary = monthly_summary.sort_values('연월_정렬')
        
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            st.subheader("개인별 상세 통계")
            stat_member = st.selectbox(
                "누구의 기록을 볼까요?", 
                members_list, 
                index=None, 
                placeholder="💡 이름을 선택하세요"
            )
            
            st.divider()

            if stat_member:
                df_stat = df_all[df_all['member'] == stat_member]
                if not df_stat.empty:
                    current_month = date.today().strftime('%Y-%m')
                    this_month_qty = df_stat[df_stat['연월_정렬'] == current_month]['quantity'].sum()
                    total_qty = df_stat['quantity'].sum()
                    st.success(f"**{stat_member}** 님의 현황")
                    st.metric("이번 달 총 사용", f"{this_month_qty} 개")
                    st.metric("전체 누적 사용", f"{total_qty} 개")
                else:
                    st.info(f"{stat_member} 님의 데이터가 없습니다.")
            else:
                st.info("👆 위 목록에서 **이름**을 선택하면 개인별 사용 통계를 확인할 수 있습니다.")
            
            st.divider()
            st.subheader("🗓️ 월별 전체 합계")
            summary_display = monthly_summary.sort_values('연월_정렬', ascending=False)
            st.table(summary_display.rename(columns={'연월_표시': '날짜', 'quantity': '합계'})[['날짜', '합계']].set_index('날짜'))

        with col_b:
            st.subheader("📊 일별 상세 기록")
            df_day = df_all.groupby(['date', 'member'])['quantity'].sum().reset_index()
            df_day = df_day.sort_values('date')
            df_day['date_str'] = df_day['date'].dt.strftime('%Y-%m-%d')
            
            fig_day = px.bar(df_day, x='date_str', y='quantity', color='member', 
                             barmode='group', text='quantity')
            
            fig_day.update_traces(
                textposition='outside', 
                textfont=dict(size=18, family="Arial Black", color="black"),
                cliponaxis=False
            )
            
            fig_day.update_layout(
                xaxis_title="날짜", yaxis_title="수량", 
                xaxis={'type': 'category', 'categoryorder': 'array', 'categoryarray': df_day['date_str'].unique(), 'fixedrange': True}, # 🔥 줌 방지
                yaxis={'fixedrange': True}, # 🔥 줌 방지
                bargap=0.6, 
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=14),
                dragmode=False # 🔥 드래그 비활성화
            )
            st.plotly_chart(fig_day, width='stretch', config={'displayModeBar': False}) # 🔥 툴바 숨김
            
            st.subheader("📈 월간 사용 추이")
            fig_month = px.line(monthly_summary, x='연월_표시', y='quantity', markers=True, text='quantity')
            fig_month.update_traces(
                line_color='#2E7D32', marker=dict(size=12), 
                textposition="top center", 
                textfont=dict(size=18, family="Arial Black", color="black")
            )
            fig_month.update_layout(
                xaxis_title="연월", yaxis_title="총 수량",
                xaxis={'type': 'category', 'categoryorder': 'array', 'categoryarray': monthly_summary['연월_표시'].unique(), 'fixedrange': True}, # 🔥 줌 방지
                yaxis={'fixedrange': True}, # 🔥 줌 방지
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=14),
                dragmode=False # 🔥 드래그 비활성화
            )
            st.plotly_chart(fig_month, width='stretch', config={'displayModeBar': False}) # 🔥 툴바 숨김

with tab2:
    st.subheader("데이터 수정 및 삭제")
    df_raw = load_all_data()

    if not df_raw.empty:
        df_edit = df_raw.copy()
        df_edit['date'] = df_edit['date'].dt.date
        df_edit = df_edit.sort_values(by=['date', 'member'], ascending=[False, True])
        df_edit = df_edit.reset_index(drop=True)
        
        edited_df = st.data_editor(df_edit[['member', 'date', 'quantity']], num_rows="dynamic", key="data_editor", hide_index=True)

        if st.button("💾 모든 변경사항 저장"):
            final_df = edited_df.dropna(subset=['member', 'date'])
            final_df = final_df[final_df['member'].astype(str).str.strip() != ""] 

            conn = get_connection()
            try:
                conn.execute("DELETE FROM usage")
                if not final_df.empty:
                    save_df = final_df[['member', 'date', 'quantity']]
                    save_df['date'] = save_df['date'].astype(str)
                    save_df.to_sql("usage", conn, if_exists="append", index=False)
                conn.commit()
                st.success("데이터가 업데이트되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")
            finally:
                conn.close()
    else:
        st.info("수정할 기록이 없습니다.")

if not df_raw.empty:
    csv_data = df_raw.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 전체 데이터 내보내기 (CSV)",
        data=csv_data,
        file_name=f"tennis_ball_{date.today()}.csv",
        mime="text/csv",
    )
