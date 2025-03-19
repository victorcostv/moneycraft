from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
import pandas as pd
import re
import os

app = Flask(__name__, template_folder="moneycraft_web/templates")
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Dicionário de categorias
categories = {
    "Alimentação": ["Mc Donalds", "Burger King", "KFC", "Restaurante", "Lanchonete", "Pizza", "Subway"],
    "Transporte": ["Uber", "99 Táxi", "Posto", "Gasolina", "Rodoviária", "Metrô"],
    "Compras": ["Mercadolivre", "Shopee", "Magazine Luiza", "Americanas", "Casas Bahia"],
    "Saúde": ["Drogaria", "Raia", "Farmácia", "Consulta", "Hospital", "Clínica"],
    "Entretenimento": ["Netflix", "Spotify", "Cinema", "Ingresso", "Teatro"]
}

@app.route("/")
def home():
    return render_template("index.html", categories=categories)

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    if file:
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(pdf_path)
        excel_path = process_pdf(pdf_path)
        return send_file(excel_path, as_attachment=True)
    return "Erro ao processar o arquivo."

def process_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    transactions = []
    current_date = None
    pattern_date = re.compile(r"(\d{2} \w{3})")
    pattern_value = re.compile(r"R\$ -?\d+,\d{2}")
    
    def classify_expense(description):
        for category, keywords in categories.items():
            if any(keyword.lower() in description.lower() for keyword in keywords):
                return category
        return "Outros"
    
    for page in doc:
        lines = page.get_text("text").split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if pattern_date.fullmatch(line):
                current_date = line
            elif pattern_value.fullmatch(line) and current_date:
                value = float(line.replace("R$ ", "").replace(",", "."))
                description = lines[i - 1].strip()
                category = classify_expense(description)
                transactions.append([current_date, description, value, category])
            i += 1
    
    df = pd.DataFrame(transactions, columns=["Data", "Descrição", "Valor", "Categoria"])
    output_path = os.path.join(OUTPUT_FOLDER, "fatura_nubank.xlsx")
    df.to_excel(output_path, index=False)
    return output_path

if __name__ == "__main__":
    app.run(debug=True)
