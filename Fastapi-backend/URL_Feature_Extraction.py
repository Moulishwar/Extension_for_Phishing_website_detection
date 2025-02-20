import re
from urllib.parse import urlparse
from datetime import datetime
import whois           # for WHOIS lookups
import requests        # for HTTP requests (to check favicon)
import pandas as pd
import urllib
import urllib.request
from bs4 import BeautifulSoup
import ipaddress
import tldextract   
import requests

# 1. IP Address in URL: True if the hostname is a valid IP address.
def Ip_in_Domain(url):
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    try:
        ipaddress.ip_address(hostname)
        return 1
    except ValueError:
         return 0

#2. URL Length:
def getLength(url):#
    if len(url) < 50:
        length = 0            
    else:
        length = 1            
    return length

# 3.Checks the presence of @ in URL (Have_At)
def haveAtSign(url):
  if "@" in url:
    at = 1    
  else:
    at = 0    
  return at

# 4. Redirection using '//' in the path (beyond the protocol delimiter).
def check_double_slash(url):
    parsed = urlparse(url)
    # If the path contains '//' it's suspicious.
    return 1 if '//' in parsed.path else 0

# 5. Hyphen in Domain: Returns 1 if the hostname contains a hyphen.
def check_hyphen(url):
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return 1 if '-' in hostname else 0

# 6. Subdomain Count: Returns the count of subdomain parts.
def count_subdomains(url):
    ext = tldextract.extract(url)
    if ext.subdomain:
        # Count the number of parts in the subdomain.
        return len(ext.subdomain.split('.'))
    else:
        return 0

# 7. Use of HTTPS Protocol.
def uses_https(url):
    parsed = urlparse(url)
    return 1 if parsed.scheme.lower() == "https" else 0

# 8. Checking for Shortening Services in URL (Tiny_URL)
def tinyURL(url):
    shortening_services = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|" \
                      r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|" \
                      r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|" \
                      r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|" \
                      r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|" \
                      r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|" \
                      r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|" \
                      r"tr\.im|link\.zip\.net"
    match=re.search(shortening_services,url)
    if match:
        return 1
    else:
        return 0

# 9. Domain Age: Returns the age of the domain in days,
def domain_age(url, threshold=180):
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    try:
        domain_info = whois.whois(hostname)
        creation_date = domain_info.creation_date
        # Handle if creation_date is returned as a list
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        # Check if creation_date is valid and a datetime object.
        if creation_date and isinstance(creation_date, datetime):
            age_days = (datetime.now() - creation_date).days
            return 0 if age_days >= threshold else 1
        else:
            return 1
    except Exception:
        return 1

# 10 Web Traffic: Returns the web traffic of the domain.
def web_traffic(url):
  try:
    #Filling the whitespaces in the URL if any
    url = urllib.parse.quote(url)
    rank = BeautifulSoup(urllib.request.urlopen("http://data.alexa.com/data?cli=10&dat=s&url=" + url).read(), "xml").find(
        "REACH")['RANK']
    rank = int(rank)
  except TypeError:
        return 1
  if rank <100000:
    return 1
  else:
    return 0
  
# 11.DNS Record availability (DNS_Record)
def dns_record(url):
    dns = 0
    try:
        domain_name = whois.whois(urlparse(url).netloc)
    except:
        dns = 1
    return dns

# 12.Checks the number of forwardings (Web_Forwards)    
def forwarding(url):
    try:
        response = requests.get(url)
    except:
        response = ""
    if response == "":
        return 1
    else:
        if len(response.history) <= 2:
            return 0
        else:
            return 1
        

# 13. IFrame Redirection (iFrame)
def iframe(url):
    try:
        response = requests.get(url)
    except:
        response = ""
    if response == "":
        return 1
    else:
        if re.findall(r"[<iframe>|<frameBorder>]", response.text):
            return 0
        else:
            return 1


# Helper function to extract all features for a given URL
def extract_features(url):
    return {
        "IP_in_Domain": Ip_in_Domain(url),
        "URL_Length": getLength(url),
        "Have_at_Sign": haveAtSign(url),
        "Redirection": check_double_slash(url),
        "Hyphen": check_hyphen(url),
        "URL_Depth": count_subdomains(url),
        "HTTPS/HTTP": uses_https(url),
        "Tiny_URL": tinyURL(url),
        "Domain_Age": domain_age(url),
        "Web_Traffic": web_traffic(url),
        "DNS_Record": dns_record(url),
        "Forwarding": forwarding(url),
        "iFrame": iframe(url)
    }


l_df = pd.read_csv("/CyberProjects/Phish/Dataset/Legit_URL.csv")
p_df = pd.read_csv("/CyberProjects/Phish/Dataset/Phish_URL.csv")

phishurl = p_df.sample(n = 5000, random_state = 12).copy()
phishurl = phishurl.reset_index(drop=True)

legiturl = l_df.sample(n = 5000, random_state = 12).copy()
legiturl = legiturl.reset_index(drop=True)

phishurl['Label'] = 1
legiturl['Label'] = 0

# Combine the datasets
combined_df = pd.concat([phishurl, legiturl], ignore_index=True)

# Extract features for each URL and create a DataFrame of features
features_df = combined_df["url"].apply(lambda url: pd.Series(extract_features(url)))

# Concatenate the original data with the extracted features
combined_df = pd.concat([combined_df, features_df], axis=1)

# Save the final DataFrame to a CSV file for later use
combined_df.to_csv("/CyberProjects/Phish/Dataset/Final_URL.csv", index=False)
