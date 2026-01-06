-- TEMPORARY POLICY: Allow anonymous inserts/selects for testing
-- This is needed because the Python app is not using a Service Role key
-- and we have not implemented a full login flow yet.

-- 1. Enable RLS (already enabled, just making sure)
ALTER TABLE interpretations ENABLE ROW LEVEL SECURITY;

-- 2. Drop existing restrictive policies if needed (conflicts won't stop execution usually, but cleanest to add new ones)
-- We keep "Write Access Strategy" but ADD a new permissible one for 'anon'

CREATE POLICY "Allow Anon Insert" 
ON interpretations 
FOR INSERT 
TO anon, authenticated 
WITH CHECK (true);

CREATE POLICY "Allow Anon Select" 
ON interpretations 
FOR SELECT 
TO anon, authenticated 
USING (true);

CREATE POLICY "Allow Anon Update" 
ON interpretations 
FOR UPDATE 
TO anon, authenticated 
USING (true);

-- Also fix Issuers table access
CREATE POLICY "Allow Anon Read Issuers" 
ON issuers 
FOR SELECT 
TO anon, authenticated 
USING (true);

CREATE POLICY "Allow Anon Insert Issuers" 
ON issuers 
FOR INSERT 
TO anon, authenticated 
WITH CHECK (true);
