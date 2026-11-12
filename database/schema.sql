-- PostgreSQL schema (mirrors backend/models). Admin accounts are normally users with role='admin'.
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(20) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(10) NOT NULL DEFAULT 'user',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_user_role CHECK (role IN ('user','admin'))
);
CREATE TABLE IF NOT EXISTS waste_classifications (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  image_path VARCHAR(255) NOT NULL,
  waste_category VARCHAR(20) NOT NULL,
  confidence_score DOUBLE PRECISION NOT NULL,
  disposal_recommendation TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_conf_range CHECK (confidence_score >= 0 AND confidence_score <= 1),
  CONSTRAINT ck_class_cat CHECK (waste_category IN ('plastic','paper','metal','glass','organic'))
);
CREATE INDEX IF NOT EXISTS ix_class_user ON waste_classifications(user_id);
CREATE INDEX IF NOT EXISTS ix_class_cat ON waste_classifications(waste_category);
CREATE INDEX IF NOT EXISTS ix_class_created ON waste_classifications(created_at);
CREATE TABLE IF NOT EXISTS collection_requests (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  waste_category VARCHAR(20) NOT NULL,
  quantity DOUBLE PRECISION NOT NULL,
  pickup_address TEXT NOT NULL,
  pickup_date DATE NOT NULL,
  status VARCHAR(12) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_qty_positive CHECK (quantity > 0),
  CONSTRAINT ck_req_status CHECK (status IN ('pending','approved','completed','cancelled')),
  CONSTRAINT ck_req_cat CHECK (waste_category IN ('plastic','paper','metal','glass','organic'))
);
CREATE INDEX IF NOT EXISTS ix_req_user ON collection_requests(user_id);
CREATE INDEX IF NOT EXISTS ix_req_status ON collection_requests(status);
CREATE TABLE IF NOT EXISTS collection_history (
  id SERIAL PRIMARY KEY,
  request_id INTEGER NOT NULL REFERENCES collection_requests(id) ON DELETE CASCADE,
  status VARCHAR(12) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_hist_req ON collection_history(request_id);
CREATE TABLE IF NOT EXISTS admin (
  id SERIAL PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL
);
