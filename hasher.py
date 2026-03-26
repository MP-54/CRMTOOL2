import streamlit_authenticator as stauth

passwords = [
    "zqsd", "crm-max2025", "TERO14052016!#", "crm-lou2025",
    "crm-maxa2025", "crm-ali2025", "crm-sam2025", "crm-matt2025",
    "crm-kev2025", "crm-ale2025", "crm-eri2025", "crm-cor2025",
    "crm-mic2025", "crm-ven2025", "crm-sio2025", "crm-pal2025",
    "crm-cha2025", "crm-chl2025", "crm-pj2025", "crm-thS2025",
    "crm-jpt2025", "crm-sar2025", "crm-jul2025", "crm-flo2025", "crm-luc2025"
]

hasher = stauth.Hasher()
hashed_passwords = hasher.generate(passwords)
print(hashed_passwords)