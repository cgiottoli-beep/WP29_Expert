-- FIX DELETE RLS
-- The previous scripts missed the DELETE policy, so deletions were silently blocked.

-- 1. Interpretation Deletion
CREATE POLICY "Allow Anon Delete" 
ON interpretations 
FOR DELETE 
TO anon, authenticated 
USING (true);

-- 2. Embeddings Deletion
-- (Needed if cascading delete triggers RLS checks or if we delete manually)
CREATE POLICY "Allow Anon Delete Embeddings" 
ON embeddings 
FOR DELETE 
TO anon, authenticated 
USING (true);

-- 3. Issuers - Create just in case we need to delete issuers later
CREATE POLICY "Allow Anon Delete Issuers" 
ON issuers 
FOR DELETE 
TO anon, authenticated 
USING (true);
