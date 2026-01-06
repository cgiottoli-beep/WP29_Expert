-- FIX MISSING COLUMNS
-- Run this to ensure 'created_at' exists (fixes "Error fetching users" if sorting fails)

ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
