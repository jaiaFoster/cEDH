"""Read six public deck/primer endpoints once each, without auth or bypass.
Raw responses stay local; commit factual deck lists/metadata and our summaries only.
"""
import gzip,json,pathlib,time,requests
HERE=pathlib.Path(__file__).resolve().parent
SOURCES={'blue_farm':'7O1sCuIti0igU6Us_Jhadg','dawnwaker':'Ar6aYd7qVkK6GoFD4f9P4Q','najeela':'nLIqybqUQEqc6DUajd1Ewg','derevi':'RjBJjJhU6ESAcA_s8Y6_VQ','yuriko_tempo':'RM9tBCjdsEOUQQpleGI4Gw','yuriko_combo':'Lo9INgdoeEqeYrflZ7Mcpw'}
def fetch():
 out=HERE/'local_research';out.mkdir(exist_ok=True)
 for key,ident in SOURCES.items():
  url='https://api2.moxfield.com/v3/decks/all/'+ident;r=requests.get(url,headers={'User-Agent':'CommanderDoublesResearch/1.0 (noncommercial attribution research)','Accept':'application/json'},timeout=45)
  if r.status_code!=200:print(key,r.status_code);continue
  data=r.json();(out/(key+'.json.gz')).write_bytes(gzip.compress(r.content,mtime=0))
  print(key,len(r.content),list(data)[:40]);print(str({k:v for k,v in data.items() if k in ['name','createdAtUtc','lastUpdatedAtUtc','publicId','createdBy','mainboardCount','description','boards'] and k!='boards'})[:1200]);time.sleep(.15)
if __name__=='__main__':fetch()
