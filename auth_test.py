import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login()

if st.session_state.get('authentication_status'):
    authenticator.logout()
    st.write(f"Bienvenue *{st.session_state.get('name')}*")
    st.title("Contenu protege ici")
elif st.session_state.get('authentication_status') is False:
    st.error("Nom d'utilisateur/mot de passe incorrect")
elif st.session_state.get('authentication_status') is None:
    st.warning("Merci d'entrer votre nom d'utilisateur et mot de passe")