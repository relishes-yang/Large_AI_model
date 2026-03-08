import streamlit as st

if "a" not in st.session_state:
    st.session_state.a = 0
clicked = st.button("加1")

if clicked:
    st.session_state.a += 1
st.write(st.session_state.a)
print(st.session_state)