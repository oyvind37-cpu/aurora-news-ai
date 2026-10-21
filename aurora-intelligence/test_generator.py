"""Run an isolated Workers AI test; never publish to the live app."""
import json, os, urllib.request, pathlib, sys
data=json.loads(pathlib.Path("news.json").read_text(encoding="utf-8"))
items=data.get("items",data.get("articles",[]))
if not isinstance(items,list): raise SystemExit("news.json items must be a list")
items=[{"title":x.get("title",""),"source":x.get("source",""),"url":x.get("url",""),"published":x.get("published",x.get("date","")),"summary":x.get("summary","")} for x in items[:24]]
url=os.environ["AURORA_AI_URL"].rstrip("/")+"/generate"
secret=os.environ["AURORA_AI_SECRET"]
req=urllib.request.Request(url,data=json.dumps({"items":items}).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+secret},method="POST")
with urllib.request.urlopen(req,timeout=90) as response: result=json.load(response)
assert result.get("analysis",{}).get("sections"), "No sourced sections returned"
pathlib.Path("morgenbrief-ai-test.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print("Generated test brief with",len(result["analysis"]["sections"]),"sections; live file unchanged")
