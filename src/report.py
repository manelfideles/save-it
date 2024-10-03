import io
import os
import smtplib
import time
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import schedule
from reportlab.pdfgen import canvas

from supabase_client import SupabaseClient

# Email configuration
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")


def generate_report(supabase_client: SupabaseClient):
    data = supabase_client.load_data()

    # Create PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, f"Expense Report - {datetime.now().strftime('%Y-%m-%d')}")

    # Add more report content here

    c.save()
    buffer.seek(0)
    return buffer


def send_email_report():
    pdf_buffer = generate_report()

    msg = MIMEMultipart()
    msg["Subject"] = f"Weekly Expense Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    text_part = MIMEText("Please find attached your weekly expense report.", "plain")
    pdf_part = MIMEApplication(pdf_buffer.getvalue(), Name="expense_report.pdf")
    pdf_part["Content-Disposition"] = 'attachment; filename="expense_report.pdf"'

    msg.attach(text_part)
    msg.attach(pdf_part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


# def schedule_reports():
#     schedule.every().sunday.do(send_email_report)
#     while True:
#         schedule.run_pending()
#         time.sleep(1)
