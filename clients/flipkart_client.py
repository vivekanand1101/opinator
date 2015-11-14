from requests import post
import json
payload = {'product_id': 'xyz', 'website_name': 'flipkartcom', 'url': 'http://www.flipkart.com/samsung-galaxy-j7/p/itmeafbfjhsydbpw?pid=MOBE93GWSMGZHFSK'}
r = post("http://127.0.0.1:5000", json.dumps(payload), headers={'Content-Type': 'application/json'})
print r.text