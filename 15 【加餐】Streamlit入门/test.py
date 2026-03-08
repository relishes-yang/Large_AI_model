import os
from pathlib import Path
import streamlit as st

# 获取当前脚本所在目录
script_dir = Path(__file__).parent
# 构建图片的完整路径
image_path = script_dir / "头像.png"

# 使用完整路径显示图片
st.image(str(image_path), width=200)