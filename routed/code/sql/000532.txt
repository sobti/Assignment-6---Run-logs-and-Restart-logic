CREATE TABLE currency (
  currency_id SERIAL PRIMARY KEY,
  character_name TEXT NOT NULL,
  type TEXT NOT NULL,
  amount INTEGER NOT NULL
);
