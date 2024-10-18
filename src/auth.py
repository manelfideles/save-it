import hashlib
import hmac
import os
import time
from datetime import datetime, timedelta

import jwt
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


class Authenticator:
    def __init__(self):
        self.correct_username = os.environ.get("ADMIN_USERNAME")
        self.correct_password_hash = os.environ.get("ADMIN_PASSWORD_HASH")
        self.jwt_secret = os.environ.get("JWT_SECRET")
        self.jwt_expiry_days = 30

        if not all(
            [self.correct_username, self.correct_password_hash, self.jwt_secret]
        ):
            raise ValueError("Authentication credentials not properly configured")

        # Initialize session state
        if "token" not in st.session_state:
            st.session_state.token = None

    def hash_password(self, password: str) -> str:
        """Create a hash of the password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, provided_password: str) -> bool:
        """Verify the provided password against stored hash"""
        provided_hash = self.hash_password(provided_password)
        return hmac.compare_digest(provided_hash, self.correct_password_hash)

    def create_token(self) -> str:
        """Create a JWT token"""
        expiry = datetime.utcnow() + timedelta(days=self.jwt_expiry_days)
        return jwt.encode(
            {"username": self.correct_username, "exp": expiry},
            self.jwt_secret,
            algorithm="HS256",
        )

    def verify_token(self, token: str) -> bool:
        """Verify the JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload["username"] == self.correct_username
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    def login(self) -> bool:
        """Handle the login process"""
        if st.session_state.token and self.verify_token(st.session_state.token):
            return True

        st.markdown(
            """
        <style>
            .auth-container {
                max-width: 400px;
                margin: 0 auto;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .stButton button {
                width: 100%;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <script>
            // Function to store token
            function storeToken(token) {
                localStorage.setItem('auth_token', token);
            }
            
            // Function to retrieve token
            function getStoredToken() {
                return localStorage.getItem('auth_token');
            }
            
            // Function to clear token
            function clearToken() {
                localStorage.removeItem('auth_token');
            }
            
            // Check for stored token on page load
            window.addEventListener('load', function() {
                const token = getStoredToken();
                if (token) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: token
                    }, '*');
                }
            });
        </script>
        """,
            unsafe_allow_html=True,
        )

        with st.container():
            st.header("Login")

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            remember_me = st.checkbox("Keep me logged in", value=True)

            if st.button("Login"):
                if username == self.correct_username and self.verify_password(password):
                    token = self.create_token()
                    st.session_state.token = token
                    if remember_me:
                        st.markdown(
                            f"""
                            <script>
                                storeToken('{token}');
                            </script>
                            """,
                            unsafe_allow_html=True,
                        )
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                    return False

        query_params = st.query_params
        if "token" in query_params:
            token = query_params["token"][0]
            if self.verify_token(token):
                st.session_state.token = token
                st.experimental_set_query_params()
                time.sleep(2)
                return True

        return False

    def check_authentication(self):
        """Main authentication check"""
        if not st.session_state.token or not self.verify_token(st.session_state.token):
            if not self.login():
                st.stop()

    def logout(self):
        """Handle logout"""
        if st.button("Logout"):
            st.session_state.token = None
            # Clear token from local storage
            st.markdown(
                """
                <script>
                    clearToken();
                </script>
                """,
                unsafe_allow_html=True,
            )
            st.rerun()
