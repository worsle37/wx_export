import glob
pats=[b"CREATE TABLE Msg_", b"real_sender_id", b"Msg_", b"WCDB_CT_message_content", b"Name2Id"]
for f in sorted(glob.glob("mem/pid_*.bin")):
    d=open(f,"rb").read()
    out=[]
    for p in pats:
        out.append((p.decode(), d.count(p)))
    print(f, out)
