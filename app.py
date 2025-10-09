import os
import streamlit as st
from PIL import Image
import io
from agents import coordinator, fetch_all_items, init_db
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv("api.env")

# ---------- Ensure DB exists ----------
init_db()

# ---------- Streamlit page config ----------
st.set_page_config(
    page_title="Lost & Found 2.0", 
    layout="wide",
    page_icon="🔎"
)

# ---------- Custom CSS for better styling ----------
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem !important;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem !important;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .match-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-notification {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .info-notification {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #bee5eb;
    }
    .upload-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.image("./assets/openai-text.png", width=150)
    Openai_key = st.text_input("OpenAI API key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
    twilio_key = st.text_input("TWILIO_ACCOUNT_SID", value=os.getenv("TWILIO_ACCOUNT_SID", ""), type="password")

    if st.button("💾 Save Keys"):
        st.session_state["OPENAI_API_KEY"] = Openai_key
        st.session_state["TWILIO_ACCOUNT_SID"] = twilio_key
    if Openai_key or twilio_key:
        st.success("Keys saved for this session")

with st.sidebar:
    st.markdown("## 🎯 Navigation")
    
    page = st.radio(
        "Go to:",
        ["🏠 Home", "📤 Report Item", "📋 Recent Items", "ℹ️ About"],
        key="navigation"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    
    # Quick stats in sidebar
    items = fetch_all_items()
    lost_count = len([item for item in items if item['type'] == 'lost'])
    found_count = len([item for item in items if item['type'] == 'found'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Lost Items", lost_count)
    with col2:
        st.metric("Found Items", found_count)
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.info("""
    - Upload clear, well-lit images
    - Provide detailed descriptions
    - Include multiple angles if possible
    - Keep your contact info updated
    """)

# ---------- Home Page ----------
if page == "🏠 Home":
    st.markdown('<div class="main-header">🔎 Lost & Found 2.0</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Item Recovery System</div>', unsafe_allow_html=True)
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Welcome to Lost & Found 2.0
        
        Our intelligent system uses **Camel AI + OpenAI + Twilio** to help reunite lost items with their owners.
        
        **How it works:**
        1. 📸 **Upload** an image of lost/found item
        2. 🔍 **AI Analysis** extracts features and descriptions
        3. 🤝 **Smart Matching** finds potential matches
        4. 📱 **Instant Notifications** via SMS/WhatsApp
        
        **Get started by reporting an item in the 'Report Item' section!**
        """)
    
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/2997/2997896.png", width=200)
    
    # Features grid
    st.markdown("---")
    st.markdown("### 🚀 Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h4>🖼️ Image Analysis</h4>
            <p>Advanced vision to understand item details</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h4>🔗 Smart Matching</h4>
            <p>PHASH + text embedding for accurate matches</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h4>📞 Multi-Channel Alerts</h4>
            <p>SMS & CALL , WhatsApp notifications</p>
        </div>
        """, unsafe_allow_html=True)

# ---------- Report Item Page ----------
elif page == "📤 Report Item":
    st.markdown("## 📤 Report Lost or Found Item")
    
    # Upload section with better styling
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown("### 📸 Upload Item Details")
        st.markdown("Fill in the form below to report a lost or found item")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Upload Form
    with st.form("upload_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Item Information")
            item_type = st.selectbox(
                "Item Type *", 
                ["lost", "found"],
                help="Select 'lost' if you lost an item, 'found' if you found someone else's item"
            )
            title = st.text_input(
                "Title *", 
                placeholder="e.g., 'Black Leather Wallet', 'iPhone 13 Pro'",
                help="Clear, descriptive title helps in better matching"
            )
            description = st.text_area(
                "Description", 
                placeholder="Provide additional details like brand, color, distinctive features, location found/lost, etc.",
                height=100
            )
        
        with col2:
            st.subheader("Contact & Image")
            # Pre-fill your verified number for testing
            owner_contact = st.text_input(
                "Your phone number",
                value="",  #ENTER A NUMBER 
                help="Twilio verified number for testing notifications"
            )
            
            st.markdown("---")
            uploaded_file = st.file_uploader(
                "Upload Image *", 
                type=["jpg", "jpeg", "png"],
                help="Clear images work best for matching"
            )
            
            if uploaded_file:
                st.image(uploaded_file, caption="Preview", use_container_width=True)
        
        st.markdown("**Note:** Fields marked with * are required")
        
        submitted = st.form_submit_button(
            "🚀 Submit & Search for Matches", 
            use_container_width=True
        )

    # ---------- Form Submission ----------
    if submitted:
        if not uploaded_file:
            st.error("❌ Please upload an image to continue.")
        elif not title.strip():
            st.error("❌ Please enter a title for the item.")
        else:
            img_bytes = uploaded_file.read()
            pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            
            with st.spinner("🔍 Processing with multi-agent pipeline..."):
                try:
                    # Coordinator multi-agent call
                    res = coordinator.run_pipeline(img_bytes, title, description, item_type, owner_contact)
                except json.JSONDecodeError:
                    st.error("Error decoding response from agent. Please try again.")
                    res = {}

            if res.get("error"):
                st.error(f"❌ {res['error']}")
            else:
                matches = res.get("matches", [])
                
                # Results section
                st.markdown("---")
                st.markdown("## 📊 Results")
                
                if not matches:
                    st.markdown('<div class="info-notification">ℹ️ No matches found yet. Item stored in database; system will automatically match with future uploads.</div>', unsafe_allow_html=True)
                else:
                    st.success(f"🎉 Found {len(matches)} potential match(es)!")
                    
                    for i, m in enumerate(matches, 1):
                        itm = m["match"]
                        
                        with st.container():
                            st.markdown(f'<div class="match-card">', unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"### Match #{i}: {itm.get('title')}")
                                st.markdown(f"**Description:** {itm.get('description', 'No description')}")
                                st.markdown(f"**Match Score:** `{itm.get('score', 0.0):.3f}`")
                                
                                reasons = itm.get('reasons', [])
                                if reasons:
                                    st.markdown("**Matching Reasons:**")
                                    for reason in reasons:
                                        st.markdown(f"- {reason}")
                            
                            with col2:
                                st.markdown(f"**Item ID:** `{itm.get('id')}`")
                                st.markdown(f"**Type:** `{itm.get('type')}`")
                                st.markdown(f"**Contact:** {m.get('masked_contact', 'Not available')}")
                            
                            # Notification status
                            notif_status = m.get("notif_status", {})
                            if notif_status:
                                st.markdown("**Notifications Sent:**")
                                notif_cols = st.columns(len(notif_status))
                                for idx, (channel, status) in enumerate(notif_status.items()):
                                    with notif_cols[idx]:
                                        if "success" in status.lower():
                                            st.success(f"{channel.upper()} ✅")
                                        else:
                                            st.error(f"{channel.upper()} ❌")
                                        st.caption(status)
                            
                            st.markdown('</div>', unsafe_allow_html=True)

# ---------- Recent Items Page ----------
elif page == "📋 Recent Items":
    st.markdown("## 📋 Recent Items")
    
    items = fetch_all_items()
    recent_items = items[-20:][::-1]  
    
    if not recent_items:
        st.info("No items found in the database.")
    else:
        search_term = st.text_input("🔍 Search items...", placeholder="Search by title, description, or type")
        
        # Filter items based on search
        if search_term:
            filtered_items = [
                item for item in recent_items 
                if search_term.lower() in item['title'].lower() 
                or search_term.lower() in str(item.get('description', '')).lower()
                or search_term.lower() in item['type'].lower()
            ]
        else:
            filtered_items = recent_items
        
        st.markdown(f"**Showing {len(filtered_items)} items**")
        
        for item in filtered_items:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{item['title']}**")
                    if item.get('description'):
                        st.caption(item['description'])
                
                with col2:
                    st.write(f"**Type:**")
                    if item['type'] == 'lost':
                        st.error("LOST")
                    else:
                        st.success("FOUND")
                
                with col3:
                    st.write(f"**ID:**")
                    st.code(item['id'])
                
                with col4:
                    st.write(f"**Date:**")
                    st.caption(item['created_at'].split(' ')[0] if ' ' in item['created_at'] else item['created_at'])
                
                st.markdown("---")

# ---------- About Page ----------
elif page == "ℹ️ About":
    st.markdown("## ℹ️ About Lost & Found 2.0")
    
    st.markdown("""
    ### 🤖 Technology Stack
    
    This application uses cutting-edge AI technologies to help reunite lost items with their owners:
    
    - **Camel AI**: Multi-agent coordination for intelligent processing
    - **OpenAI**: Advanced image understanding and text analysis
    - **Twilio**: Multi-channel notifications (SMS + WhatsApp)
    - **Streamlit**: Modern web interface
    - **PHASH Algorithm**: Perceptual hashing for image similarity
    - **Text Embeddings**: Semantic matching of item descriptions
    
    ### 🔧 How It Works
    
    1. **Image Processing**: Uploaded images are analyzed for visual features
    2. **Feature Extraction**: Both visual (PHASH) and textual embeddings are created
    3. **Intelligent Matching**: AI agents compare against existing items
    4. **Notification System**: Automatic alerts to potential owners
    5. **Continuous Learning**: System improves with more data
    
    ### 📞 Contact & Support
    
    For technical support or questions about the system, please contact the development team.
    
    ---
    
    *Built with ❤️ using Streamlit and AI technologies*
    """)
    
    # Tech stack icons
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("**Camel AI**")
    with col2:
        st.markdown("**OpenAI**")
    with col3:
        st.markdown("**Twilio**")
    with col4:
        st.markdown("**Streamlit**")
    with col5:
        st.markdown("**Python**")
