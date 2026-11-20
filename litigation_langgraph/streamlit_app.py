"""Simple Streamlit UI: run the graph, review its work, and export Word drafts."""
import json
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from graph import workflow
from storage import load, save, audit, persist_run
from export_docx import to_docx

load_dotenv()
st.set_page_config(page_title='Litigation Agent Workflow', page_icon='⚖️', layout='wide')
st.title('⚖️ Agentic Litigation Workflow')
st.caption('LangGraph + Streamlit | local educational prototype | attorney-in-the-loop')
st.warning('Do not enter confidential client data. Local JSON storage is not encrypted or access-controlled. No deadline or legal authority is verified automatically.')

with st.sidebar:
    st.header('Workflow')
    st.code('Supervisor ⇄ Intake / Matter / Precedent / Case Law / Analysis / Draft / Tasks → Human Review')
    st.info('Court event intake is manual. No live docket monitoring or Microsoft 365 sync is configured.')
    st.write('**Matter directory**')
    st.dataframe(load('matters.json', []), hide_index=True)

intake, review, audit_tab = st.tabs(['New filing event', 'Attorney review', 'Audit log'])
with intake:
    sample = json.loads((Path(__file__).parent/'sample_event.json').read_text())
    event_text = st.text_area('Paste court event JSON (synthetic sample preloaded)', value=json.dumps(sample, indent=2), height=260)
    if st.button('Run multi-agent workflow', type='primary'):
        try:
            event = json.loads(event_text)
            if not isinstance(event, dict):
                raise ValueError('Event must be a JSON object')
            if not isinstance(event.get('event_id'), str) or not event['event_id'].strip():
                raise ValueError('event_id is required')
            if event['event_id'] in load('runs.json', {}):
                raise ValueError('Duplicate event_id: choose a new ID to avoid overwriting a previous run')
            with st.spinner('Executing LangGraph agents...'):
                result = workflow.invoke({'event':event})
            persist_run(result)
            st.session_state['last_event_id'] = event['event_id']
            if result.get('error'):
                st.error(result['error'])
            else:
                st.success('Draft and tasks created. Awaiting attorney review.')
                st.subheader('Supervisor decisions')
                st.dataframe(result.get('supervisor_history', []), hide_index=True)
                st.subheader('AI analysis / demo output')
                st.text(result.get('analysis',''))
                st.subheader('Proposed tasks')
                st.dataframe(result.get('tasks',[]), hide_index=True)
        except (ValueError, TypeError) as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f'Workflow failed: {type(exc).__name__}: {exc}')

with review:
    runs = load('runs.json', {})
    if not runs:
        st.info('Run a sample filing event first.')
    else:
        selected = st.selectbox('Select event', list(runs), index=list(runs).index(st.session_state['last_event_id']) if st.session_state.get('last_event_id') in runs else 0)
        run = runs[selected]
        st.write('**Status:**', run.get('status','unknown'))
        st.write('**Matter:**', run.get('matter',{}).get('name','UNMATCHED'))
        with st.expander('Supervisor routing history'):
            st.dataframe(run.get('supervisor_history', []), hide_index=True)
        st.text_area('Draft work product', value=run.get('draft','No draft generated.'), height=290, disabled=True)
        st.dataframe(run.get('tasks',[]), hide_index=True)
        st.caption(run.get('research_note',''))
        if run.get('draft'):
            st.download_button('Download Word draft', data=to_docx(run), file_name=f'{selected}_draft.docx', mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        if run.get('status') in ('awaiting_attorney_review','approved','rejected'):
            reviewer = st.text_input('Reviewer name (required)')
            notes = st.text_area('Review notes (required)')
            c1,c2 = st.columns(2)
            def decide(action):
                if not reviewer.strip() or not notes.strip():
                    st.error('Reviewer name and notes are required.')
                    return
                latest = load('runs.json', {})
                item = latest[selected]
                item['status'] = action
                item['review'] = {'reviewer':reviewer.strip(),'notes':notes.strip(),'decision':action}
                latest[selected] = item
                save('runs.json', latest)
                audit(selected,'human_review',f'{action} by {reviewer.strip()}')
                st.success(f'Recorded {action}. No external action was taken.')
                st.rerun()
            if c1.button('Approve draft'):
                decide('approved')
            if c2.button('Reject draft'):
                decide('rejected')

with audit_tab:
    st.dataframe(load('audit.json', []), hide_index=True)
