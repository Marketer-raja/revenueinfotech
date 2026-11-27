"""Free-confirmed providers only. Never log keys, URLs with keys, or raw responses."""
import os, json, re, urllib.request, urllib.error
DISABLED=set()
COUNTS={}
DRAFT_SCHEMA={'type':'object','properties':{'sufficient':{'type':'boolean'},**{k:{'type':'string'} for k in ('title','summary','articleBody','verificationNotes')}},'required':['sufficient','title','summary','articleBody','verificationNotes'],'additionalProperties':False}

def request(url,payload,headers,timeout=55):
    req=urllib.request.Request(url,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json',**headers})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.load(r)

def decode(raw):
    if isinstance(raw,list):
        raw=''.join(p.get('text','') for p in raw if isinstance(p,dict) and isinstance(p.get('text'),str))
    if not isinstance(raw,str) or not raw.strip():
        raise ValueError('empty or non-text response')
    raw=re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$', '', raw.strip(),flags=re.I)
    obj=json.loads(raw)
    if not isinstance(obj,dict): raise ValueError('expected JSON object')
    return obj

def candidates(prompt):
    configs=[('GROQ','https://api.groq.com/openai/v1/chat/completions','openai/gpt-oss-120b'),('GEMINI','https://generativelanguage.googleapis.com/v1beta/models','gemini-3.8-flash'),('OPENROUTER','https://openrouter.ai/api/v1/chat/completions','openrouter/free'),('MISTRAL','https://api.mistral.ai/v1/chat/completions','mistral-small-latest')]
    for name,url,model in configs:
        key=os.getenv(name+'_API_KEY','')
        if not key or os.getenv(name+'_FREE_CONFIRMED')!='yes' or name in DISABLED: continue
        if COUNTS.get(name,0)>=int(os.getenv('PROVIDER_RUN_LIMIT','5')): continue
        COUNTS[name]=COUNTS.get(name,0)+1
        try:
            print(f'{name}: requesting {model}',flush=True)
            if name=='GEMINI':
                headers={'x-goog-api-key':key}
                listing=request(url+'?pageSize=100',None,headers)
                available={m['name'].removeprefix('models/') for m in listing.get('models',[]) if 'generateContent' in m.get('supportedGenerationMethods',[])}
                if model not in available:
                    print('GEMINI: configured free-tier model not listed; skipping rather than choosing an unconfirmed model',flush=True); DISABLED.add(name); continue
                result=request(url+'/'+model+':generateContent',{'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'temperature':.2,'maxOutputTokens':4096,'responseMimeType':'application/json'}},headers)
                raw=''.join(p['text'] for p in result['candidates'][0]['content']['parts'] if isinstance(p.get('text'),str) and not p.get('thought'))
            else:
                payload={'model':model,'messages':[{'role':'user','content':prompt}],'temperature':.2,'max_tokens':2400}
                if name=='OPENROUTER':payload['provider']={'max_price':{'prompt':0,'completion':0}}
                else:payload['response_format']={'type':'json_object'}
                if name=='GROQ':
                    payload['max_completion_tokens']=4096; del payload['max_tokens']; payload['reasoning_effort']='low'
                result=request(url,payload,{'Authorization':'Bearer '+key})
                raw=result['choices'][0]['message'].get('content')
            draft=decode(raw); print(f'{name}: JSON received; checking editorial quality',flush=True); yield name,draft
        except urllib.error.HTTPError as e:
            DISABLED.add(name); print(f'{name}: HTTP {e.code}; paused for run; retry-after={e.headers.get("Retry-After","not supplied") if e.headers else "not supplied"}',flush=True)
        except (urllib.error.URLError,TimeoutError,ValueError,KeyError,IndexError,TypeError,AttributeError) as e:
            print(f'{name}: invalid or unavailable response ({type(e).__name__})',flush=True)
    if os.getenv('OLLAMA_ENABLED','yes')=='yes' and 'OLLAMA' not in DISABLED and COUNTS.get('OLLAMA',0)<int(os.getenv('PROVIDER_RUN_LIMIT','5')):
        COUNTS['OLLAMA']=COUNTS.get('OLLAMA',0)+1
        try:
            print('OLLAMA: requesting local draft',flush=True)
            result=request('http://127.0.0.1:11434/api/generate',{'model':os.getenv('NEWS_AI_MODEL','qwen2.5:3b'),'prompt':prompt,'stream':False,'format':DRAFT_SCHEMA,'options':{'temperature':.2,'num_predict':3072,'num_ctx':8192}}, {},timeout=240)
            print('OLLAMA: completion reason:',result.get('done_reason','unknown'),'output tokens:',result.get('eval_count','unknown'),flush=True)
            draft=decode(result.get('response')); print('OLLAMA: JSON received; checking editorial quality',flush=True); yield 'OLLAMA',draft
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,KeyError,TypeError,AttributeError) as e:
            DISABLED.add('OLLAMA'); print('OLLAMA paused:',type(e).__name__,flush=True)
