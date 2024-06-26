import os
import streamlit as st
import pandas as pd
import numpy as np
import pickle
from scipy.sparse.linalg import svds
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from streamlit_option_menu import option_menu
from pathlib import Path
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from firebase_admin import auth
import json
import requests
from dotenv import load_dotenv
import base64
import plotly.express as px

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="STARBOOK",
    page_icon="book",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.header('Selamat Datang di STARBOOK 📚')

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("starbook-team23-163e5d9905db.json")
    firebase_admin.initialize_app(cred)

# Functions for Firebase Authentication
def sign_up_with_email_and_password(email, password, username=None, return_secure_token=True):
    try:
        rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": return_secure_token
        }
        if username:
            payload["displayName"] = username 
        payload = json.dumps(payload)
        r = requests.post(rest_api_url, params={"key": "AIzaSyApr-etDzcGcsVcmaw7R7rPxx3A09as7uw"}, data=payload)
        return r.json().get('email')
    except Exception as e:
        st.warning(f'Signup failed: {e}')

def sign_in_with_email_and_password(email=None, password=None, return_secure_token=True):
    rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    try:
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": return_secure_token
        }
        payload = json.dumps(payload)
        r = requests.post(rest_api_url, params={"key": "AIzaSyApr-etDzcGcsVcmaw7R7rPxx3A09as7uw"}, data=payload)
        data = r.json()
        user_info = {
            'email': data['email'],
            'username': data.get('displayName')
        }
        return user_info
    except Exception as e:
        st.warning(f'Signin failed: {e}')

def reset_password(email):
    try:
        rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode"
        payload = {
            "email": email,
            "requestType": "PASSWORD_RESET"
        }
        payload = json.dumps(payload)
        r = requests.post(rest_api_url, params={"key": "AIzaSyApr-etDzcGcsVcmaw7R7rPxx3A09as7uw"}, data=payload)
        if r.status_code == 200:
            return True, "Reset email sent"
        else:
            error_message = r.json().get('error', {}).get('message')
            return False, error_message
    except Exception as e:
        return False, str(e)


# Function to add background image
def add_bg_from_local(image_file, page):
    with open(image_file, "rb") as image:
        encoded_image = base64.b64encode(image.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{encoded_image});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            
        }}
        
        </style>
        """,
        unsafe_allow_html=True
    )

# File names for the background images
login_bg_image = 'login.png'  # Replace with your login background image
home_bg_image = 'joanna-kosinska-7ACuHoezUYk-unsplash.jpg'    # Replace with your home background image



# App initialization
def app():
    add_bg_from_local(login_bg_image, 'login')

    st.markdown(
            """
            <style>
            body {
                margin: 0; /* Remove default margin for body */
                padding: 0; /* Remove default padding for body */
                
            }

            .stApp {
                font-size: 50px; /* Increase font size for all text in the app */
            }
            .st-bw {
                   background-color: #000FF; /* White background for widgets */
            }
            .st-cq {
                background-color: #cccccc; /* Red background for chat input */
                border-radius: 10px; /* Add rounded corners */
                padding: 8px 12px; /* Add padding for input text */
                color: black; /* Set text color */
            }            
           .st-cx {
                background-color: light blue; /*background for chat messages */
            }
            .sidebar .block-container {
                   background-color: #f0f0f0; /* Light gray background for sidebar */
                   border-radius: 10px; /* Add rounded corners */
                   padding: 10px; /* Add some padding for spacing */
            }
            .top-right-image-container {
                   position: fixed;
                   top: 30px;
                   right: 0;
                   padding: 20px;
                   background-color: white; /* background for image container */
                   border-radius: 0 0 0 10px; /* Add rounded corners to bottom left */
               }
               .footer {
                   position: fixed;
                   bottom: 0;
                   width: 100%;
                   text-align: center;
                   padding: 10px;
                }
                .footer p {
                   margin: 0;
                }
               </style>
               """,
               unsafe_allow_html=True
           )
           
         # Footer
    st.markdown("""
               <div class="footer">
                   <p>Developed with ❤ by Team 23</p>
            </div> 
        """, unsafe_allow_html=True)
    

    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.useremail = ''


    def login():
        try:
            userinfo = sign_in_with_email_and_password(st.session_state.email_input, st.session_state.password_input)
            st.session_state.username = userinfo['username']
            st.session_state.useremail = userinfo['email']
            st.session_state.logged_in = True
        except:
            st.warning('Login Failed')

    def logout():
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.session_state.useremail = ''

    def forget_password():
        st.markdown('Lupa Password ⬇️')
        email = st.text_input('Email')
        if st.button('Send Reset Link'):
            success, message = reset_password(email)
            if success:
                st.success("Password reset email sent successfully.")
            else:
                st.warning(f"Password reset failed: {message}")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        main_page()
    else:
        choice = st.selectbox('Login/Signup', ['Login', 'Sign up'])
        email = st.text_input('Email Address')
        password = st.text_input('Password', type='password')
        st.session_state.email_input = email
        st.session_state.password_input = password

        if choice == 'Sign up':
            username = st.text_input("Enter your username")
            if st.button('Create my account'):
                user = sign_up_with_email_and_password(email=email, password=password, username=username)
                st.success('Account created successfully!')
                st.markdown('Login with E-mail and password')
                st.balloons()
        else:
            st.button('Login', on_click=login)
            forget_password()

        if st.session_state.logged_in:
            st.text('Name: ' + st.session_state.username)
            st.text('Email: ' + st.session_state.useremail)
            st.button('Sign out', on_click=logout)

    # Tambahkan kode aplikasi Streamlit Anda di sini
def main_page():
    add_bg_from_local(home_bg_image, 'home')
    with st.sidebar:
        selected = option_menu(
        menu_title="Menu Utama",  # required
        options=["Home", "Latar Belakang", "Unique Value", "Buku Untuk Kamu", "Profil Pengembang"],
        icons=['house-fill', 'tags', 'slack', 'bookmark-star', 'stars'],
            menu_icon='book',
            default_index=0,
            styles={
                "container": {"padding": "5!important", "background-color": 'black'},
                "icon": {"color": "white", "font-size": "23px"},
                "nav-link": {"color": "white", "font-size": "20px", "text-align": "left", "margin": "0px", "--hover-color": "blue"},
                "nav-link-selected": {"background-color": "#02ab21"},
            }
        )
    
    if selected == "Home":
        st.markdown("""
               <div style='display: flex; align-items: center; gap: 1px; margin-top: -30px;''>
                   <h2 style='margin: 0;'>A Book Recommendation System</h2>
            </div>
        """, unsafe_allow_html=True) 
    # Additional description
        st.write("""
            Website ini dirancang untuk membantu Anda menemukan rekomendasi buku terbaik sesuai dengan preferensi Anda. 
            Kami menyediakan berbagai macam rekomendasi dari berbagai genre dan kategori, sehingga Anda dapat dengan mudah 
            menemukan buku yang Anda sukai. Selamat menjelajahi dan semoga Anda menemukan banyak buku menarik untuk dibaca!
        """)
    elif selected == "Latar Belakang":
        st.title(f"Latar Belakang")
    # Additional description
        st.write("""
            Website ini hadir dengan latar belakang untuk memberikan rekomendasi buku yang sesuai dengan minat dan 
            kebutuhan pembaca. Dengan banyaknya pilihan buku yang tersedia, kami ingin membantu Anda menemukan 
            buku-buku yang berkualitas dan sesuai dengan selera Anda. Dengan memanfaatkan teknologi dan data, 
            kami dapat memberikan rekomendasi yang lebih personal dan relevan. Selamat menemukan buku-buku baru 
            yang menarik dan bermanfaat!
        """)   
    elif selected == "Unique Value":
        st.title(f"Unique Value")
        st.write("""
            Di website ini, kami memberikan nilai unik yang membedakan kami dari platform rekomendasi buku lainnya. Berikut adalah beberapa fitur unggulan kami:
                
            - **Personalisasi Rekomendasi:** Buku yang direkomendasikan sesuai dengan minat individu.
            - **Kemudahan Akses:** Pengguna dapat dengan mudah menemukan buku yang menarik tanpa harus mencari manual.
            - **Penemuan Baru:** Membantu pengguna menemukan buku dari genre atau penulis yang mungkin tidak mereka ketahui sebelumnya.
            """)
    elif selected == "Buku Untuk Kamu":

        st.markdown(
            """
            <style>
            body {
                background-color: #f0f0f0; /* Light gray background */
                margin: 0; /* Remove default margin for body */
                padding: 0; /* Remove default padding for body */
                
            }
            .st-bw {
                   background-color: #eeeeee; /* White background for widgets */
            }
            .st-cq {
                background-color: #cccccc; /* Red background for chat input */
                border-radius: 10px; /* Add rounded corners */
                padding: 8px 12px; /* Add padding for input text */
                color: black; /* Set text color */
            }            
            .st-cx {
                background-color: white; /* Black background for chat messages */
            }
                .sidebar .block-container {
                   background-color: #f0f0f0; /* Light gray background for sidebar */
                   border-radius: 10px; /* Add rounded corners */
                   padding: 10px; /* Add some padding for spacing */
                }
                .top-right-image-container {
                   position: fixed;
                   top: 30px;
                   right: 0;
                   padding: 20px;
                   background-color: white; /* White background for image container */
                   border-radius: 0 0 0 10px; /* Add rounded corners to bottom left */
               }
               .footer {
                   position: fixed;
                   bottom: 0;
                   width: 100%;
                   text-align: center;
                   padding: 10px;
                }
                .footer p {
                   margin: 0;
                }
               </style>
               """,
               unsafe_allow_html=True
           )
           
        st.markdown("""
               <div style='display: flex; align-items: center; gap: 15px;'>
                   <img src='data:image/jpeg;base64,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' width='50'>
                    <h1 style='margin: 0;'>Temukan Rekomendasi Buku Untuk Kamu</h1>
            </div>
        """, unsafe_allow_html=True)

         # Footer
        st.markdown("""
               <div class="footer">
                   <p>Developed with ❤ by Team 23</p>
            </div> 
        """, unsafe_allow_html=True)
        st.markdown(
             """
            <style>
            input[type=number] {
            background-color: #add8e6; /* Warna latar belakang biru muda */
            color: black; /* Warna teks hitam */
            border-radius: 5px; /* Sudut melengkung */
            padding: 5px; /* Padding */
            }
          </style>
        """,unsafe_allow_html=True) 
    
            # Create functions to open each social media app
        def open_app(app_name):
            st.experimental_set_query_params(page=app_name)
    
            # Fungsi untuk mendapatkan rekomendasi
        def get_svd_recommendations(user_id, preds_df, user_book_matrix, num_recommendations=5):
            try:
                # Mendapatkan prediksi rating untuk pengguna tertentu
                user_row_number = user_id
                   
                # Mendapatkan buku yang telah di-rating oleh pengguna
                sorted_user_predictions = preds_df.loc[user_row_number].sort_values(ascending=False)
                   
                # Mendapatkan data asli user yang sudah di-rating
                user_data = user_book_matrix.loc[user_row_number]
                   
                # Buku yang belum di-rating oleh user
                recommendations = pd.concat([user_data, sorted_user_predictions], axis=1)
                recommendations.columns = ['actual', 'score']
                recommendations = recommendations[recommendations['actual'] == 0]
                   
                # Mengambil top-n rekomendasi
                top_recommendations = recommendations.sort_values('score', ascending=False).head(num_recommendations)
           
                # Menghilangkan kolom 'actual'
                top_recommendations = top_recommendations[['score']]
                   
                return top_recommendations
            except KeyError:
                st.error("User ID tidak ditemukan.")
                return pd.DataFrame()
   
           # Fungsi utama untuk aplikasi Streamlit
        def main():
            # Memuat data dari file CSV
            df = pd.read_csv("df.csv")  # Pastikan file ini memiliki kolom 'user_id', 'book_id', 'rating', dan 'original_title'
               
            # Menghapus duplikat dengan mengagregasi rating yang ada
            df_ratings = df.groupby(['user_id', 'book_id']).agg({'rating': 'mean'}).reset_index()
            
            # Membuat matriks user-book
            user_book_matrix = df_ratings.pivot(index='user_id', columns='book_id', values='rating').fillna(0)
               
            # Melakukan SVD
            R = user_book_matrix.values
            user_ratings_mean = R.mean(axis=1)
            R_demeaned = R - user_ratings_mean.reshape(-1, 1)
                
            U, sigma, Vt = svds(R_demeaned, k=50)  # Anda dapat menyesuaikan nilai k sesuai kebutuhan
            sigma = np.diag(sigma)
               
            all_user_predicted_ratings = np.dot(np.dot(U, sigma), Vt) + user_ratings_mean.reshape(-1, 1)
            preds_df = pd.DataFrame(all_user_predicted_ratings, columns=user_book_matrix.columns, index=user_book_matrix.index)
            
    
    
            # Input user ID
            user_id = st.number_input("Masukkan User ID:", min_value=0, step=1)
            
            if st.button("Dapatkan Rekomendasi"):
                # Memanggil fungsi get_svd_recommendations
                recommendations = get_svd_recommendations(user_id, preds_df, user_book_matrix)
                   
                if not recommendations.empty:
                    # Mendapatkan daftar rekomendasi
                    List = recommendations.index.to_list()
                       
                    # Menggabungkan data buku untuk mendapatkan judul buku dari rekomendasi
                    temp = []
                    for book_id in List:    
                        result = df[df['book_id'] == book_id].iloc[0]
                        temp.append(result['original_title'])
                        
                    data = {
                        'book_id': List,
                        'title': temp   
                    }
                       
                    result = pd.DataFrame(data)
                    st.write("Rekomendasi Buku untuk User ID", user_id)
                    st.table(result)
                else:
                    st.write("Tidak ada rekomendasi yang tersedia untuk pengguna ini.")
                     
        if __name__ == "__main__":
            main()
                    
    if selected == "Profil Pengembang":
        st.title(f"Profil Pengembang😎")
    # Additional description
        st.write("""
            Berikut adalah profil dari tim pengembang yang berkontribusi dalam pembuatan website ini:

        1. **Ifanda Ariel Pradana Aji** as Project Manager & Programmer - Universitas PGRI Yogyakarta
        2. **Ilham Ramadhan** as Business Analyst  & Web Developer - Universitas Negeri Semarang
        3. **Thadeo Miftakhul Fauzi** as UI/UX Designer & Programmer - Universitas Islam Sultan Agung
        4. **Novita Nur Alifah** as Web Developer & Cybersecurity - Universitas Cendekia Abditama
        5. **Devi Koestri Elviani** - Universitas Jember
        """)
        # Appreciation section
        st.header("Ucapan Terima Kasih 🙏🏻")
        st.write("""
            Kami mengucapkan terima kasih kepada:

        - **Kampus Merdeka** - atas dukungan dan kesempatan yang diberikan dalam mengembangkan keterampilan kami.
        - **Skilvul** - atas platform pembelajaran yang luar biasa yang membantu kami dalam pengembangan website ini.
        - **IBM** - atas bimbingan dan sumber daya teknis yang diberikan untuk memastikan kualitas dan keandalan website ini.

        Tanpa dukungan dan kolaborasi dari mereka, proyek ini tidak akan mungkin terwujud. Terima kasih!
        """) 


app()
