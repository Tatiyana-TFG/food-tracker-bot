CREATE TABLE IF NOT EXISTS authorized_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phone_number TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS meals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
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

CREATE TABLE IF NOT EXISTS user_goals (
  phone_number TEXT PRIMARY KEY,
  calories INTEGER,
  protein INTEGER,
  carbs INTEGER,
  fat INTEGER,
  FOREIGN KEY (phone_number) REFERENCES authorized_users(phone_number)
);

CREATE TABLE IF NOT EXISTS daily_tracking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phone_number TEXT,
  date TEXT,
  total_calories REAL,
  total_protein REAL,
  total_carbs REAL,
  total_fat REAL,
  FOREIGN KEY (phone_number) REFERENCES authorized_users(phone_number)
);