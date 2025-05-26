import streamlit as st

# Main Page Redirection
def main():
    st.title("Main Page")
    st.write("Welcome to the Crime Dashboard")

    # Use button to trigger page switch
    if st.button('Go to Overview'):
        st.switch_page("1 Overview")

if __name__ == "__main__":
    main()
