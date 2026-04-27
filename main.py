# main.py
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="chuseseon", layout="wide")
st.title("추세선과 손실함수")
st.caption("제작 : 윤진석")

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

    for i in range(X_RANGE[0], X_RANGE[1] + 1):
        px, _ = data_to_pixel(i, 0)
        d.line([(px, 0), (px, IMG_H)], fill="#ececec", width=1)
    for i in range(Y_RANGE[0], Y_RANGE[1] + 1):
        _, py = data_to_pixel(0, i)
        d.line([(0, py), (IMG_W, py)], fill="#ececec", width=1)

    px0, py0 = data_to_pixel(0, 0)
    d.line([(px0, 0), (px0, IMG_H)], fill="black", width=2)
    d.line([(0, py0), (IMG_W, py0)], fill="black", width=2)

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

    if lines:
        for a, b, color in lines:
            p1 = data_to_pixel(X_RANGE[0], a * X_RANGE[0] + b)
            p2 = data_to_pixel(X_RANGE[1], a * X_RANGE[1] + b)
            d.line([p1, p2], fill=color, width=3)

    for x, y in points:
        px, py = data_to_pixel(x, y)
        r = 8
        d.ellipse(
            [px - r, py - r, px + r, py + r],
            fill="#222",
            outline="white",
            width=2,
        )
    return img


if "points" not in st.session_state:
    st.session_state.points = []
if "step" not in st.session_state:
    st.session_state.step = 1
if "last_click" not in st.session_state:
    st.session_state.last_click = None
if "lines" not in st.session_state:
    st.session_state.lines = {
        "line1": {"a": 1.0, "b": 0.0, "color": "#e74c3c", "label": "추세선 1"},
        "line2": {"a": 1.333, "b": 0.0, "color": "#2ecc71", "label": "추세선 2"},
        "line3": {"a": 0.5, "b": 1.0, "color": "#3498db", "label": "추세선 3"},
    }


st.markdown("### 단계 진행")
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("1단계 시작", use_container_width=True):
        st.session_state.step = 1
with c2:
    disabled2 = len(st.session_state.points) < 2
    if st.button("2단계 진행", use_container_width=True, disabled=disabled2):
        st.session_state.step = max(st.session_state.step, 2)
with c3:
    disabled3 = len(st.session_state.points) < 2
    if st.button("3단계 진행", use_container_width=True, disabled=disabled3):
        st.session_state.step = max(st.session_state.step, 3)
with c4:
    if st.button("모두 초기화", use_container_width=True):
        st.session_state.points = []
        st.session_state.step = 1
        st.session_state.last_click = None
        st.rerun()

st.divider()

st.header("1단계 - 데이터 설정")
st.write("아래 좌표평면을 클릭하면 점이 찍힙니다.")

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


if st.session_state.step >= 2 and len(st.session_state.points) >= 2:
    st.divider()
    st.header("2단계 - 추세선 그리기")

    x = np.array([p[0] for p in st.session_state.points], dtype=float)
    y = np.array([p[1] for p in st.session_state.points], dtype=float)
    a_fit, b_fit = np.polyfit(x, y, 1)

    img2 = render_plane(
        st.session_state.points,
        lines=[(a_fit, b_fit, "#e67e22")],
    )
    st.image(img2)
    st.success(f"최소제곱법 추세선 : y = {a_fit:.3f} x + {b_fit:.3f}")


if st.session_state.step >= 3 and len(st.session_state.points) >= 2:
    st.divider()
    st.header("3단계 - 손실함수값 구하기")

    st.markdown("**손실함수 (MSE) 코드**")
    code_text = (
        "def MSE(y, y_hat):\n"
        "    return np.mean((y - y_hat)**2)\n\n"
        "print('추세선의 손실함수 값 :', MSE(y, 4/3*x))"
    )
    st.code(code_text, language="python")

    x = np.array([p[0] for p in st.session_state.points], dtype=float)
    y = np.array([p[1] for p in st.session_state.points], dtype=float)

    def MSE(y, y_hat):
        return np.mean((y - y_hat) ** 2)

    st.markdown("#### 추세선을 슬라이더로 움직여 보세요")
    cols = st.columns(3)
    for (key, info), col in zip(st.session_state.lines.items(), cols):
        with col:
            st.markdown(f"**{info['label']}**")
            info["a"] = st.slider(
                f"{info['label']} 기울기 a",
                -5.0, 5.0, float(info["a"]), 0.05,
                key=f"{key}_a",
            )
            info["b"] = st.slider(
                f"{info['label']} 절편 b",
                -10.0, 10.0, float(info["b"]), 0.1,
                key=f"{key}_b",
            )

    lines_for_draw = [
        (info["a"], info["b"], info["color"])
        for info in st.session_state.lines.values()
    ]
    img3 = render_plane(st.session_state.points, lines=lines_for_draw)
    st.image(img3)

    st.markdown("#### 손실함수 값 비교")
    losses = {}
    for key, info in st.session_state.lines.items():
        a, b = info["a"], info["b"]
        loss = MSE(y, a * x + b)
        losses[key] = (info["label"], a, b, loss)

    best_key = min(losses, key=lambda k: losses[k][3])
    mc = st.columns(3)
    for (key, (label, a, b, loss)), col in zip(losses.items(), mc):
        with col:
            delta_text = "최저" if key == best_key else None
            st.metric(
                f"{label} (y = {a:.2f}x + {b:.2f})",
                f"MSE = {loss:.4f}",
                delta=delta_text,
            )

    with st.expander("코드 실행 결과 (예시)"):
        for key, (label, a, b, loss) in losses.items():
            st.write(f"{label}: MSE(y, {a:.3f}*x + {b:.3f}) -> {loss:.4f}")
