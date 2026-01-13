-- Create table for Adopted Proposals
create table if not exists adopted_proposals (
    id uuid default gen_random_uuid() primary key,
    regulation_id text references regulations(id),
    session_id uuid references sessions(id),
    source_doc_id uuid references documents(id),
    series text, -- e.g. "05"
    supplement text, -- e.g. "12"
    entry_date date,
    description text,
    status text default 'Adopted', -- 'Adopted', 'Entered into Force', etc.
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Index for fast lookup by regulation
create index if not exists adopted_proposals_reg_idx on adopted_proposals(regulation_id);
create index if not exists adopted_proposals_session_idx on adopted_proposals(session_id);
create index if not exists adopted_proposals_doc_idx on adopted_proposals(source_doc_id);

-- Enable RLS
alter table adopted_proposals enable row level security;

-- Policies (simplified for this app - assuming basic read/write for authenticated)
create policy "Allow read access to all users"
    on adopted_proposals for select
    using (true);

create policy "Allow insert for authenticated users"
    on adopted_proposals for insert
    with check (auth.role() = 'authenticated');

create policy "Allow update for authenticated users"
    on adopted_proposals for update
    using (auth.role() = 'authenticated');

create policy "Allow delete for authenticated users"
    on adopted_proposals for delete
    using (auth.role() = 'authenticated');
