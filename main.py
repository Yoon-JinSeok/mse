import streamlit as st
import numpy as np
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

st.set_page_config(page_title="추세선과 손실함수", layout="wide")

st.title("📈 추세선과 손실함수")
st.caption("제작 : 윤진석")

# ---------- 세션 상태 초기화 ----------
if "points" not in st.session_state:
    st.session_state.points = []        # [(x, y), ...]
if "step" not in st.session_state:
    st.session_state.step = 1           # 현재까지 진행한 단계
if "lines" not in st.session_state:
    # 3개의 추세선 (a: 기울기, b: 절편)
    st.session_state.lines = {
        "추세선 1": {"a": 1.0, "b": 0.0, "color": "#e74c3c"},
        "추세선 2": {"a": 1.333, "b": 0.0, "color": "#2ecc71"},
        "추세선 3": {"a": 0.5, "b": 1.0, "color": "#3498db"},
    }

# ---------- 단계 진행 버튼 ----------
st.markdown("### 단계 진행")
c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
with c1:
    if st.button("▶ 1단계 시작", use_container_width=True):
        st.session_state.step = 1
with c2:
    if st.button("▶ 2단계 진행", use_container_width=True,
                 disabled=len(st.session_state.points) < 2):
        st.session_state.step = max(st.session_state.step, 2)
with c3:
    if st.button("▶ 3단계 진행", use_container_width=True,
                 disabled=len(st.session_state.points) < 2):
        st.session_state.step = max(st.session_state.step, 3)
with c4:
    if st.button("🔄 모두 초기화", use_container_width=True):
        st.session_state.points = []
        st.session_state.step = 1
        st.rerun()

st.divider()

# =====================================================
# 1단계 : 데이터 설정 (좌표평면 클릭으로 점 찍기)
# =====================================================
st.header("1단계 · 데이터 설정")
st.write("좌표평면 위를 **클릭**하면 점이 찍힙니다. (최소 2개 이상)")

X_RANGE = (-10, 10)
Y_RANGE = (-10, 10)

fig1 = go.Figure()

# 클릭 영역 확보용 그리드 (투명 점)
gx = np.linspace(X_RANGE[0], X_RANGE[1], 41)
gy = np.linspace(Y_RANGE[0], Y_RANGE[1], 41)
GX, GY = np.meshgrid(gx, gy)
fig1.add_trace(go.Scatter(
    x=GX.ravel(), y=GY.ravel(),
    mode="markers",
    marker=dict(size=14, color="rgba(0,0,0,0)"),
    hoverinfo="x+y",
    showlegend=False,
    name="click-grid",
))

# 현재 점들
if st.session_state.points:
    xs = [p[0] for p in st.session_state.points]
    ys = [p[1] for p in st.session_state.points]
    fig1.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(size=12, color="#222", line=dict(color="white", width=2)),
        name="데이터",
    ))

fig1.update_layout(
    xaxis=dict(range=X_RANGE, zeroline=True, dtick=1, gridcolor="#eee"),
    yaxis=dict(range=Y_RANGE, zeroline=True, dtick=1, gridcolor="#eee",
               scaleanchor="x", scaleratio=1),
    width=650, height=600,
    margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="white",
)

clicked = plotly_events(fig1, click_event=True, hover_event=False,
                        override_height=600, key="plot_click")

# 클릭 처리 (가장 가까운 격자 포인트로 스냅)
if clicked:
    cx = round(float(clicked[0]["x"]))
    cy = round(float(clicked[0]["y"]))
    if (cx, cy) not in st.session_state.points:
        st.session_state.points.append((cx, cy))
        st.rerun()

colA, colB = st.columns([1, 3])
with colA:
    if st.button("마지막 점 지우기"):
        if st.session_state.points:
            st.session_state.points.pop()
            st.rerun()
with colB:
    st.write(f"현재 점 개수 : **{len(st.session_state.points)}**")
    if st.session_state.points:
        st.code(str(st.session_state.points), language="python")

# =====================================================
# 2단계 : 추세선 그리기
# =====================================================
if st.session_state.step >= 2 and len(st.session_state.points) >= 2:
    st.divider()
    st.header("2단계 · 추세선 그리기")
    st.write("점들 근처를 지나는 추세선(최소제곱법으로 구한 직선)을 그립니다.")

    x = np.array([p[0] for p in st.session_state.points], dtype=float)
    y = np.array([p[1] for p in st.session_state.points], dtype=float)
    a_fit, b_fit = np.polyfit(x, y, 1)

    xx = np.linspace(X_RANGE[0], X_RANGE[1], 200)
    yy = a_fit * xx + b_fit

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x, y=y, mode="markers",
                              marker=dict(size=12, color="#222"),
                              name="데이터"))
    fig2.add_trace(go.Scatter(x=xx, y=yy, mode="lines",
                              line=dict(color="#e67e22", width=3),
                              name=f"추세선  y = {a_fit:.2f}x + {b_fit:.2f}"))
    fig2.update_layout(
        xaxis=dict(range=X_RANGE, zeroline=True, dtick=1, gridcolor="#eee"),
        yaxis=dict(range=Y_RANGE, zeroline=True, dtick=1, gridcolor="#eee",
                   scaleanchor="x", scaleratio=1),
        width=650, height=600,
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig2, use_container_width=False)

    st.success(f"가장 잘 맞는 추세선 : **y = {a_fit:.3f} x + {b_fit:.3f}**")

# =====================================================
# 3단계 : 손실함수값 구하기
# =====================================================
if st.session_state.step >= 3 and len(st.session_state.points) >= 2:
    st.divider()
    st.header("3단계 · 손실함수값 구하기")

    st.markdown("**손실함수 (MSE) 코드**")
    st.code(
        'def MSE(y, y_hat):\n'
        '    return np.mean((y - y_hat)**2)\n\n'
        "print('추세선의 손실함수 값 :', MSE(y, 4/3*x))",
        language="python",
    )

    x = np.array([p[0] for p in st.session_state.points], dtype=float)
    y = np.array([p[1] for p in st.session_state.points], dtype=float)

    def MSE(y, y_hat):
        return np.mean((y - y_hat) ** 2)

    st.markdown("#### 🎚 추세선을 슬라이더로 '잡아서' 움직여 보세요")
    st.caption("기울기(a)와 절편(b)을 조절하면 추세선과 손실함수값이 실시간으로 변합니다.")

    cols = st.columns(3)
    for (name, info), col in zip(st.session_state.lines.items(), cols):
        with col:
            st.markdown(f"**{name}**")
            info["a"] = st.slider(f"{name} 기울기 a",
                                  -5.0, 5.0, float(info["a"]), 0.05,
                                  key=f"{name}_a")
            info["b"] = st.slider(f"{name} 절편 b",
                                  -10.0, 10.0, float(info["b"]), 0.1,
                                  key=f"{name}_b")

    # 시각화
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=x, y=y, mode="markers",
                              marker=dict(size=12, color="#222"),
                              name="데이터"))

    xx = np.linspace(X_RANGE[0], X_RANGE[1], 200)
    losses = {}
    for name, info in st.session_state.lines.items():
        a, b = info["a"], info["b"]
        yy = a * xx + b
        loss = MSE(y, a * x + b)
        losses[name] = (a, b, loss)
        fig3.add_trace(go.Scatter(
            x=xx, y=yy, mode="lines",
            line=dict(color=info["color"], width=3),
            name=f"{name}: y={a:.2f}x+{b:.2f}  |  MSE={loss:.3f}",
        ))

    fig3.update_layout(
        xaxis=dict(range=X_RANGE, zeroline=True, dtick=1, gridcolor="#eee"),
        yaxis=dict(range=Y_RANGE, zeroline=True, dtick=1, gridcolor="#eee",
                   scaleanchor="x", scaleratio=1),
        width=750, height=600,
        plot_bgcolor="white",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.8)"),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig3, use_container_width=False)

    st.markdown("#### 📊 손실함수 값 비교")
    metric_cols = st.columns(3)
    best_name = min(losses, key=lambda k: losses[k][2])
    for (name, (a, b, loss)), col in zip(losses.items(), metric_cols):
        with col:
            label = f"{name}  (y = {a:.2f}x + {b:.2f})"
            delta = "🥇 최저" if name == best_name else None
            st.metric(label, f"MSE = {loss:.4f}", delta=delta)

    with st.expander("📜 코드 실행 결과 (예시)"):
        for name, (a, b, loss) in losses.items():
            st.write(f"`print('추세선({name})의 손실함수 값 :', "
                     f"MSE(y, {a:.3f}*x + {b:.3f}))`  →  **{loss:.4f}**")
