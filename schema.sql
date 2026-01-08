-- Tabela de Ativos
create table if not exists assets (
  id uuid default gen_random_uuid() primary key,
  ticker text not null,
  type text not null,
  quantity numeric not null default 0,
  average_price numeric not null default 0,
  current_price numeric default 0,
  target_allocation numeric default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Tabela de Alocao por Categoria
create table if not exists category_allocations (
  id uuid default gen_random_uuid() primary key,
  category text not null unique,
  target_percentage numeric not null default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Configurar RLS (Row Level Security) - Desabilitado para simplicidade inicial
-- Em produo, voc deve habilitar e configurar polticas de acesso.
alter table assets disable row level security;
alter table category_allocations disable row level security;
