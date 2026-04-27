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
if "lines" not in st.session_state:
    st.session_state.lines = {
        "추세선 1": {"a": 1.0, "b": 0.0, "color": "#e74c3c"},
        "추세선 2": {"a": 1.333, "b": 0.0, "color": "#2ecc71"},
        "추세선 3": {"a": 0.5, "b": 1.0, "color": "#3498db"},
    }


# ---------- 단계 진행 ----------
st.markdown("### 단계 진행")
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("1단계 시작", use_container_width=True):
        st.session_state.step = 1
with c2:
    if st.button("2단계 진행", use_container_width=True,
                 disabled=len(st.session_state.points) < 2):
        st.session_state.step = max(st.session_state.step, 2)
with c3:
    if st.button("3단계 진행", use_container_width=True,
                 disabled=len(st.session_state.points) < 2):
        st.session_state.step = max(st.session_state.step, 3)
with c4:
    if st.button("모두 초기화", use_container_width=True):
        st.session_state.points = []
        st.session_state.step = 1
        st.session_state.last_click = None
        st.rerun()

st.divider()

# =====================================================
# 1단계 : 데이터 설정
# =====================================================
st.header("1단계 · 데이터 설정")
st.write("아래 좌표평면 위를 **클릭**하면 점이 찍힙니다.")

snap = st.checkbox("정수 격자에 스냅", value=True)

img = render_plane(st.session_state.points)
coords = streamlit_image_coordinates(img, key="plane_click
