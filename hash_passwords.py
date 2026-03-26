import streamlit_authenticator as stauth

passwords = ["pass123", "secure456"]
hashed_passwords = stauth.Hasher(passwords).generate()

for pw, h in zip(passwords, hashed_passwords):
    print(f"{pw} → {h}")
