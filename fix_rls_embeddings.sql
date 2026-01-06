-- FIX EMBEDDINGS RLS
-- The previous script fixed 'interpretations', but we also need to allow 
-- writing to the 'embeddings' table for the AI search to work as 'anon'.

CREATE POLICY "Allow Anon Insert Embeddings" 
ON embeddings 
FOR INSERT 
TO anon, authenticated 
WITH CHECK (true);

CREATE POLICY "Allow Anon Select Embeddings" 
ON embeddings 
FOR SELECT 
TO anon, authenticated 
USING (true);

-- Ensure we can delete/update if needed (optional but good for cleanup)
CREATE POLICY "Allow Anon All Embeddings" 
ON embeddings 
FOR ALL 
TO anon, authenticated 
USING (true)
WITH CHECK (true);
