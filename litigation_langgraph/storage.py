"""Small local JSON store for a demonstration; NOT appropriate for confidential production matters."""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)

def load(name, default):
    path = DATA / name
    if not path.exists():
        sample = ROOT / ('sample_' + name)
        return json.loads(sample.read_text(encoding='utf-8')) if sample.exists() else default
    return json.loads(path.read_text(encoding='utf-8'))

def save(name, value):
    path = DATA / name
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(path)

def audit(event_id, step, message):
    records = load('audit.json', [])
    records.append({'timestamp':datetime.now(timezone.utc).isoformat(), 'event_id':event_id, 'step':step, 'message':message})
    save('audit.json', records)

def persist_run(state):
    runs = load('runs.json', {})
    runs[state['event']['event_id']] = state
    save('runs.json', runs)
