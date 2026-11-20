"""Litigation agents: each node takes graph state and returns only state updates.

No node files in court, emails a client, or creates a binding deadline.
All external work products remain drafts until an attorney reviews them.
"""
import os
import re
import requests
from datetime import date
from langchain_openai import ChatOpenAI
from storage import load, audit

# Utility: log node activity in an audit trail so attorneys can trace workflow decisions.
def log(state, name, detail):
    audit(state['event']['event_id'], name, detail)

def intake_agent(state):
    """NODE 1: validate incoming event. This is NOT a docket-monitoring service."""
    event = state['event']
    required = ('event_id','docket_number','court','title','filed_date')
    missing = [k for k in required if not str(event.get(k, '')).strip()]
    if missing:
        reason = 'Missing required event fields: ' + ', '.join(missing)
        log(state, 'intake', reason)
        return {'error':reason, 'status':'blocked'}
    try:
        date.fromisoformat(event['filed_date'])
    except ValueError:
        return {'error':'filed_date must be YYYY-MM-DD', 'status':'blocked'}
    log(state, 'intake', 'Event validated; no authenticity verification performed')
    return {'status':'intake_validated'}

def matter_agent(state):
    """NODE 2: deterministic docket+court matching; never silently guess a matter."""
    e = state['event']
    matches = [m for m in load('matters.json', []) if
               m['docket_number'].strip().casefold() == e['docket_number'].strip().casefold()
               and m['court'].strip().casefold() == e['court'].strip().casefold()]
    if len(matches) != 1:
        reason = f'Matter match count = {len(matches)}. Manual matter resolution required.'
        log(state, 'matter_match', reason)
        return {'status':'needs_matter_review','error':reason}
    log(state, 'matter_match', f"Matched {matches[0]['matter_id']}")
    return {'matter':matches[0], 'status':'matter_matched'}

def precedent_agent(state):
    """NODE 3: retrieve synthetic/local precedent using keyword overlap.

Replace with permission-filtered iManage/NetDocuments search for production.
"""
    event = state['event']
    query = (event['title'] + ' ' + event.get('description','')).lower()
    tokens = set(re.findall(r'[a-z]{4,}', query))
    scored = []
    for p in load('precedents.json', []):
        score = len(tokens & set(re.findall(r'[a-z]{4,}', ' '.join(p['tags']) + ' ' + p['title'].lower())))
        if score:
            scored.append((score, p))
    selected = [p for _,p in sorted(scored, key=lambda x:x[0], reverse=True)[:3]]
    log(state, 'precedent', f'Retrieved {len(selected)} local examples')
    return {'precedents':selected}

def caselaw_agent(state):
    """NODE 4: optionally search CourtListener; no claim of exhaustive research.

Research results are candidate leads, NOT verified authorities or holdings.
"""
    if os.getenv('ENABLE_COURTLISTENER','0') != '1':
        return {'case_law':[], 'research_note':'CourtListener disabled; no external case-law search performed.'}
    headers = {'User-Agent':'LitigationDemo/0.1 (educational prototype)'}
    if os.getenv('COURTLISTENER_TOKEN'):
        headers['Authorization'] = 'Token ' + os.environ['COURTLISTENER_TOKEN']
    try:
        response = requests.get('https://www.courtlistener.com/api/rest/v3/search/',
                                params={'q':state['event']['title'],'type':'o'}, headers=headers, timeout=12)
        response.raise_for_status()
        payload = response.json()
        results = payload.get('results', [])[:5]
        leads = [{'title':str(r.get('caseName') or r.get('case_name') or 'Untitled'),
                  'citation':str(r.get('citation') or ''),
                  'url':str(r.get('absolute_url') or r.get('download_url') or ''),
                  'source':'CourtListener search result — unverified'} for r in results]
        log(state, 'case_law', f'{len(leads)} candidate results returned')
        return {'case_law':leads, 'research_note':'Search leads only. Verify case text, jurisdiction, treatment, and citations.'}
    except (requests.RequestException, ValueError) as exc:
        log(state, 'case_law', f'Search unavailable: {type(exc).__name__}')
        return {'case_law':[], 'research_note':f'CourtListener unavailable ({type(exc).__name__}); manual research required.'}

def analysis_agent(state):
    """NODE 5: generate a preliminary legal issue memo using the LLM, if configured.

AI is instructed not to invent law, deadlines, holdings, or missing facts.
"""
    e = state['event']
    context = {'matter':state.get('matter'), 'event':e,
               'precedents':state.get('precedents',[]), 'case_law':state.get('case_law',[])}
    if not os.getenv('OPENAI_API_KEY'):
        memo = ('DEMO MODE — NO AI ANALYSIS PERFORMED.\n'
                f"Event: {e['title']} ({e['filed_date']}).\n"
                'Attorney should read the original filing, identify response requirements, '
                'verify service and applicable court rules, and research controlling authority.\n'
                'This text is a deterministic placeholder, not a legal opinion.')
    else:
        import json
        llm = ChatOpenAI(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'), temperature=0)
        prompt = ('You are a litigation work-product drafting assistant. Draft a cautious, clearly '
                  'labeled PRELIMINARY attorney-review memo. Separate facts from unknowns, identify '
                  'potential issues, next research steps, and cite only supplied sources by identifier. '
                  'Do not invent citations, rules, holdings, or deadlines. Flag that court rules, '
                  'filing authenticity, jurisdiction, and citator treatment require human verification. '
                  'Do not treat sample precedents as genuine firm documents.\n\nINPUT:\n' + json.dumps(context))
        memo = llm.invoke(prompt).content
    log(state, 'analysis', 'Draft analysis prepared (AI)' if os.getenv('OPENAI_API_KEY') else 'Demo placeholder prepared')
    return {'analysis':str(memo)}

def drafting_agent(state):
    """NODE 6: compose a draft attorney work product; no court-ready filing generated."""
    draft = ('DRAFT — ATTORNEY REVIEW REQUIRED\n\n'
             f"Matter: {state['matter']['name']}\n"
             f"Court event: {state['event']['title']}\n\n"
             'PRELIMINARY ANALYSIS\n' + state['analysis'] + '\n\n'
             'REQUIRED REVIEW: compare original filing; validate authorities and citations; '
             'check local rules, service date, confidentiality, and deadlines.')
    log(state, 'drafting', 'Internal review draft created')
    return {'draft':draft}

def task_agent(state):
    """NODE 7: create proposed tasks WITHOUT calculating legal deadlines.

All due dates remain unset until an attorney verifies the rules and service dates.
"""
    base = state['event']['event_id']
    tasks = [
        {'id':base+'-1','title':'Verify court filing and service information','due_date':None,'status':'proposed'},
        {'id':base+'-2','title':'Research controlling law and verify citations','due_date':None,'status':'proposed'},
        {'id':base+'-3','title':'Calculate response deadline from verified court rules','due_date':None,'status':'proposed'},
        {'id':base+'-4','title':'Review and revise draft work product','due_date':None,'status':'proposed'}]
    log(state, 'tasks', 'Four proposed tasks created with no due dates')
    return {'tasks':tasks,'status':'awaiting_attorney_review'}

# Conditional EDGE 1: failed intake or ambiguous matter routes to END, not to AI.
def route_after_intake(state):
    return 'stop' if state.get('error') else 'match'

# Conditional EDGE 2: only a uniquely matched matter may reach privileged retrieval.
def route_after_match(state):
    return 'stop' if state.get('error') else 'research'
