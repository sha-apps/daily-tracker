import db
from datetime import date, timedelta
import random

db.init_db()

categories = ["🔥 Critical", "📅 Goals", "⚡ Quick Tasks", "🌱 Backlog"]
today = date.today()

# Add tasks for the last 10 days
for i in range(10):
    day = today - timedelta(days=i)
    for _ in range(random.randint(1, 3)):
        task_title = f"Task for {day}"
        category = random.choice(categories)
        db.add_task(task_title, category, day)
        
        # Mark some as completed
        if random.random() > 0.3:
            # We need to get the ID of the task we just added, but add_task doesn't return it.
            # For simplicity in this seed script, we'll just update random tasks later or assume some are done if I updated add_task logic, 
            # but here I'll just manually update status for recent tasks.
            pass

# Manually update some tasks to completed
import sqlite3
conn = sqlite3.connect(db.DB_NAME)
c = conn.cursor()
c.execute("UPDATE tasks SET status = 'Completed' WHERE id % 2 = 0")
conn.commit()
conn.close()

print("Database seeded!")
