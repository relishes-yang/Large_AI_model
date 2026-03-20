import cv2
import numpy as np
import streamlit as st
from PIL import Image
import io
import zipfile
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="AI 美颜照片处理",
    page_icon="📸",
    layout="wide"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    .stTooltipContent {
        max-width: 400px;
        font-size: 14px;
    }
    .filter-card {
        padding: 10px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📸 AI 美颜照片处理工具")
st.markdown("---")

# 侧边栏说明
with st.sidebar:
    st.header("💡 使用说明")
    st.markdown("""
    1. **上传**一张人像照片
    2. **多选**美颜功能（可全选）
    3. **查看**对比效果
    4. **下载**处理后的图片

    **支持格式**: JPG, JPEG, PNG, BMP

    **注意**: 下载时浏览器会弹出保存对话框，
    您可以在对话框中选择保存路径。
    """)

    st.header("⚙️ 参数设置")
    ksize = st.slider("滤波核大小 (奇数)", 3, 15, 5, step=2)
    sigma = st.slider("Sigma 强度值", 10, 100, 50)

# 滤镜功能定义（已修复数据类型问题）
FILTER_OPTIONS = {
    "mean": {
        "name": "🌟 均值滤波",
        "desc": "通过计算邻域像素平均值来平滑图像，适合去除随机噪声，但会模糊边缘细节。",
        "func": lambda img, k, s: cv2.blur(img, (k, k))
    },
    "box": {
        "name": "📦 方框滤波",
        "desc": "类似均值滤波，但可控制是否归一化。归一化后效果与均值滤波相同。",
        "func": lambda img, k, s: cv2.boxFilter(img, -1, (k, k), normalize=True)
    },
    "gaussian": {
        "name": "🌸 高斯滤波",
        "desc": "使用高斯分布加权平均，中心权重高，边缘权重低。比均值滤波更好地保留细节。",
        "func": lambda img, k, s: cv2.GaussianBlur(img, (k, k), sigmaX=s)
    },
    "median": {
        "name": "🧹 中值滤波",
        "desc": "取邻域像素的中位数，对椒盐噪声（黑白雪花点）去除效果极佳，能很好保留边缘。",
        "func": lambda img, k, s: cv2.medianBlur(img, k)
    },
    "bilateral": {
        "name": "✨ 双边滤波",
        "desc": "非线性滤波，既能去噪又能保留边缘。适合人像磨皮，不会模糊五官轮廓。",
        "func": lambda img, k, s: cv2.bilateralFilter(img, d=k, sigmaColor=s, sigmaSpace=s)
    },
    "laplacian": {
        "name": "🔍 拉普拉斯锐化",
        "desc": "增强图像边缘和细节，使图片更清晰。适合处理模糊照片。",
        "func": lambda img, k, s: cv2.convertScaleAbs(cv2.Laplacian(img, cv2.CV_64F))
    },
    "laplacian_sharpen": {
        "name": "⚡ 拉普拉斯锐化增强",
        "desc": "将拉普拉斯边缘叠加回原图，增强细节同时保留原图信息。修复了数据类型问题。",
        "func": lambda img, k, s: np.clip(img.astype(np.float32) - cv2.Laplacian(img, cv2.CV_64F), 0, 255).astype(
            np.uint8)
    },
    "sobel": {
        "name": "📐 Sobel 边缘检测",
        "desc": "检测图像中的边缘轮廓，可用于提取物体边界或艺术效果处理。",
        "func": lambda img, k, s: cv2.convertScaleAbs(cv2.Sobel(img, cv2.CV_64F, 1, 1, ksize=k))
    },
    "canny": {
        "name": "🎯 Canny 边缘检测",
        "desc": "更精确的边缘检测算法，能检测出图像中的主要轮廓线条。",
        "func": lambda img, k, s: cv2.Canny(img, 100, 200)
    },
    "sharpen": {
        "name": "🔪 锐化增强",
        "desc": "通过卷积核增强图像细节，让照片看起来更清晰锐利。",
        "func": lambda img, k, s: cv2.filter2D(img, -1,
                                               np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]], dtype=np.float32))
    },
    "warm": {
        "name": "🌞 暖色滤镜",
        "desc": "增加红色通道强度，使照片呈现温暖色调，适合人像美化。",
        "func": lambda img, k, s: cv2.convertScaleAbs(img, alpha=1.0, beta=0)
    },
    "denoise": {
        "name": "🧼 快速去噪",
        "desc": "使用快速非局部均值去噪算法，有效去除图像噪点同时保留细节。",
        "func": lambda img, k, s: cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    },
    "histogram": {
        "name": "📊 直方图均衡化",
        "desc": "增强图像对比度，使暗部更亮、亮部更暗，细节更丰富。",
        "func": lambda img, k, s: cv2.convertScaleAbs(cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2YUV)[:, :, 0]))
    }
}


def load_image(image_file):
    """加载图片"""
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    return img


def apply_filters(img, selected_filters, ksize, sigma):
    """应用选定的滤波器"""
    results = []
    for filter_key in selected_filters:
        filter_info = FILTER_OPTIONS[filter_key]
        try:
            if filter_key == "warm":
                result = img.copy()
                # 修复：增加红色通道，确保数据类型正确
                result = result.astype(np.int16)
                result[:, :, 2] = np.clip(result[:, :, 2] + 30, 0, 255)
                result = result.astype(np.uint8)

            elif filter_key == "histogram":
                # 修复：直方图均衡化需要正确处理通道
                yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
                yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
                result = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

            else:
                result = filter_info["func"](img, ksize, sigma)

            # 确保数据类型为 uint8
            if result.dtype != np.uint8:
                result = np.clip(result, 0, 255).astype(np.uint8)

            # 确保是 3 通道
            if len(result.shape) == 2:
                result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

            results.append({
                "name": filter_info["name"],
                "key": filter_key,
                "image": result,
                "desc": filter_info["desc"]
            })
        except Exception as e:
            st.error(f"❌ {filter_info['name']} 处理失败：{str(e)}")

    return results


def cv2_to_pil(cv2_img):
    """OpenCV 转 PIL"""
    if len(cv2_img.shape) == 2:
        cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_GRAY2RGB)
    else:
        cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(cv2_img)


def create_download_bytes(cv2_img, format='jpg'):
    """转换为可下载字节"""
    _, buffer = cv2.imencode(f'.{format}', cv2_img)
    return buffer.tobytes()


# 主界面
st.header("📤 步骤 1: 上传图片")
uploaded_file = st.file_uploader(
    "选择一张图片",
    type=["jpg", "jpeg", "png", "bmp"],
    help="支持中文文件名，直接拖拽或点击上传"
)

if uploaded_file is not None:
    # 加载原图
    original_img = load_image(uploaded_file)

    # 显示原图
    col_orig, col_info = st.columns([1, 5]) # 返回三个列对象，用于并排按照比例显示内容，第一个参数是列的比例，第二个参数是列的比例
    with col_orig:
        st.subheader("📷 原图")
        st.image(cv2_to_pil(original_img), use_container_width=True)
    with col_info:
        st.metric("宽度", f"{original_img.shape[1]} px")
        st.metric("高度", f"{original_img.shape[0]} px")
        st.metric("通道", f"{original_img.shape[2] if len(original_img.shape) > 2 else 1}")

    st.markdown("---")

    # 功能选择区域
    st.header("🎨 步骤 2: 选择美颜功能")
    st.caption("💡 鼠标悬停在功能名称上可查看详细说明")

    # 创建功能选择网格
    cols_per_row = 4
    filter_keys = list(FILTER_OPTIONS.keys())
    num_filters = len(filter_keys)

    selected_filters = []

    # 分行显示复选框
    for i in range(0, num_filters, cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < num_filters:
                key = filter_keys[i + j]
                with col:
                    with st.container():
                        st.markdown(f"<div class='filter-card'>", unsafe_allow_html=True)
                        # 使用 tooltip 显示说明
                        selected = st.checkbox(
                            FILTER_OPTIONS[key]["name"],
                            key=f"filter_{key}",
                            help=FILTER_OPTIONS[key]["desc"]
                        )
                        if selected:
                            selected_filters.append(key)
                        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"✅ 已选择 **{len(selected_filters)}** 个功能")

    # 处理按钮
    process_btn = st.button("🚀 开始处理", type="primary", disabled=len(selected_filters) == 0)

    if process_btn:
        with st.spinner("正在处理图片，请稍候..."):
            # 应用所有选定的滤波器
            results = apply_filters(original_img, selected_filters, ksize, sigma)

            if results:
                st.markdown("---")
                st.header("📊 步骤 3: 查看处理结果")

                # 计算网格布局（最多 4 列）
                num_results = len(results)
                cols_per_row = min(4, num_results)
                num_rows = (num_results + cols_per_row - 1) // cols_per_row

                # 显示结果网格
                for row in range(num_rows):
                    cols = st.columns(cols_per_row)
                    for col_idx, col in enumerate(cols):
                        result_idx = row * cols_per_row + col_idx
                        if result_idx < num_results:
                            with col:
                                result = results[result_idx]
                                st.subheader(result["name"])
                                st.image(cv2_to_pil(result["image"]), use_container_width=True)
                                with st.expander("📖 功能说明"):
                                    st.write(result["desc"])

                st.markdown("---")
                st.header("📥 步骤 4: 下载结果")

                # 单个下载
                st.subheader("单独下载")
                download_cols = st.columns(min(3, len(results)))
                for idx, result in enumerate(results):
                    with download_cols[idx % len(download_cols)]:
                        download_bytes = create_download_bytes(result["image"])
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            label=f"📸 下载 {result['name']}",
                            data=download_bytes,
                            file_name=f"{result['name']}_{timestamp}.jpg",
                            mime="image/jpeg",
                            key=f"download_{result['key']}"
                        )

                # 批量下载（打包）
                st.subheader("📦 批量下载（ZIP 压缩包）")
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    for result in results:
                        img_bytes = create_download_bytes(result["image"])
                        zip_file.writestr(f"{result['name']}_{timestamp}.jpg", img_bytes)
                    # 也添加原图
                    orig_bytes = create_download_bytes(original_img)
                    zip_file.writestr(f"原图_{timestamp}.jpg", orig_bytes)

                zip_buffer.seek(0)
                st.download_button(
                    label="📦 下载全部图片 (ZIP)",
                    data=zip_buffer,
                    file_name=f"美颜处理结果_{timestamp}.zip",
                    mime="application/zip",
                    type="primary"
                )

                st.success(f"✅ 处理完成！共生成 {len(results)} 张图片。")
                st.info("💡 **下载提示**: 点击下载按钮后，浏览器会弹出保存对话框，您可以在对话框中选择保存路径。")

else:
    st.info("👆 请先上传一张图片")

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "Powered by OpenCV + Streamlit | 📸 AI 美颜照片处理工具<br>"
    "支持 13 种图像处理功能 | 可多选 | 批量下载"
    "</div>",
    unsafe_allow_html=True
)