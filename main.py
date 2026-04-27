# main.py
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="추세선과 손실함수", layout="wide")
st.title("추세선과 손실함수")
st.caption("제작 : 윤진석")

# ---------- 상수 ----------
IMG_W, IMG_H = 560, 560
X_RANGE = (-10, 10)
Y_RANGE = (-10, 10)


def data_to_pixel(x, y):
    px = (x - X_RANGE[0]) / (X_RANGE[1] - X_RANGE[0]) * IMG_W
    py = (Y_RANGE[1] - y) / (Y_RANGE[1] - Y_RANGE[0]) * IMG_H
    return px, py


def pixel_to_data(px, py):
    x = X_RANGE[0] + px / IMG_W * (X_RANGE[1] - X_RANGE[0])
    y = Y_RANGE[1] - py / IMG_H * (Y_RANGE[1] - Y_RANGE[0])
    return x, y


def render_plane(points, lines=None):
    img = Image.new("RGB", (IMG_W, IMG_H), "white")
    d = ImageDraw.Draw(img)

    # 격자
    for i in range(X_RANGE[0], X_RANGE[1] + 1):
        px, _ = data_to_pixel(i, 0)
        d.line([(px, 0), (px, IMG_H)], fill="#ececec", width=1)
    for i in range(Y_RANGE[0], Y_RANGE[1] + 1):
        _, py = data_to_pixel(0, i)
        d.line([(0, py), (IMG_W, py)], fill="#ececec", width=1)

    # 축
    px0, py0 = data_to_pixel(0, 0)
    d.line([(px0, 0), (px0, IMG_H)], fill="black", width=2)
    d.line([(0, py0), (IMG_W, py0)], fill="black", width=2)

    # 눈금 라벨
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    for i in range(X_RANGE[0], X_RANGE[1] + 1, 2):
        if i == 0:
            continue
        px, _ = data_to_pixel(i, 0)
        d.text((px + 2, py0 + 2), str(i), fill="#666", font=font)
    for i in range(Y_RANGE[0], Y_RANGE[1] + 1, 2):
        if i == 0:
            continue
        _, py = data_to_pixel(0, i)
        d.text((px0 + 4, py - 6), str(i), fill="#666", font=font)

    # 추세선
    if lines:
        for a, b, color in lines:
            p1 = data_to_pixel(X_RANGE[0], a * X_RANGE[0] + b)
            p2 = data_to_pixel(X_RANGE[1], a * X_RANGE[1] + b)
            d.line([p1, p2], fill=color, width=3)

    # 데이터 점
    for x, y in points:
        px, py = data_to_pixel(x, y)
        r = 8
        d.ellipse([px - r, py - r, px + r, py + r],
                  fill="#222", outline="white", width=2)
    return img


# ---------- 세션 상태 ----------
if "points" not in st.session_state:
    st.session_state.points = []
if "step" not in st.session_state:
    st.session_state.step = 1
if "last_click" not in st.session_state:
    st.session_state.last_click = None
if "init_line" not in st.session_state:
    st.session_state.init_line = False


# ---------- 단계 진행 ----------
st.markdown("### 단계 진행")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("1단계 시작", use_container_width=True):
        st.session_state.step = 1
with c2:
    if st.button("2단계 진행", use_container_width=True,
                 disabled=len(st.session_state.points) < 2):
        st.session_state.step = max(st.session_state.step, 2)
        st.session_state.init_line = False
with c3:
    if st.button("모두 초기화", use_container_width=True):
        st.session_state.points = []
        st.session_state.step = 1
        st.session_state.last_click = None
        st.session_state.init_line = False
        for k in ["slope_a", "intercept_b"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

st.divider()

# =====================================================
# 1단계 : 데이터 설정
# =====================================================
st.header("1단계 · 데이터 설정")
st.write("아래 좌표평면 위를 **클릭**하면 점이 찍힙니다.")

snap = st.checkbox("정수 격자에 스냅", value=True)

img = render_plane(st.session_state.points)
coords = streamlit_image_coordinates(img, key="plane_click")

if coords is not None:
    sig = (coords["x"], coords["y"])
    if sig != st.session_state.last_click:
        st.session_state.last_click = sig
        x_data, y_data = pixel_to_data(coords["x"], coords["y"])
        if snap:
            x_data = int(round(x_data))
            y_data = int(round(y_data))
        else:
            x_data = round(x_data, 2)
            y_data = round(y_data, 2)
        if (x_data, y_data) not in st.session_state.points:
            st.session_state.points.append((x_data, y_data))
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
        st.code(f"points = {st.session_state.points}", language="python")

# =====================================================
# 2단계 : 추세선 그리기 + 손실함수값 구하기 (통합)
# =====================================================
if st.session_state.step >= 2 and len(st.session_state.points) >= 2:
    st.divider()
    st.header("2단계 · 추세선 그리기 & 손실함수값 구하기")

    x = np.array([p[0] for p in st.session_state.points], dtype=float)
    y = np.array([p[1] for p in st.session_state.points], dtype=float)

    a_fit, b_fit = np.polyfit(x, y, 1)

    if not st.session_state.init_line:
        a_init = round(float(a_fit) + 0.7, 2)
        b_init = round(float(b_fit) - 1.5, 1)
        a_init = max(-5.0, min(5.0, a_init))
        b_init = max(-10.0, min(10.0, b_init))
        st.session_state.slope_a = a_init
        st.session_state.intercept_b = b_init
        st.session_state.init_line = True

    left, right = st.columns([2, 1])

    with right:
        st.markdown("#### 추세선 조절")
        a = st.slider("기울기 a", -5.0, 5.0,
                      float(st.session_state.slope_a), 0.05,
                      key="slope_a")
        b = st.slider("절편 b", -10.0, 10.0,
                      float(st.session_state.intercept_b), 0.1,
                      key="intercept_b")

        st.markdown("#### 손실함수 (MSE) 코드")
        mse_code = (
            "def MSE(y, y_hat):\n"
            "    return np.mean((y - y_hat)**2)\n\n"
        )
        st.code(mse_code, language="python")

        def MSE(y, y_hat):
            return np.mean((y - y_hat) ** 2)

        y_hat = a * x + b
        loss = MSE(y, y_hat)

        st.markdown("#### 현재 추세선")
        st.write(f"y = {a:.2f} x + ({b:.2f})")

        st.markdown("#### 손실함수 값")
        st.metric("MSE", f"{loss:.4f}")

        with st.expander("최적 추세선 보기 (참고)"):
            st.write(f"최소제곱법 결과 : y = {a_fit:.3f} x + {b_fit:.3f}")
            best_loss = MSE(y, a_fit * x + b_fit)
            st.write(f"최적 추세선의 MSE : {best_loss:.4f}")

    with left:
        img2 = render_plane(
            st.session_state.points,
            lines=[(a, b, "#e74c3c")],
        )
        st.image(img2)
