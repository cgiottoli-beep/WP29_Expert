-- Add 'Adopted Proposals' to the allowed values for doc_type
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_doc_type_check;

ALTER TABLE documents 
ADD CONSTRAINT documents_doc_type_check 
CHECK (doc_type IN ('Report', 'Agenda', 'Formal', 'Informal', 'Adopted Proposals'));
