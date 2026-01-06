-- Create ENUMs (if they don't exist)
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('basic', 'advanced', 'contributor', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE interp_status AS ENUM ('draft', 'final', 'superseded');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create Issuers Table
CREATE TABLE IF NOT EXISTS issuers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    code TEXT,
    type TEXT, -- 'Ministry', 'Group', 'Internal'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Profiles Table (managing roles)
-- Links to Supabase auth.users
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role DEFAULT 'basic',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to handle new user signup (auto-create profile)
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, role)
  VALUES (new.id, 'basic');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Create Interpretations Table
CREATE TABLE IF NOT EXISTS interpretations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    issuer_id UUID REFERENCES issuers(id),
    issue_date DATE,
    status interp_status DEFAULT 'draft',
    regulation_mentioned TEXT,
    comments TEXT,
    content_text TEXT, -- Transcription
    file_url TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    session_id UUID REFERENCES sessions(id), -- Link to TAAM sessions or similar
    created_by UUID REFERENCES auth.users(id),
    embedding_id UUID REFERENCES embeddings(id), -- For searching
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS (Row Level Security)
ALTER TABLE interpretations ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Profiles Policies
CREATE POLICY "Public profiles are viewable by everyone" 
ON profiles FOR SELECT USING ( true );

CREATE POLICY "Users can insert their own profile" 
ON profiles FOR INSERT WITH CHECK ( auth.uid() = id );

CREATE POLICY "Users can update own profile" 
ON profiles FOR UPDATE USING ( auth.uid() = id );

-- Interpretations Policies

-- 1. Read Access
-- Basic users (or no role) see ONLY public.
-- Advanced/Contributor/Admin see ALL.
CREATE POLICY "Read Access Strategy" 
ON interpretations FOR SELECT 
TO authenticated 
USING (
    is_public = true 
    OR 
    (SELECT role FROM profiles WHERE id = auth.uid()) IN ('advanced', 'contributor', 'admin')
);

-- 2. Write Access
-- Only Contributor and Admin can insert/update/delete
CREATE POLICY "Write Access Strategy" 
ON interpretations FOR ALL 
TO authenticated 
USING (
    (SELECT role FROM profiles WHERE id = auth.uid()) IN ('contributor', 'admin')
);

-- Insert default issuers
INSERT INTO issuers (name, code, type) VALUES 
('Ministry of Transport Germany', 'E1', 'Ministry'),
('Ministry of Transport France', 'E2', 'Ministry'),
('Ministry of Transport Italy', 'E3', 'Ministry'),
('Ministry of Transport Netherlands', 'E4', 'Ministry'),
('TAAM', 'TAAM', 'Group')
ON CONFLICT DO NOTHING;
