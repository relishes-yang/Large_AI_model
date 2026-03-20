import cv2
import numpy as np
import streamlit as st
from PIL import Image
import io

# 页面配置
st.set_page_config(
    page_title="AI 美颜照片处理",
    page_icon="📸",
    layout="centered"
)

# 标题
st.title("📸 AI 美颜照片处理工具")
st.markdown("---")

# 侧边栏说明
with st.sidebar:
    st.header("💡 使用说明")
    st.markdown("""
    1. 上传一张人像照片
    2. 选择美颜功能
    3. 下载处理后的图片

    **支持格式**: JPG, JPEG, PNG, BMP
    """)

# 功能选项映射
FILTER_OPTIONS = {
    "1": ("🌟 磨皮 (高斯滤波)", "SmoothSkin"),
    "2": ("🌞 滤镜 (暖色调)", "WarmFilter"),
    "3": ("🧹 去噪 (中值滤波)", "Denoise"),
    "4": ("🔍 锐化 (增强细节)", "Sharpen"),
    "5": ("✨ 高级磨皮 (双边滤波)", "BilateralBlur")
}


def load_image(image_file):
    """将上传的文件转换为 OpenCV 格式"""
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    return img


def apply_filter(img, choice):
    """根据用户选择应用不同的美颜功能"""
    if choice == 1:  # 磨皮 (基于高斯模糊)
        result = cv2.GaussianBlur(img, (15, 15), 0)
        description = "SmoothSkin"

    elif choice == 2:  # 滤镜 (暖色调)
        result = img.copy()
        # OpenCV 默认是 BGR 格式，索引 2 是红色通道
        result[:, :, 2] = cv2.add(result[:, :, 2], 30)
        description = "WarmFilter"

    elif choice == 3:  # 去噪 (中值滤波)
        result = cv2.medianBlur(img, 5)
        description = "Denoise"

    elif choice == 4:  # 锐化 (增强细节)
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        result = cv2.filter2D(img, -1, kernel)
        description = "Sharpen"

    elif choice == 5:  # 双边滤波 (高级磨皮)
        result = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
        description = "BilateralBlur"

    else:
        return img, "Original"

    return result, description


def cv2_to_pil(cv2_img):
    """将 OpenCV 图像转换为 PIL 格式（用于 Streamlit 显示）"""
    cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(cv2_img)


def pil_to_download(cv2_img, filename):
    """将 OpenCV 图像转换为可下载格式"""
    _, buffer = cv2.imencode('.jpg', cv2_img)
    return buffer.tobytes()


# 主界面
st.header("📤 步骤 1: 上传图片")
uploaded_file = st.file_uploader(
    "选择一张图片",
    type=["jpg", "jpeg", "png", "bmp"],
    help="支持中文文件名，直接拖拽或点击上传"
)

if uploaded_file is not None:
    # 显示原图
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("原图")
        original_img = load_image(uploaded_file)
        st.image(cv2_to_pil(original_img), use_container_width=True)
        st.caption(f"尺寸：{original_img.shape[1]} x {original_img.shape[0]}")

    # 功能选择
    st.header("🎨 步骤 2: 选择美颜功能")

    # 使用单选按钮代替数字输入
    filter_choice = st.radio(
        "选择处理效果:",
        options=list(FILTER_OPTIONS.keys()),
        format_func=lambda x: FILTER_OPTIONS[x][0],
        horizontal=True
    )

    # 处理按钮
    process_btn = st.button("🚀 开始处理", type="primary")

    if process_btn:
        with st.spinner("正在处理图片..."):
            # 应用滤镜
            processed_img, desc = apply_filter(original_img, int(filter_choice))

            # 显示结果
            with col2:
                st.subheader("处理后")
                st.image(cv2_to_pil(processed_img), use_container_width=True)
                st.caption(f"效果：{FILTER_OPTIONS[filter_choice][0]}")

            # 下载按钮
            st.header("📥 步骤 3: 下载结果")

            download_bytes = pil_to_download(processed_img, f"result_{desc}.jpg")

            st.download_button(
                label="📸 下载处理后的图片",
                data=download_bytes,
                file_name=f"result_{desc}.jpg",
                mime="image/jpeg",
                type="primary"
            )

            st.success("✅ 处理完成！点击下载保存到您的设备。")

else:
    st.info("👆 请先上传一张图片")

    # 显示示例图（可选）
    st.markdown("### 示例效果预览")
    st.markdown("上传后即可看到处理前后的对比效果")

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Powered by OpenCV + Streamlit | 📸 AI 美颜照片处理"
    "</div>",
    unsafe_allow_html=True
)