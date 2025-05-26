import streamlit as st

def main():
    st.set_page_config(page_title="Gloucestershire Crime Dashboard", page_icon=":police_car:", layout="centered")

    # Heading
    st.markdown("""
        <h1 style='text-align: center; color: #2c3e50;'>🚓 Gloucestershire Crime Dashboard</h1>
        <p style='text-align: center; font-size: 18px; color: #cccccc;'>
            Explore crime statistics and trends in Gloucestershire through interactive visualizations.
        </p>
    """, unsafe_allow_html=True)

    # Button area
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Go to Overview"):
            st.switch_page("pages/1 Overview.py")

    with col2:
        if st.button("🗺️ Go to Crime Map"):
            st.switch_page("pages/2 Crime_Map.py")

    st.markdown("<br><hr style='border-top: 1px solid #ccc;'>", unsafe_allow_html=True)
    st.info("Use the buttons above to explore crime trends and locations across Gloucestershire.")

if __name__ == "__main__":
    main()
