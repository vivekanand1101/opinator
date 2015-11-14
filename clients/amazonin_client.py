from requests import post
import json
payload = {'product_id': 'B016UPKCGU', 'website_name': 'amazonIN', 'url': 'xyz'}
r = post("http://127.0.0.1:5000", json.dumps(payload), headers={'Content-Type': 'application/json'})
print r.text