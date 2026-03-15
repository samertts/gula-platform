from test_library_db import connect


def search_test(keyword):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
    SELECT name,code,category FROM tests
    WHERE name LIKE ?
    """,
        ("%" + keyword + "%",),
    )

    results = c.fetchall()

    conn.close()

    return results


if __name__ == "__main__":

    print(search_test("Glucose"))
