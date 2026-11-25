"""Explicitly enabled free accounts only; never upgrade or retry paid routes."""
import os,json,urllib.request,urllib.error

DISABLED=set()
COUNTS={}

def request(url,payload,headers,timeout=55):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json',**headers})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.load(r)

def candidates(prompt):
    configs=[('GROQ','https://api.groq.com/openai/v1/chat/completions','llama-3.3-70b-versatile'),('GEMINI','https://generativelanguage.googleapis.com/v1beta/models/','gemini-2.5-flash-lite'),('OPENROUTER','https://openrouter.ai/api/v1/chat/completions','openrouter/free'),('MISTRAL','https://api.mistral.ai/v1/chat/completions','mistral-small-latest')]
    for name,url,default in configs:
        key=os.getenv(name+'_API_KEY',''); model=os.getenv(name+'_MODEL',default)
        if not key or os.getenv(name+'_FREE_CONFIRMED')!='yes' or name in DISABLED: continue
        if COUNTS.get(name,0)>=max(0,min(10,int(os.getenv(name+'_RUN_LIMIT','3')))):continue
        if name=='OPENROUTER' and model!='openrouter/free':continue
        COUNTS[name]=COUNTS.get(name,0)+1
        try:
            if name=='GEMINI':
                if model not in ('gemini-2.5-flash-lite','gemini-2.5-flash'):continue
                result=request(url+model+':generateContent',{'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'temperature':.2,'maxOutputTokens':1800,'responseMimeType':'application/json'}},{'x-goog-api-key':key})
                raw=''.join(p.get('text','') for p in result['candidates'][0]['content']['parts'] if not p.get('thought'))
            else:
                payload={'model':model,'messages':[{'role':'user','content':prompt}],'temperature':.2,'max_tokens':1800}
                if name=='OPENROUTER':payload['provider']={'max_price':{'prompt':0,'completion':0}}
                else:payload['response_format']={'type':'json_object'}
                result=request(url,payload,{'Authorization':'Bearer '+key}); raw=result['choices'][0]['message']['content']
            yield name,json.loads(raw)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,KeyError,IndexError,TypeError) as e:
            DISABLED.add(name); print(name,'paused for this run:',getattr(e,'code',type(e).__name__))
    if os.getenv('OLLAMA_ENABLED','yes')=='yes' and 'OLLAMA' not in DISABLED:
        try:
            result=request('http://127.0.0.1:11434/api/generate',{'model':os.getenv('NEWS_AI_MODEL','qwen2.5:3b'),'prompt':prompt,'stream':False,'format':'json','options':{'temperature':.2,'num_predict':1800,'num_ctx':4096}}, {},timeout=240)
            yield 'OLLAMA',json.loads(result['response'])
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,KeyError,TypeError) as e:
            DISABLED.add('OLLAMA'); print('OLLAMA paused:',type(e).__name__)
