import requests


api_key = "2d0207e8454155f8ce2e341cd7a8ea80f7294226c2eb4c78588f5069441e9919"
url = "https://www.virustotal.com/gui/home/search"
hash_md5 =  "44d88612fea8a8f36de82e1278abb02f"

headers = {
    "x-apikey": api_key
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    result = response.json()
    print(result["data"]["attributes"]["last_analysis_results"])
else:
    print("Error: ", response.status_code)