-- Criar tabelas se elas não existirem:

CREATE TABLE IF NOT EXISTS dim_pokemon (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    height INTEGER CHECK (height > 0),
    weight INTEGER CHECK (weight > 0)
);

CREATE TABLE IF NOT EXISTS dim_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS pokemon_types (
    pokemon_id INTEGER REFERENCES dim_pokemon(id),
    type_id INTEGER REFERENCES dim_type(id),
    slot INTEGER CHECK (slot IN (1, 2)),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE IF NOT EXISTS fact_stats (
    id SERIAL PRIMARY KEY,
    pokemon_id INTEGER REFERENCES dim_pokemon(id),
    hp INTEGER CHECK (hp >= 0),
    attack INTEGER CHECK (attack >= 0),
    defense INTEGER CHECK (defense >= 0),
    special_attack INTEGER CHECK (special_attack >= 0),
    special_defense INTEGER CHECK (special_defense >= 0),
    speed INTEGER CHECK (speed >= 0),
    CONSTRAINT unique_pokemon_stats UNIQUE (pokemon_id)
);
