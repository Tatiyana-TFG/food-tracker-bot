import psycopg2
import os


class UserService:
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self.AUTH_PASSWORD = "3233"  # Authorization password

    def register_user(self, phone_number, password=None):
        """
        Register a new user. Authorizes them if correct password is provided.
        Returns: dict with status and message
        """
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Check if user exists
            cursor.execute(
                "SELECT authorized FROM authorized_users WHERE phone_number = %s",
                (phone_number,)
            )
            result = cursor.fetchone()

            # If password matches, authorize the user
            is_authorized = password == self.AUTH_PASSWORD

            if result is None:
                # New user - insert with authorization based on password
                cursor.execute(
                    """
                    INSERT INTO authorized_users 
                    (phone_number, authorized) 
                    VALUES (%s, %s)
                    """,
                    (phone_number, is_authorized)
                )
                conn.commit()
                msg = "User registered and authorized!" if is_authorized else "User registered. Send password 3233 to get authorized."
                return {'status': 'success', 'message': msg}

            # Existing user - update authorization if password provided
            if password:
                if is_authorized:
                    cursor.execute(
                        "UPDATE authorized_users SET authorized = TRUE WHERE phone_number = %s",
                        (phone_number,)
                    )
                    conn.commit()
                    return {'status': 'success', 'message': 'User authorized successfully!'}
                else:
                    return {'status': 'error', 'message': 'Incorrect password'}

            return {'status': 'existing', 'message': 'User already registered'}

        except Exception as e:
            print(f"Error in register_user: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if conn:
                conn.close()

    def set_user_goals(self, phone_number, calories, protein, carbs, fat):
        """Set user's nutritional goals"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Check if user is authorized
            cursor.execute(
                "SELECT authorized FROM authorized_users WHERE phone_number = %s",
                (phone_number,)
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                return {'status': 'error', 'message': 'User not authorized. Send password 3233 to get authorized.'}

            # Insert or update user goals
            cursor.execute("""
                INSERT INTO user_goals (phone_number, calories, protein, carbs, fat)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (phone_number) 
                DO UPDATE SET 
                    calories = EXCLUDED.calories,
                    protein = EXCLUDED.protein,
                    carbs = EXCLUDED.carbs,
                    fat = EXCLUDED.fat
            """, (phone_number, calories, protein, carbs, fat))

            conn.commit()
            return {'status': 'success', 'message': 'Goals updated successfully'}

        except Exception as e:
            print(f"Error in set_user_goals: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if conn:
                conn.close()

    def get_user_goals(self, phone_number):
        """Get user's nutritional goals"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Check if user is authorized
            cursor.execute(
                "SELECT authorized FROM authorized_users WHERE phone_number = %s",
                (phone_number,)
            )
            auth_result = cursor.fetchone()

            if not auth_result or not auth_result[0]:
                return {'status': 'error', 'message': 'User not authorized. Send password 3233 to get authorized.'}

            # Get goals
            cursor.execute("""
                SELECT calories, protein, carbs, fat 
                FROM user_goals
                WHERE phone_number = %s
            """, (phone_number,))

            result = cursor.fetchone()
            if result:
                return {
                    'status': 'success',
                    'goals': {
                        'calories': result[0],
                        'protein': result[1],
                        'carbs': result[2],
                        'fat': result[3]
                    }
                }
            return {'status': 'error', 'message': 'No goals found'}

        except Exception as e:
            print(f"Error in get_user_goals: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if conn:
                conn.close()