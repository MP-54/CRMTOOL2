import streamlit as st

st.set_page_config(page_title="How to use", layout="wide")
st.title("How to use it ❓")

st.markdown("""
Welcome to **MIDCAP's CRM App**!  

---

## 🎯 Focus

### Overview  
This page allows you to have a quick outlook on which sales addresses how many clients/prospects and in which countries.  
Right under, you'll see a **TOP 10** of the clients.  
⚠️ This top 10 is always based on your applied filters (filters are on the left).

### Client  
Here you can access info sheets on clients, per company and/or person.  
You can update the **company info** (upper pane), **client info** (left pane) and their **access** to our services (right pane).

If you edit a client's a info, make sure to hit the save button !
---

## 💾 Database

### The table sheet  
Here you have direct access to the "Supabase" sheet that contains all the info we've gathered so far about anyone.  
I’ve tried to make it as user-friendly as possible, with dropdowns, checkboxes and filters, and safe so the database doesn’t get obliterated in one click.  

- **Filters** are up top  
- **Sheet** is underneath

**How to edit the sheet**: you must click on the **enable editing** button, then hit **Save** afterwards. 
I've added a function that allows you to see when you are **IN** 🟢, or **OUT** of edit mode 🔴. If you are just navigating, I'd recommend you stay out of it. 
(You can also add a row, delete one, enter view mode and save as file at the top right of the table sheet) 
            
**How to make sure you're looking at the latest data**: Use the **reload** 🔄 button to pull in the latest Database edits back into the app.

---

The whole point of this app is to make everyone’s life easier, but it only works if you keep it **up to date**!  
So please don’t hesitate to make changes (that’s why there are edit buttons everywhere), and **don’t forget to save** 😊

If you have any questions, login issues, bugs to report, or feature suggestions/requests, ping me on Teams (Tanguy Moncler) or email **tanguy.moncler@tpicap.com**.

Have fun navigating 🥷
""")