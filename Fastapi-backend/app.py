from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pickle
import re
import socket
import requests
import ipaddress
import urllib
from urllib.parse import urlparse, urlencode
import urllib.request
import smtplib, time, hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd

# Import the feature extraction function from your script
from URL_Feature_Extraction import extract_features

app = FastAPI()

# Load the new XGBoost model saved as a pickle file
with open('xgboost_model.pkl', 'rb') as file:
    model = pickle.load(file)

class UrlData(BaseModel):
    urls: list[str]

@app.post("/collect", response_model=list[str])
async def collect_urls(data: UrlData):
    # Receive the collected URLs from the frontend
    collected_urls = data.urls
    # Extract features for each URL using the function from URL_Feature_Extraction.py
    features_list = [extract_features(url) for url in collected_urls]
    features_df = pd.DataFrame(features_list)
    # Predict phishing status using the new model
    # (Assuming the model returns 1 for phishing and 0 for legitimate)
    predictions = model.predict(features_df)
    # Return URLs that are classified as phishing (i.e. 1)
    res = [collected_urls[i] for i, pred in enumerate(predictions) if pred == 1]
    return res

@app.post("/collection", response_model=list[str])
async def collection_urls(data: UrlData):
    collected_urls = data.urls
    features_list = [extract_features(url) for url in collected_urls]
    features_df = pd.DataFrame(features_list)
    predictions = model.predict(features_df)
    res = [collected_urls[i] for i, pred in enumerate(predictions) if pred == 1]
    return res

@app.post("/process_url", response_model=list[str])
async def process_url(data: UrlData):
    URLS = data.urls
    url = URLS[0]
    val = []
    val.append(url)
    domain_name = getDomain(url)
    val.append(domain_name)
    ip_address = get_ip_address(domain_name)
    val.append(ip_address)
    location = get_location(ip_address)
    val.append(location)
    return val

def get_ip_address(domain):
    try:
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror:
        return None

def get_location(ip_address):
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            data = response.json()
            location = data.get('city', 'Unknown') + ', ' + data.get('region', 'Unknown') + ', ' + data.get('country', 'Unknown')
            return location
        else:
            return "Location not found"
    except Exception as e:
        return str(e)

def getDomain(url):
    domain = urlparse(url).netloc
    if re.match(r"^www\.", domain):
        domain = domain.replace("www.", "")
    return domain

@app.post("/post_mail", response_model=list[str])
async def post_mail(data: UrlData):
    temp = data.urls
    dom_data = []
    dom_data.append(temp[0])
    domain_name = getDomain(temp[0])
    dom_data.append(domain_name)
    ip_address = get_ip_address(domain_name)
    dom_data.append(ip_address)
    location = get_location(ip_address)
    dom_data.append(location)
    dom_data.append(is_website_running(domain_name))
    sender = "moulishwarvs@gmail.com"
    receiver = "selvadharsh1208@gmail.com"
    subject = "trial"
    message = f"""
            <html>
            <body>
                <h2>Website Information</h2>
                <table border="1">
                <tr>
                    <th>Attribute</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>URL</td>
                    <td>{dom_data[0]}</td>
                </tr>
                <tr>
                    <td>Domain Name</td>
                    <td>{dom_data[1]}</td>
                </tr>
                <tr>
                    <td>IP Address</td>
                    <td>{dom_data[2]}</td>
                </tr>
                <tr>
                    <td>Location</td>
                    <td>{dom_data[3]}</td>
                </tr>
                <tr>
                    <td>Uptime Status</td>
                    <td>{dom_data[4]}</td>
                </tr>
                </table>
            </body>
            </html>
    """
    send_email(sender, receiver, subject, message)
    return dom_data

def send_email(sender, receiver, subject, message):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.attach(MIMEText(message, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender, 'eoujdrtjlbwtyvvg')
    server.sendmail(sender, receiver, msg.as_string())
    server.quit()

def is_website_running(domain):
    try:
        url = "http://" + domain
        response = requests.get(url)
        if response.status_code == 200:
            return "Website is active"
    except Exception as e:
        print(e)
    return "Website is not active"
