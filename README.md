# 🏥 Drug Interaction Data Engineering and Analysis

## 📌 Project Overview

In the field of health, data on medications and their possible interactions play a fundamental role in **patient safety** and **treatment efficiency**. However, the **complexity and volume** of these data pose significant challenges in terms of **management, storage, and analysis**.

This **Master's Thesis (TFM)** focuses on addressing these challenges using **NoSQL technologies** and **Natural Language Processing (NLP)** to improve drug interaction data handling.

## 📊 Data Source

- **CIMA (Centro de Información de Medicamentos)** Database:  
  👉 [CIMA Nomenclator](https://cima.aemps.es/cima/publico/nomenclator.html)  
  Managed by **AEMPS (Agencia Española de Medicamentos y Productos Sanitarios)**, this dataset contains **medication details in XML format**.

## 🎯 Objectives

- **Improve storage, querying, and analysis** of pharmacological interaction data.
- **Use NoSQL databases** (MongoDB & Neo4j) for efficient handling of semi-structured and unstructured data.
- **Apply NLP techniques** to extract valuable insights from textual descriptions in the dataset.
- **Provide a scalable solution** that benefits healthcare professionals, developers, and researchers.
---

## 🛠 Methodology
To ensure structured development, this project follows an **incremental and prototype-based methodology**:
1. **Incremental Development**  
   - Progressively develop modules: XML processing → NoSQL database setup → NLP integration.
2. **Iterative Prototyping**  
   - Each module undergoes functional testing before moving to the next stage.
3. **Continuous Evaluation**  
   - Regular performance and functionality checks to optimize results.
---
****
## 🏗️ Tech Stack

- **Backend**: Python 3.9+, FastAPI
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS
- **Databases**: MongoDB, Neo4j
- **Data Processing**: NLP, Pandas
- **Development Tools**: Git

---

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

- **Python 3.9+** ([Download Python](https://www.python.org/downloads/))
- **Node.js 18+** and **npm** ([Download Node.js](https://nodejs.org/))
- **Git** ([Download Git](https://git-scm.com/downloads))

> **Note**: This project uses **MongoDB Atlas** and **Neo4j Aura DB** (cloud databases). You do NOT need to install MongoDB or Neo4j locally. Database credentials will be provided by the project owner.

---

## 🚀 Setup Instructions

### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/YOUR-USERNAME/Drug-Interaction-Analysis.git
cd Drug-Interaction-Analysis
```

### **2️⃣ Get Database Credentials**

This project uses **MongoDB Atlas** and **Neo4j Aura DB** (cloud databases). You do **NOT** need to install or set up these databases yourself.

**Contact the project owner to obtain the following credentials:**

- MongoDB Atlas connection URI
- Neo4j Aura connection URI, username, and password

Once you receive the credentials, you'll add them to the `.env` file in the next step.

### **3️⃣ Backend Setup (drug-data-engine)**

#### **Navigate to Backend Directory**

```bash
cd drug-data-engine
```

#### **Create Virtual Environment**

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

> **Note**: After activation, you should see `(venv)` in your terminal prompt.

#### **Install Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### **Configure Environment Variables**

1. **Copy the sample environment file** to create your `.env` file:

```bash
cp .env.sample .env  # macOS/Linux
# or
copy .env.sample .env  # Windows
```

2. **Fill in the credentials** in the `.env` file:
   - **Contact the project owner** to obtain the database credentials
   - Add your MongoDB Atlas connection URI to `MONGODB_URI`
   - Add your Neo4j Aura URI to `NEO4J_URI`
   - Add your Neo4j username to `NEO4J_USER`
   - Add your Neo4j password to `NEO4J_PASSWORD`
   - Generate and add a secret key to `SECRET_KEY` (you can generate one using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

> **Important**: 
> - The `.env.sample` file is a template - **do not** put your actual credentials in it
> - **Never commit the `.env` file to version control!** It contains sensitive credentials
> - Make sure all required fields are filled in before running the application

#### **Run the Backend Server**

Make sure you're in the `drug-data-engine/` directory and your virtual environment is activated:

```bash
uvicorn app.main:app --reload
```

The FastAPI server will start at: **http://localhost:8000**

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### **4️⃣ Frontend Setup (drug-data-ui)**

#### **Navigate to Frontend Directory**

Open a **new terminal window** (keep the backend running) and navigate to the frontend directory:

```bash
cd drug-data-ui
```

#### **Install Dependencies**

```bash
npm install
```

#### **Run the Development Server**

```bash
npm run dev
```

The Vite development server will start at: **http://localhost:5173**

> **Note**: The frontend is configured to connect to the backend API at `http://localhost:8000`. Make sure the backend is running before starting the frontend.

---

## 🎯 Running the Complete Project

To run the full application:

1. **Terminal 1 - Backend:**
   ```bash
   cd drug-data-engine
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   uvicorn app.main:app --reload
   ```

2. **Terminal 2 - Frontend:**
   ```bash
   cd drug-data-ui
   npm run dev
   ```

3. **Access the Application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## 📁 Project Structure

```
Drug-Interaction-Analysis/
├── data/                          # Data files (XML and CSV)
│   ├── convert-to-csv/           # Converted CSV files
│   └── *.xml                      # Original XML data files
├── drug-data-engine/              # Backend (FastAPI)
│   ├── app/
│   │   ├── api/                  # API routes
│   │   ├── core/                 # Configuration and database
│   │   ├── extractor/            # XML parsing and extraction
│   │   ├── loader/               # Database loaders
│   │   ├── schemas/              # Pydantic schemas
│   │   └── services/             # Business logic
│   ├── requirements.txt          # Python dependencies
│   ├── setup.py                  # Package setup
│   ├── .env.sample               # Environment variables template
│   └── .env                      # Environment variables (create from .env.sample)
├── drug-data-ui/                  # Frontend (React + Vite)
│   ├── src/
│   │   ├── api/                  # API client
│   │   ├── components/           # React components
│   │   ├── pages/                # Page components
│   │   └── ...
│   ├── package.json              # Node.js dependencies
│   └── vite.config.ts            # Vite configuration
└── README.md                      # This file
```

---

## 🔧 Additional Commands

### **Backend Commands**

```bash
# Run with specific host and port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests (if available)
pytest

# Format code
black .
isort .

# Lint code
flake8 .
```

### **Frontend Commands**

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

---
****
## 👤 Author

**Mohamed Serbout**  
Email: m.serbout7@outlook.com

---

## 📄 License

This project is part of a Master's Thesis (TFM) and is for educational/research purposes.

---

## 🤝 Contributing

This is a Master's Thesis project. For questions or suggestions, please contact the author.
