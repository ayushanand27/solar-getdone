import streamlit as st


def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown(
            """
<div style="text-align:center; padding:50px;">
<h1>☀️ Solar OS</h1>
<p style="color:#8B949E;">Autonomous Solar Farm Intelligence</p>
</div>
""",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input(
                "🔐 Enter Access Password",
                type="password",
                placeholder="Enter password...",
            )
            if st.button("Login", use_container_width=True):
                try:
                    expected = st.secrets["auth"]["password"]
                except (KeyError, FileNotFoundError, AttributeError):
                    st.error("❌ Auth not configured. Add [auth] password to secrets.")
                    st.stop()
                if password == expected:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")
        st.stop()
