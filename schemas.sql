CREATE TABLE authorized_users (
  id SERIAL PRIMARY KEY,
  phone_number TEXT UNIQUE NOT NULL
);

CREATE TABLE meals (
  id SERIAL PRIMARY KEY,
  phone_number TEXT NOT NULL,
  date TEXT NOT NULL,
  meal_time TEXT NOT NULL,
  food_items TEXT NOT NULL,
  calories INTEGER,
  protein INTEGER,
  carbs INTEGER,
  fat INTEGER,
  image_url TEXT,
  analysis_text TEXT,
  FOREIGN KEY (phone_number) REFERENCES authorized_users(phone_number)
);

CREATE TABLE user_goals (
  phone_number TEXT PRIMARY KEY,
  calories INTEGER,
  protein INTEGER,
  carbs INTEGER,
  fat INTEGER
);

CREATE TABLE daily_tracking (
  id SERIAL PRIMARY KEY,
  phone_number TEXT,
  date TEXT,
  total_calories REAL,
  total_protein REAL,
  total_carbs REAL,
  total_fat REAL,
  FOREIGN KEY (phone_number) REFERENCES authorized_users(phone_number)
);