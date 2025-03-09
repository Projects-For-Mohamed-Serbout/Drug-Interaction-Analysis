## 🚀 Quick Setup Guide

If you'd like to quickly set up the project, follow this [**Step-by-Step Setup Guide**](#-how-to-set-up-the-project). This link will take you directly to the section of the README that explains how to clone the repository, create a virtual environment, install dependencies, and get started.

---

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

## 🔄 Work Phases

### **📌 1. State of the Art & Literature Review**
- Research existing **drug interaction databases** and **NLP applications in pharmacology**.
- Identify gaps and opportunities for improvement.

### **📌 2. Data Structure Design**
- Design database schemas for:
  - **MongoDB (JSON format)**
  - **Neo4j (Graph format)**

### **📌 3. Data Extraction & Transformation**
- Extract key fields from **XML data**.
- Apply **NLP techniques** to extract and categorize interaction data.
- Load data into **MongoDB & Neo4j**, ensuring data integrity.

### **📌 4. Query Development & Performance Testing**
- Develop key queries for pharmacological interactions.
- Compare **MongoDB vs Neo4j** in terms of speed, scalability, and efficiency.

### **📌 5. Comparative Analysis & Results Evaluation**
- Assess **database performance** in managing pharmacological data.
- Measure **NLP effectiveness** in extracting interaction insights.

### **📌 6. Documentation & Final Report**
- Compile project findings into a structured **Master’s Thesis document** with clear explanations and visuals.

---

## 🏗️ Tech Stack
- **Programming Language**: Python 🐍  
- **Databases**: MongoDB, Neo4j  
- **Data Processing**: NLP, Pandas  
- **Development Tools**: Git, Jupyter Notebook  

---

## 🚀 How to Set Up the Project

### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/YOUR-USERNAME/Drug_Interaction_Analysis.git
```
```sh
cd Drug_Interaction_Analysis
```

### **2️⃣ Set Up the Virtual Environment**
Create a virtual environment to keep the dependencies isolated and prevent conflicts with system-wide packages.

***On Windows:***

```sh
python -m venv env
```
```sh
.\env\Scripts\activate
```

***On macOS/Linux:***

```sh
python3 -m venv env
```
```sh
source env/bin/activate
```
### **3️⃣ Install Project Dependencies**

Once the virtual environment is activated, install all required libraries using this command:
```sh
pip install -r requirements.txt
```

### **4️⃣ Verify Installation**

To verify that the dependencies are correctly installed, you can check the installed packages:
```sh
pip freeze
```

### **5️⃣ Run the Project**

Now you're ready to start working on the project! You can run the Python scripts or start the development server as needed. For example:
```sh
python main.py
```

### **6️⃣ Deactivate the Virtual Environment**

When you're done working on the project, deactivate the virtual environment by running:
```sh
deactivate

```