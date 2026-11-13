import json, os, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MODEL=os.getenv('GEMINI_MODEL','gemini-2.5-flash-lite')
SYSTEM='''Сен Qolдау AI, 5–11 сынып оқушыларына арналған инклюзивті оқу көмекшісісің. Барлық пәнді қолдайсың. Тек қазақша жауап бер, бірақ пәндегі қажетті терминдерді өз тілінде сақта. Оқушыны кемсітпе, диагноз қойма. Оқушы сұрағын талда, оның жасына және қолдау деңгейіне сәйкес қарапайым, нақты, қысқа түсіндір. Дайын жауапты бірден бермей, алдымен ойлануға бағыттайтын көмек көрсет. Математика есептерін мұқият тексер. Ақпаратқа сенімсіз болсаң ашық айт. Жауап пішімі: 1) Түсіндіру 2) Мысал 3) Оқушыға бір шағын тапсырма. Егер оқушы өз жауабын берсе, оны талдап, дұрыс тұсын, қатесін және келесі қадамды көрсет. Ешқашан оқушының жеке деректерін сұрама.'''
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
 def do_POST(self):
  if self.path!='/api/help': return self.send_error(404)
  try:
   size=int(self.headers.get('Content-Length','0'))
   if size>15000: return self.send_error(413)
   data=json.loads(self.rfile.read(size))
   subject=str(data.get('subject',''))[:60]; grade=str(data.get('grade',''))[:10]; level=str(data.get('level',''))[:30]
   task=str(data.get('task',''))[:2500]; answer=str(data.get('answer',''))[:1500]
   if not task.strip(): raise ValueError('Тапсырманы енгізіңіз')
   key=os.getenv('GEMINI_API_KEY')
   if not key: raise ValueError('GEMINI_API_KEY орнатылмаған. README нұсқаулығын қараңыз.')
   prompt=f'Пән: {subject}\nСынып: {grade}\nҚолдау деңгейі: {level}\nТапсырма: {task}\nОқушы жауабы: {answer or "әлі берілген жоқ"}'
   payload={'system_instruction':{'parts':[{'text':SYSTEM}]},'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'temperature':0.35,'maxOutputTokens':900}}
   req=urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key},method='POST')
   with urllib.request.urlopen(req,timeout=35) as r: result=json.load(r)
   output='\n'.join(p.get('text','') for c in result.get('candidates',[]) for p in c.get('content',{}).get('parts',[]))
   if not output: raise ValueError('AI жауап бермеді. Қайта көріңіз.')
   self.respond(200,{'reply':output})
  except urllib.error.HTTPError as e:
   self.respond(502,{'error':f'AI қызметі қате қайтарды ({e.code}). Модельді немесе тегін лимитті тексеріңіз.'})
  except Exception as e: self.respond(400,{'error':str(e)})
 def respond(self,status,obj):
  raw=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
if __name__=='__main__':
 port=int(os.getenv('PORT','8000'))
 print(f'Qolдау AI listening on {port}')
 ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
