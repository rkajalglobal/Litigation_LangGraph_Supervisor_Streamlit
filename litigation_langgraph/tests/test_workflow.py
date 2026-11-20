"""Run with pytest -q. No API keys or network access required."""
from graph import workflow
from storage import load

def sample_event():
    return {'event_id':'test-1','docket_number':'1:26-cv-00123',
            'court':'US District Court, Example District',
            'title':'Motion to Compel Discovery','filed_date':'2026-10-15'}

def test_happy_path(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('ENABLE_COURTLISTENER','0')
    result = workflow.invoke({'event':sample_event()})
    assert result['status'] == 'awaiting_attorney_review'
    assert result['matter']['matter_id'] == 'MAT-1001'
    assert len(result['tasks']) == 4
    assert all(task['due_date'] is None for task in result['tasks'])

def test_unmatched_matter_stops(monkeypatch):
    event = sample_event()
    event['docket_number'] = 'UNKNOWN'
    result = workflow.invoke({'event':event})
    assert result['status'] == 'needs_matter_review'
    assert 'analysis' not in result

def test_bad_event_stops():
    result = workflow.invoke({'event':{'event_id':'bad'}})
    assert result['status'] == 'blocked'
