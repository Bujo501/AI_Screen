import mysql.connector
from mysql.connector import Error
print("Connecting to MySQL Database");
def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",          # Your MySQL host
            user="root",               # Your MySQL username
            password="Airesume@s2",  # Your MySQL password
            database="testing1"   # Database name
        )
        if connection.is_connected():
            print("✅ Connected to MySQL Database")
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

