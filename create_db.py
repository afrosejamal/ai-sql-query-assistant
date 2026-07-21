"""
Creates a sample company.db SQLite database with Employees, Departments,
and Sales tables so the AI SQL Assistant has something interesting to query.

Run this once: python create_db.py
"""
import sqlite3

conn = sqlite3.connect("company.db")
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS sales;

CREATE TABLE departments (
    dept_id INTEGER PRIMARY KEY,
    dept_name TEXT NOT NULL
);

CREATE TABLE employees (
    emp_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    dept_id INTEGER,
    salary INTEGER,
    hire_date TEXT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY,
    emp_id INTEGER,
    amount INTEGER,
    sale_date TEXT,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);
""")

departments = [
    (1, "Engineering"),
    (2, "Sales"),
    (3, "Marketing"),
    (4, "HR"),
]

employees = [
    (1, "Aditi Sharma", 1, 95000, "2021-03-15"),
    (2, "Rohan Mehta", 1, 88000, "2020-07-01"),
    (3, "Priya Nair", 2, 72000, "2022-01-10"),
    (4, "Karan Verma", 2, 76000, "2019-11-23"),
    (5, "Sneha Iyer", 3, 65000, "2023-02-05"),
    (6, "Arjun Reddy", 4, 60000, "2021-09-18"),
    (7, "Divya Rao", 1, 102000, "2018-05-30"),
    (8, "Vikram Singh", 2, 81000, "2022-08-12"),
]

sales = [
    (1, 3, 15000, "2024-01-10"),
    (2, 4, 22000, "2024-01-15"),
    (3, 3, 18000, "2024-02-01"),
    (4, 8, 30000, "2024-02-20"),
    (5, 4, 12000, "2024-03-05"),
    (6, 8, 27000, "2024-03-18"),
]

cur.executemany("INSERT INTO departments VALUES (?, ?)", departments)
cur.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", employees)
cur.executemany("INSERT INTO sales VALUES (?, ?, ?, ?)", sales)

conn.commit()
conn.close()

print("✅ company.db created successfully with sample data!")