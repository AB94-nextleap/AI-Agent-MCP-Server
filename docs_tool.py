import json
from googleapiclient.discovery import build

def append_to_doc(doc_id: str, content: str, creds) -> dict:
    """
    Appends content to a Google Doc.
    If 'content' is a valid JSON array of Google Docs API requests, it executes them directly,
    automatically shifting relative indices to append at the end of the document.
    Otherwise, it appends the content as plain text at the end.
    """
    service = build('docs', 'v1', credentials=creds)
    
    # 1. Fetch document to determine length/EOF insertion point
    doc = service.documents().get(documentId=doc_id).execute()
    body_content = doc.get('body', {}).get('content', [])
    doc_length = body_content[-1].get('endIndex', 1) if body_content else 1
    insert_index = max(1, doc_length - 1)
    
    # 2. Try parsing content as JSON list of requests
    requests = None
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            requests = parsed
        elif isinstance(parsed, dict) and "requests" in parsed:
            requests = parsed["requests"]
    except Exception:
        pass
        
    if not requests:
        # Standard plain text append
        requests = [
            {
                'insertText': {
                    'text': content,
                    'location': { 'index': insert_index }
                }
            }
        ]
    else:
        # Deep copy and shift relative ranges by the insertion offset
        shifted_requests = []
        offset = insert_index - 1
        
        for req in requests:
            new_req = json.loads(json.dumps(req))
            
            # Shift text insertion locations
            if 'insertText' in new_req:
                insert_info = new_req['insertText']
                # Swap endOfSegmentLocation with precise index
                if 'endOfSegmentLocation' in insert_info:
                    del insert_info['endOfSegmentLocation']
                    insert_info['location'] = { 'index': insert_index }
                elif 'location' in insert_info and 'index' in insert_info['location']:
                    insert_info['location']['index'] += offset
                    
            # Shift formatting styles ranges
            for key in ['updateParagraphStyle', 'updateTextStyle', 'createNamedRange']:
                if key in new_req and 'range' in new_req[key]:
                    rng = new_req[key]['range']
                    if 'startIndex' in rng:
                        rng['startIndex'] += offset
                    if 'endIndex' in rng:
                        rng['endIndex'] += offset
                        
            shifted_requests.append(new_req)
        requests = shifted_requests
        
    body = {'requests': requests}
    result = service.documents().batchUpdate(documentId=doc_id, body=body).execute()
    return result
