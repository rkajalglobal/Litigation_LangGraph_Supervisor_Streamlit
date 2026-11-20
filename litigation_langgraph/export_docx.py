"""Generate a Word memo in memory for an attorney to review."""
from io import BytesIO
from docx import Document

def to_docx(run):
    doc = Document()
    doc.add_heading('Litigation Event — Draft Review Memo', 0)
    doc.add_paragraph('NOT VERIFIED — ATTORNEY REVIEW REQUIRED')
    doc.add_heading('Matter', level=1)
    doc.add_paragraph(run.get('matter',{}).get('name','Unmatched'))
    doc.add_heading('Filing', level=1)
    doc.add_paragraph(run['event'].get('title',''))
    doc.add_heading('Preliminary analysis', level=1)
    doc.add_paragraph(run.get('analysis',''))
    doc.add_heading('Proposed tasks', level=1)
    for task in run.get('tasks',[]):
        doc.add_paragraph(task['title'] + ' — Due date not verified', style='List Bullet')
    doc.add_paragraph('No filing, court deadline, or external notification was automatically created.')
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
