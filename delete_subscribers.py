import sqlite3

def clear_table():
    # Connect to the database
    conn = sqlite3.connect("your_database.db")
    cursor = conn.cursor()

    # Delete all records from the table
    cursor.execute("DELETE FROM subscribers")
    conn.commit()  # Save changes

    # Optional: Reset auto-increment ID
    cursor.execute("VACUUM")
    conn.commit()

    # Close connection
    conn.close()
    print("All records deleted successfully!")

# Run the function
if __name__ == "__main__":
    clear_table()
