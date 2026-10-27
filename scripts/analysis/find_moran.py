import sqlite3
con=sqlite3.connect(r"decrypted\contact\contact.db"); con.text_factory=bytes; cur=con.cursor()
rows=cur.execute("SELECT username,nick_name,remark,alias FROM contact WHERE nick_name LIKE ? OR remark LIKE ? OR alias LIKE ?",
    ("%示例会话A%".encode(),"%示例会话A%".encode(),"%示例会话A%".encode())).fetchall()
print("matches:", len(rows))
for u,n,r,a in rows:
    print("  ", u.decode("utf-8","replace"), "| nick=", (n or b"").decode("utf-8","replace"), "| remark=", (r or b"").decode("utf-8","replace"), "| alias=", (a or b"").decode("utf-8","replace"))
con.close()
