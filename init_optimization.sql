-- Function to get documents that don't have any embeddings
-- This runs on the database side, avoiding the need to fetch all IDs to the client.

create or replace function get_documents_without_embeddings()
returns setof documents
language sql
as $$
  select *
  from documents d
  where not exists (
    select 1
    from embeddings e
    where e.source_id = d.id
  );
$$;
