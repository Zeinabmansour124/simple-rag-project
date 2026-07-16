import streamlit_authenticator as stauth


mots_de_passe = ["monmotdepasse123"]
hasher = stauth.Hasher(mots_de_passe)
hashes = hasher.generate()
print(hashes)