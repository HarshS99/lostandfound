<h1 align="center">🕵️‍♂️ LostAndFound</h1> <p align="center"> <b>AI-powered Lost & Found Item Management Tool</b><br> Report lost/found items, search efficiently, and reconnect owners using a <b>simple dashboard</b>. </p> <p align="center"> <a href="https://streamlit.io" target="_blank"> <img src="https://img.shields.io/badge/Framework-Streamlit-FF4B4B?style=for-the-badge" alt="Streamlit"/> </a> <a href="https://www.python.org" target="_blank"> <img src="https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge" alt="Python"/> </a> <a href="https://www.sqlite.org/index.html" target="_blank"> <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge" alt="SQLite"/> </a> </p>
🌟 Why This Project?

Lost & Found situations happen every day, and finding the right owner or reporting items can be tedious.
This project turns manual tracking into quick, searchable management:

🔹 Report Items → Add lost or found items with details & images

🔹 Search Easily → Filter by category, location, or keywords

🔹 Match Owners → Quickly find potential matches

🔹 Dashboard Insights → View all items in one place

✨ Features

📝 Report Lost Item → Add lost item with description, location, date

🗂 Report Found Item → Add found item and match with existing lost items

🔍 Search & Filter → Category, location, keywords

📊 Dashboard → Summary stats & CSV export

🖼️ Visual Demo
<p align="center"> <img src="assets/demo.gif" alt="demo" width="600"/> </p>
🛠 Tech Stack

Frontend & Dashboard: Streamlit

Backend: Python 3.10+

Database: SQLite / PostgreSQL

Utilities: Pandas, Requests, PDF/Docx support (optional)

📂 Project Structure
LostAndFound
|
├── app.py            # Streamlit UI (dashboard + interactions)
├── database.py       # DB operations (SQLite / PostgreSQL)
├── models.py         # Item models & matching logic
├── utils.py          # Helper functions
├── assets/           # Images, UI elements, screenshots
├── requirements.txt  # Dependencies
└── README.md         # Documentation

⚙️ Setup & Installation
1️⃣ Clone the Repository
git clone https://github.com/username/LostAndFound.git
cd LostAndFound

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Run the App
streamlit run app.py


Visit 👉 http://localhost:8501

Typical Workflow

Add a lost or found item

Search for items by category/location/keyword

View potential matches and contact owners

Export data to CSV if needed

🤝 Contributing

Contributions are welcome 💡

Fork the repo

Create a feature branch

Submit a PR 🚀

📜 License

MIT License © 2025 — Built with ❤️ using Python & Streamlit
