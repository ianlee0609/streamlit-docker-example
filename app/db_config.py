import requests
current_external_ip = requests.get('https://api.ipify.org?format=json').json()['ip']
  
gspadmin_url =  "mysql+pymysql://datateam:77202880@10.240.240.240:6035/gspadmin"
superset_dashboard_url = "mysql+pymysql://datateam_pxc:77202880@10.240.240.240:6033/superset_dashboard"


if current_external_ip.startswith("220.135"):
    gspadmin_url = "mysql+pymysql://datateam:77202880@35.201.218.25:6035/gspadmin"
    superset_dashboard_url = "mysql+pymysql://datateam_pxc:77202880@35.201.218.25:6033/superset_dashboard"



