from flask import Flask, request, send_file
from fpdf import FPDF
from datetime import datetime, timedelta
import random
import unicodedata
import io

app = Flask(__name__)

def sanitize(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

@app.route("/")
def index():
    return open("invoice_form.html").read()

@app.route("/generate", methods=["POST"])
def generate():
    f = request.form
    invoice_number = f"INVOICE #{random.randint(100000, 999999)}"
    invoice_date = (datetime.today() - timedelta(days=random.randint(0, 30))).strftime("%B %d, %Y")
    subtotal = int(f["qty"]) * float(f["unit_price"])
    total = subtotal + float(f["shipping_cost"])

    supplier_address = f"{f['supplier_street']}, {f['supplier_city']}, {f['supplier_state']} {f['supplier_zip']}"
    buyer_address = [f["buyer_country"], f["buyer_street"], f"{f['buyer_city']}, {f['buyer_state_zip']}"]

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 16)
            self.cell(0, 10, f["supplier_name"], ln=True)
            self.set_font("Arial", "", 10)
            self.cell(0, 5, supplier_address, ln=True)
            self.ln(4)
            self.set_font("Arial", "B", 12)
            self.cell(0, 6, invoice_number, ln=True, align="R")
            self.set_font("Arial", "", 10)
            self.cell(0, 6, f"Invoice Date: {invoice_date}", ln=True, align="R")
            self.ln(10)

        def addresses(self):
            self.set_font("Arial", "B", 12)
            self.cell(100, 6, "BILL TO", ln=0)
            self.cell(0, 6, "SHIP TO", ln=1)
            self.set_font("Arial", "", 10)
            for b in buyer_address:
                self.cell(100, 6, b, ln=0)
                self.cell(0, 6, b, ln=1)
            self.ln(5)

        def methods(self):
            self.set_font("Arial", "B", 10)
            self.cell(60, 6, "Payment Method:", ln=0)
            self.cell(0, 6, "Shipping Method:", ln=1)
            self.set_font("Arial", "", 10)
            self.cell(60, 6, "Credit Card", ln=0)
            self.cell(0, 6, "Multiple Shipping - Flat", ln=1)
            self.ln(10)

        def item_table(self):
            self.set_fill_color(70, 130, 180)
            self.set_text_color(255)
            self.set_font("Arial", "B", 10)
            self.cell(30, 8, "ITEM", border=1, align="C", fill=True)
            self.cell(80, 8, "DESCRIPTION", border=1, align="C", fill=True)
            self.cell(20, 8, "QTY", border=1, align="C", fill=True)
            self.cell(30, 8, "UNIT", border=1, align="C", fill=True)
            self.cell(30, 8, "AMOUNT", border=1, align="C", fill=True)
            self.ln()

            self.set_text_color(0)
            self.set_font("Arial", "", 10)

            x = self.get_x()
            y = self.get_y()
            self.multi_cell(30, 8, f["item_code"], border=1)
            self.set_xy(x + 30, y)
            self.multi_cell(80, 8, f["item_desc"], border=1)
            h = self.get_y() - y
            self.set_xy(x + 110, y)
            self.cell(20, h, f["qty"], border=1, align="C")
            self.cell(30, h, f"${float(f['unit_price']):.2f}", border=1, align="R")
            self.cell(30, h, f"${subtotal:.2f}", border=1, align="R")
            self.ln()

        def totals(self):
            self.set_font("Arial", "B", 10)
            self.cell(160, 8, "SUBTOTAL", align="R")
            self.cell(30, 8, f"${subtotal:.2f}", border=1, align="R")
            self.ln()
            self.cell(160, 8, "SHIPPING & HANDLING", align="R")
            self.cell(30, 8, f"${float(f['shipping_cost']):.2f}", border=1, align="R")
            self.ln()
            self.set_fill_color(220, 240, 200)
            self.cell(160, 8, "TOTAL", align="R", fill=True)
            self.cell(30, 8, f"${total:.2f}", border=1, align="R", fill=True)

        def footer(self):
            self.set_y(-20)
            self.set_font("Arial", "I", 8)
            self.set_text_color(100)
            self.cell(0, 10, f"{f['supplier_name']} | {supplier_address}", align="C")

    pdf = PDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.addresses()
    pdf.methods()
    pdf.item_table()
    pdf.totals()

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="invoice.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)