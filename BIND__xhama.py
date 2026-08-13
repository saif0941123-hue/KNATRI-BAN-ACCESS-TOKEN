import requests, os, sys, json, time, urllib.parse, hashlib, urllib3, base64
from cfonts import say
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
xH={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"}
xGr="https://100067.connect.garena.com"
xMaSrY="100067"
def clear():
    os.system('cls' if os.name=='nt' else 'clear')
    say("MASRY",font="block",colors=["white","black"])
    print(base64.b64decode("Q1JFRElUIDogQE1DXzhH").decode())
    print(base64.b64decode("Q1JFRElUIDogQFlPNFJV").decode())
    print(base64.b64decode("Q0hBTk5FTCA6IEBVWERfMA==").decode())
def step(n,t,m): print(f"\n> [{n}/{t}] {m}")
def success(m): print(f"Dn => {m}")
def error(m): print(f"W9 => {m}")
def info(m): print(f"W8 => {m}")
def sec_to_str(s):
    d,h=divmod(s,86400); h,m=divmod(h,3600); m,s=divmod(m,60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"
def fmt_resp(r,title="API Response"):
    try:
        j=r.json(); c=j.get("result")
        if c==0: success(f"{title}: SUCCESS")
        elif c is not None: error(f"{title}: FAILED (Code: {c} | {j.get('error','')})")
        else: info(f"{title}: Completed")
    except:
        if '"result":0' in r.text.replace(" ",""): success(f"{title}: SUCCESS")
        else: error(f"{title}: Unrecognized response")
def api_get(endpoint,params): return requests.get(f"{xGr}{endpoint}",params=params,headers=xH,timeout=15)
def api_post(endpoint,data): return requests.post(f"{xGr}{endpoint}",data=data,headers=xH,timeout=15)
def player_info(token):
    try:
        r=requests.get(f"https://api-otrss.garena.com/support/callback/?access_token={token}",headers={"User-Agent":xH["User-Agent"]},allow_redirects=True,timeout=15)
        q=urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        return q.get("account_id",["Unknown"])[0], q.get("nickname",["Unknown"])[0], q.get("region",["Unknown"])[0]
    except: return None,None,None
def bind_info_data(token):
    uid,nick,region=player_info(token)
    print(f"  == Player: UID={uid}\n, Nick={nick}\n, Region={region}")
    try:
        r=api_get("/game/account_security/bind:get_bind_info",{"xMaSrY":xMaSrY,"access_token":token})
        if r.status_code==200:
            d=r.json(); email=d.get("email",""); to_be=d.get("email_to_be",""); cd=d.get("request_exec_countdown",0)
            print(f"    Current Email: {email or 'None'} | Pending: {to_be or 'None'}")
            if to_be: print(f"    Countdown: {sec_to_str(cd)}")
            print(f"    Result: {'SUCCESS' if d.get('result')==0 else 'FAILED (Code: '+str(d.get('result'))+')'}")
            summary=""
            if not email and to_be: summary=f"Pending email confirmation: {to_be} - Confirms in: {sec_to_str(cd)}"
            elif email and not to_be: summary=f"Email confirmed: {email}"
            elif not email and not to_be: summary="No recovery email set"
            if summary: print(f"    Summary: {summary}")
        else: error(f"API Error {r.status_code}")
    except Exception as e: error(str(e))
def send_otp(email,token): return api_post("/game/account_security/bind:send_otp",{"email":email,"locale":"en_PK","region":"PK","xMaSrY":xMaSrY,"access_token":token})
def verify_otp_get_verifier(email,otp,token):
    r=api_post("/game/account_security/bind:verify_otp",{"email":email,"xMaSrY":xMaSrY,"access_token":token,"code":otp,"otp":otp,"type":"1"})
    fmt_resp(r,"Verify OTP")
    try: return r.json().get("verifier_token")
    except: return None
def verify_identity(email,token,otp=None,security_code=None):
    data={"email":email,"xMaSrY":xMaSrY,"access_token":token}
    if otp: data["otp"]=otp
    elif security_code: data["secondary_password"]=hashlib.sha256(security_code.encode()).hexdigest()
    r=api_post("/game/account_security/bind:verify_identity",data)
    fmt_resp(r,"Verify Identity")
    try: return r.json().get("identity_token")
    except: return None
def check_bind():
    clear(); print("=> CHECK BIND INFO"); bind_info_data(input(">> Enter Access Token : ")); input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
def bind_email():
    clear(); print("=> BIND EMAIL"); token=input(">> Enter Access Token : "); bind_info_data(token)
    email=input(">> Enter Email to bind : ")
    step(1,3,f"Sending OTP to {email}..."); fmt_resp(send_otp(email,token),"Send OTP")
    otp=input(">> Enter OTP : ")
    step(2,3,"Verifying OTP..."); verifier=verify_otp_get_verifier(email,otp,token)
    if not verifier: error("Verifier token missing"); return input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
    sec=input(">> Set 6-digit Security Code : ")
    step(3,3,"Creating bind..."); fmt_resp(api_post("/game/account_security/bind:create_bind_request",{"email":email,"xMaSrY":xMaSrY,"access_token":token,"verifier_token":verifier,"secondary_password":sec}),"Bind Request")
    input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
def unbind_email():
    clear(); print("=> UNBIND EMAIL\n [1] VIA OTP\n [2] VIA SECURITY CODE\n [0] CANCEL"); c=input(">> Select : ")
    if c not in ("1","2"): return
    token=input(">> Enter Access Token : "); bind_info_data(token)
    try: email=api_get("/game/account_security/bind:get_bind_info",{"xMaSrY":xMaSrY,"access_token":token}).json().get("email","")
    except: email=""
    if not email: error("No bound email!"); return input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
    identity=None
    if c=="1":
        step(1,3,f"Sending OTP to {email}..."); fmt_resp(send_otp(email,token),"Send OTP")
        otp=input(">> Enter OTP : ")
        step(2,3,"Verifying Identity..."); identity=verify_identity(email,token,otp=otp)
        total=3; st=3
    else:
        sec=input(">> Enter 6-digit Security Code : ")
        step(1,2,"Verifying Identity..."); identity=verify_identity(email,token,security_code=sec)
        total=2; st=2
    if not identity: error("Identity verification failed!"); return input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
    step(st,total,"Creating Unbind..."); fmt_resp(api_post("/game/account_security/bind:create_unbind_request",{"xMaSrY":xMaSrY,"access_token":token,"identity_token":identity}),"Unbind")
    input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
def change_bind():
    clear(); print("=> CHANGE BIND EMAIL\n [1] VIA OTP\n [2] VIA SECURITY CODE\n [0] CANCEL"); c=input(">> Select : ")
    if c not in ("1","2"): return
    token=input(">> Enter Access Token : "); bind_info_data(token)
    try: old=api_get("/game/account_security/bind:get_bind_info",{"xMaSrY":xMaSrY,"access_token":token}).json().get("email","")
    except: old=""
    if not old: error("No bound email!"); return input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
    identity=None; steps=5 if c=="1" else 4; cur=1
    if c=="1":
        step(cur,steps,f"Sending OTP to {old}..."); fmt_resp(send_otp(old,token),"Send OTP"); cur+=1
        otp_old=input(">> Enter OTP : ")
        step(cur,steps,"Verifying Identity..."); identity=verify_identity(old,token,otp=otp_old); cur+=1
    else:
        sec=input(">> Enter 6-digit Security Code : ")
        step(cur,steps,"Verifying Identity..."); identity=verify_identity(old,token,security_code=sec); cur+=1
    if not identity: error("Identity verification failed!"); return input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
    new_email=input(">> Enter New Email : ")
    step(cur,steps,f"Sending OTP to {new_email}..."); fmt_resp(send_otp(new_email,token),"Send OTP"); cur+=1
    otp_new=input(">> Enter OTP : ")
    step(cur,steps,"Verifying New Email..."); verifier=verify_otp_get_verifier(new_email,otp_new,token); cur+=1
    if not verifier: error("Verifier token missing"); return input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
    step(cur,steps,"Creating Rebind..."); fmt_resp(api_post("/game/account_security/bind:create_rebind_request",{"identity_token":identity,"email":new_email,"xMaSrY":xMaSrY,"verifier_token":verifier,"access_token":token}),"Rebind")
    input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
def cancel_bind():
    clear(); print("=> CANCEL BIND"); token=input(">> Enter Access Token : "); bind_info_data(token)
    step(1,1,"Cancelling..."); fmt_resp(api_post("/game/account_security/bind:cancel_request",{"xMaSrY":xMaSrY,"access_token":token}),"Cancel")
    input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
def revoke():
    clear(); print("=> REVOKE ACCESS TOKEN"); token=input(">> Enter Access Token : ")
    uid,nick,region=player_info(token)
    if uid is None: error("Token invalid or expired"); return input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
    success("Token Valid!"); step(2,2,"Revoking...")
    refresh="1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    r=requests.get(f"{xGr}/oauth/logout?access_token={token}&refresh_token={refresh}",headers=xH,timeout=15)
    if r.status_code==200 and "error" not in r.text:
        print(f" Nickname    : {nick}\n Account ID  : {uid}\n Region      : {region}\n Status      : Logged Out & Revoked")
    else: error("Revoke failed")
    input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
def check_bound_platforms():
    clear(); print("=> PLATFORM BIND INFO"); token=input(">> Enter Access Token : ")
    PLATFORMS={1:"Garena",3:"Facebook",4:"Guest",5:"VK",6:"Huawei",7:"Apple",8:"Google",10:"GameCenter/Line",11:"X",13:"Apple ID",28:"Line",35:"TikTok"}
    try:
        r=api_get("/bind/app/platform/info/get",{"access_token":token}); d=r.json()
        print(" BOUND ACCOUNTS:"); _=[print(f"   - {PLATFORMS.get(p,f'Unknown({p})')}") for p in d.get("bounded_accounts",[])]
        if not d.get("bounded_accounts"): print("   - None")
        print("\n AVAILABLE:"); _=[print(f"   - {PLATFORMS.get(p,f'Unknown({p})')}") for p in d.get("available_platforms",[])]
        if not d.get("available_platforms"): print("   - None")
    except Exception as e: error(str(e))
    input("\n◈"+"═"*58+"◈\n>> Press Enter to return to menu : ")
def main_menu():
    menu={"1":check_bind,"2":bind_email,"3":unbind_email,"4":change_bind,"5":cancel_bind,"6":revoke,"7":check_bound_platforms}
    while True:
        clear(); print("\n\n [1] CHECK BIND INFO\n [2] BIND EMAIL\n [3] UNBIND EMAIL\n [4] CHANGE BIND EMAIL\n [5] CANCEL BIND\n [6] REVOKE TOKEN\n [7] CHECK BOUND ACCOUNTS\n [0] EXIT\n\n")
        c=input(">> Select : ")
        if c in menu: menu[c]()
        elif c=="0": print("\nBye!"); sys.exit(0)
        else: print("Invalid!"); time.sleep(1)
if __name__=="__main__":
    try: main_menu()
    except KeyboardInterrupt: print("\nBye!"); sys.exit(0)
    except Exception as e: print(f"\nError: {e}"); input(">> Press Enter to exit : ")