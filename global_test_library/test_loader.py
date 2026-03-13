from test_library_db import connect


def add_test(name, code, category, unit, min_val, max_val):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
    INSERT INTO tests(name,code,category,unit,normal_min,normal_max)
    VALUES(?,?,?,?,?,?)
    """,
        (name, code, category, unit, min_val, max_val),
    )

    conn.commit()
    conn.close()
