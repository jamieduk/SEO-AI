#!/usr/bin/env python3
# (c) J~Net 2025
# seo_crawler_full_crawl.py

import sys,os,re,json,time,argparse,subprocess
from collections import Counter
from urllib.parse import urlparse,urljoin,urldefrag
import requests
from bs4 import BeautifulSoup
import html

# Settings
OLLAMA_MODEL='crewai-llama2-uncensored:latest'
MAX_PAGES=500
REQUEST_DELAY=0.2
OUTPUT_DIR='output'
USER_AGENT='seo-crawler-bot/1.0 (+https://example.com)'
TIMEOUT=10

STOPWORDS=set("""
a about above after again against all am an and any are aren't as at be because been before being below between both but by
could couldn't did didn't do does doesn't doing don't down during each few for from further had hadn't has hasn't have haven't
having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's
its itself let's me more most mustn't my myself no nor not of off on once only or other ought our ours ourselves out over own same
shan't she she'd she'll she's should shouldn't so some such than that that's the their theirs them themselves then there there's these
they they'd they'll they're they've this those through to too under until up very was wasn't we we'd we'll we're we've were weren't what
what's when when's where where's which while who who's whom why why's with won't would wouldn't you you'd you'll you're you've your yours yourself yourselves
""".split())

def ensure_output_dir():
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR,exist_ok=True)

def clean_url(u):
    u,_=urldefrag(u)
    if u.endswith('/') and len(u)>1:
        return u[:-1]
    return u

def fetch_url(session,url):
    headers={'User-Agent':USER_AGENT}
    try:
        r=session.get(url,headers=headers,timeout=TIMEOUT,allow_redirects=True)
        if r.status_code==200:
            return r
    except:
        pass
    return None

def extract_visible_text(soup):
    for el in soup(['script','style','noscript','header','footer','svg','iframe']):
        el.extract()
    return re.sub(r'\s+',' ',' '.join(soup.stripped_strings)).strip()

def extract_meta(soup):
    meta={}
    title_tag=soup.find('title')
    meta['title']=title_tag.get_text().strip() if title_tag else ''
    for name in ('description','keywords','author'):
        tag=soup.find('meta',attrs={'name':name})
        meta[name]=tag['content'].strip() if tag and tag.has_attr('content') else ''
    for prop in ('og:title','og:description','og:url','og:image'):
        tag=soup.find('meta',attrs={'property':prop})
        meta[prop]=tag['content'].strip() if tag and tag.has_attr('content') else ''
    can=soup.find('link',attrs={'rel':'canonical'})
    meta['canonical']=can['href'].strip() if can and can.has_attr('href') else ''
    return meta

def simple_keywords(text,topn=10):
    words=[w for w in re.findall(r"[a-zA-Z]{3,}",text.lower()) if w not in STOPWORDS]
    return [w for w,_ in Counter(words).most_common(topn)]

def simple_description(text,maxlen=160):
    if not text: return ''
    sents=re.split(r'(?<=[.!?])\s+',text)
    for i in range(min(5,len(sents))):
        cand=' '.join(sents[:i+1]).strip()
        if len(cand)>40:
            return (cand[:maxlen].rsplit(' ',1)[0]+'...') if len(cand)>maxlen else cand
    t=text.strip()
    return (t[:maxlen].rsplit(' ',1)[0]+'...') if len(t)>maxlen else t

def simple_title(soup,text,domain):
    h1=soup.find('h1')
    if h1 and h1.get_text(strip=True): return h1.get_text(strip=True)[:70]
    title_tag=soup.find('title')
    if title_tag and title_tag.get_text(strip=True): return title_tag.get_text(strip=True)[:70]
    txt=text.strip()
    return (txt[:60].rsplit(' ',1)[0]+'...') if len(txt)>60 else domain

def call_ollama(model,prompt,timeout_sec=20):
    try_cmds=[
        ['ollama','generate',model,prompt],
        ['ollama','generate',model,'--num-outputs','1','--no-stream','--',prompt],
        ['ollama','run',model,'--',prompt]
    ]
    for cmd in try_cmds:
        try:
            proc=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout_sec)
            if proc.returncode==0 and proc.stdout.strip(): return proc.stdout.strip()
        except:
            continue
    return ""

def generate_meta_ai(soup,text,domain,url):
    sug_title=simple_title(soup,text,domain)
    sug_description=simple_description(text,160)
    sug_keywords=simple_keywords(text,12)
    sug_canonical=url

    if not OLLAMA_MODEL:
        return {'title':sug_title,'description':sug_description,'keywords':', '.join(sug_keywords),'canonical':sug_canonical,'method':'heuristic'}

    prompt=f"""You are an SEO assistant. Given the page URL: {url} and the page text excerpt below, produce JSON with keys title,description,keywords,canonical. Keep description<=160 chars.

Text:
{text[:3000]}

Respond ONLY with valid JSON.
"""
    try:
        out=call_ollama(OLLAMA_MODEL,prompt,timeout_sec=30)
        jstart=out.find('{')
        jend=out.rfind('}')
        if jstart!=-1 and jend!=-1:
            data=json.loads(out[jstart:jend+1])
            return {
                'title':data.get('title',sug_title)[:70],
                'description':data.get('description',sug_description)[:160],
                'keywords':data.get('keywords',', '.join(sug_keywords)),
                'canonical':data.get('canonical',sug_canonical),
                'method':'ollama'
            }
    except: pass
    return {'title':sug_title,'description':sug_description,'keywords':', '.join(sug_keywords),'canonical':sug_canonical,'method':'heuristic'}

def make_html_report(report,filename):
    rows=[]
    for page,data in report.items():
        found=data['found']
        missing=data['missing']
        suggested=data['suggested']

        keywords_str=suggested['keywords']
        if isinstance(keywords_str,list):
            keywords_str=', '.join(keywords_str)

        suggested_html="\n".join([
            f"<meta name=\"description\" content=\"{html.escape(suggested['description'])}\">",
            f"<meta name=\"keywords\" content=\"{html.escape(keywords_str)}\">",
            f"<link rel=\"canonical\" href=\"{html.escape(suggested['canonical'])}\">",
            f"<title>{html.escape(suggested['title'])}</title>"
        ])

        rows.append(f"""
        <div class="page">
          <h2><a href="{html.escape(page)}" target="_blank">{html.escape(page)}</a></h2>

          <div class="block"><strong>Found meta:</strong>
            <pre>{html.escape(json.dumps(found,indent=2))}</pre>
          </div>

          <div class="block"><strong>Missing meta fields:</strong>
            <pre>{html.escape(", ".join(missing))}</pre>
          </div>

          <div class="block"><strong>Suggested SEO meta for this page:</strong>
            <pre>{html.escape(suggested_html)}</pre>
            <p><em>Method: {html.escape(suggested.get('method',''))}</em></p>
          </div>
        </div>
        """)

    htmlpage=f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>SEO Crawl Report</title>
<style>
body{{background:#0f1720;color:#e6eef8;font-family:system-ui;padding:20px}}
a{{color:#9be7ff}}
.page{{background:#0b1220;border:1px solid #122233;padding:14px;margin-bottom:12px;border-radius:8px;box-shadow:0 4px 14px rgba(0,0,0,0.6)}}
.block{{background:#07111b;padding:10px;border-radius:6px;margin-top:8px}}
pre{{white-space:pre-wrap;word-wrap:break-word;color:#cfefff}}
</style>
</head>
<body>
<h1>SEO Crawl Report</h1>
{''.join(rows)}
</body>
</html>
"""
    with open(os.path.join(OUTPUT_DIR,filename),'w',encoding='utf-8') as f:
        f.write(htmlpage)

def main():
    parser=argparse.ArgumentParser(description='Crawl a domain and generate SEO meta tags')
    parser.add_argument('domain')
    parser.add_argument('--max',type=int,default=MAX_PAGES)
    args=parser.parse_args()

    start=args.domain.strip()
    if not start.startswith('http'): start="https://"+start
    start=clean_url(start)

    parsed=urlparse(start)
    base_netloc=parsed.netloc.lower().lstrip('www.')
    base_scheme=parsed.scheme
    root=f"{base_scheme}://{base_netloc}"

    print(f"Starting full crawl at {start} (domain={base_netloc})")
    ensure_output_dir()
    session=requests.Session()

    # --- Step 1: Full site link discovery ---
    all_links=set()
    to_process=set([start])
    processed=set()

    while to_process:
        url=to_process.pop()
        url=clean_url(url)
        if url in processed: continue

        time.sleep(REQUEST_DELAY)
        r=fetch_url(session,url)
        processed.add(url)
        if not r or 'text/html' not in r.headers.get('Content-Type',''): 
            continue

        soup=BeautifulSoup(r.text,'html.parser')
        all_links.add(url)

        for a in soup.find_all('a',href=True):
            href=a['href'].strip()
            if not href or href.startswith(('mailto:','tel:','#','javascript:')): continue
            abs_url=clean_url(urljoin(url,href))
            netloc=urlparse(abs_url).netloc.lower().lstrip('www.')
            if netloc and netloc != base_netloc: continue
            if abs_url not in all_links:
                to_process.add(abs_url)

    print(f"Total unique internal links found: {len(all_links)}")

    # --- Step 2: Crawl each unique link to extract meta ---
    report={}
    pages=0
    for url in sorted(all_links):
        if pages>=args.max: break
        time.sleep(REQUEST_DELAY)
        r=fetch_url(session,url)
        if not r or 'text/html' not in r.headers.get('Content-Type',''): 
            continue

        soup=BeautifulSoup(r.text,'html.parser')
        pages+=1
        print(f"[{pages}] Crawled {url}")

        found=extract_meta(soup)
        text=extract_visible_text(soup)
        missing=[k for k in ['title','description','keywords','canonical'] if not found.get(k,'').strip()]
        suggested=generate_meta_ai(soup,text,base_netloc,url)
        report[url]={'found':found,'missing':missing,'suggested':suggested}

    with open(os.path.join(OUTPUT_DIR,'seo_report.json'),'w',encoding='utf-8') as jf:
        json.dump(report,jf,indent=2,ensure_ascii=False)
    make_html_report(report,'seo_report.html')

    print(f"Done. Pages crawled={len(report)}. Reports saved to {OUTPUT_DIR}/")
    print(f"- JSON: {OUTPUT_DIR}/seo_report.json")
    print(f"- HTML: {OUTPUT_DIR}/seo_report.html")

if __name__=='__main__':
    main()

