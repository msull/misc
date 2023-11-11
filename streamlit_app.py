from streamlit_authenticator.exceptions import RegisterError

from app_setup import get_current_user, set_page_config, st
from misc_shared.auth_helpers import save_auth_db

authenticator = set_page_config(initial_sidebar_state="expanded")
st.write(f"Welcome {get_current_user()}")
if not st.session_state.get("authentication_status"):
    data = authenticator.login("Login")
    if data[1]:
        st.rerun()
    try:
        if authenticator.register_user("Register", preauthorization=True):
            st.info("Registered!")
            save_auth_db(authenticator)
    except RegisterError:
        st.error("Sorry, registration is closed.")
else:
    authenticator.logout("Logout")
