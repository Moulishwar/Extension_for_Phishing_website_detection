'''from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import joblib
import pickle

app = FastAPI()

class UrlData(BaseModel):
    urls: list[str]

loaded_model = pickle.load(open('phishing.pkl', 'rb'))

app.post("/collect", response_model=list[str])
async def collect_urls(data: UrlData):
    # Receive the collected URLs from the extension
    collected_urls = data.urls

    # Process the URLs (you can replace this with your own logic)
    reskey = []
    resval = []
    res = []
    for url in collected_urls:
        # Your processing logic here
        index = url.find("//")
        if index != -1:
          modified_url = url[index + 2:]
          reskey.append(modified_url)
          print("A")
        else :
           reskey.append(url)
           print("B")
    resval = loaded_model.predict(reskey)
    for i in range(len(resval)):
        if resval[i] == "bad":
            res.append(reskey[i])
    print(type(res))
    return res
'''
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import joblib
import re
import socket
import requests
import ipaddress
import urllib
from urllib.parse import urlparse,urlencode
import urllib.request
import smtplib,time, hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI()
model = joblib.load("phishing.pkl")

class UrlData(BaseModel):
    urls: list[str]

@app.post("/collect", response_model=list[str])
async def collect_urls(data: UrlData):
    # Receive the collected URLs from the extension
    collected_urls = data.urls
    predictions = []
    features = []
    res = []
    for i in collected_urls:
        index = i.rfind('//')
        if index == -1:
            predictions.append(i)
        else :
            predictions.append(i[index+2:])
    features = model.predict(predictions)
    for i in range(len(features)):
        if(features[i]) == "bad":
            if predictions[i].rfind("yahoo") == -1 and predictions[i].rfind("google") == -1:
                res.append(collected_urls[i])
    print(res)
    return res

@app.post("/collection", response_model=list[str])
async def collect_urls(data: UrlData):
    # Receive the collected URLs from the extension
    collected_urls = data.urls
    predictions = []
    features = []
    res = []
    res.append(collected_urls[0])
    for i in collected_urls:
        index = i.rfind('//')
        if index == -1:
            predictions.append(i)
        else :
            predictions.append(i[index+2:])
    features = model.predict(predictions)
    for i in range(len(features)):
        if(features[i]) == "bad":
            if predictions[i].rfind("yahoo") == -1 and predictions[i].rfind("google") == -1:
                res.append(collected_urls[i])
    print(res)
    return res

@app.post("/process_url", response_model=list[str])
async def collect_urls(data: UrlData):
    # Receive the collected URLs from the extension
    URLS = data.urls
    url = URLS[0]
    val = []
    val.append(url)
    domin_name = getDomain(url)
    val.append(domin_name)
    ip_address = get_ip_address(domin_name)
    val.append(ip_address)
    location = get_location(ip_address)
    val.append(location)
    print(val)
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
  if re.match(r"^www.",domain):
    domain = domain.replace("www.","")
  return domain

@app.post("/post_mail",response_model=list[str])
async def post_mail(data: UrlData):
    temp = data.urls
    dom_data = []
    dom_data.append(temp[0])
    domin_name = getDomain(temp[0])
    dom_data.append(domin_name)
    ip_address = get_ip_address(domin_name)
    dom_data.append(ip_address)
    location = get_location(ip_address)
    dom_data.append(location)
    dom_data.append(is_website_running(domin_name))
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
    print(type(dom_data))
    return dom_data

    
def send_email(sender, receiver, subject, message):

  msg = MIMEMultipart()
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = receiver

  msg.attach(MIMEText(message, 'html'))

  server = smtplib.SMTP('smtp.gmail.com', 587)
  server.starttls()
  server.login(sender,'eoujdrtjlbwtyvvg')
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