import streamlit_authenticator as stauth

password = "{ここにパスワードを入れる}"

hashed_password = stauth.Hasher([password]).generate()

print(hashed_password)
