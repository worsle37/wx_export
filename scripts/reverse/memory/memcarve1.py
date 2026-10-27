import re
d=open("mem/pid_10292.bin","rb").read()
for name in ["示例会话B".encode(), b"示例会话C", "示例".encode()]:
    i=d.find(name)
    print(name[:20], "->", hex(i) if i>=0 else "not found")
# 群消息格式：wxid_xxx:\n 正文
pat=re.compile(rb"(wxid_[0-9a-zA-Z]{6,20}@chatroom|wxid_[0-9a-zA-Z]{6,20}):\n")
ms=[m.start() for m in pat.finditer(d)]
print("group-msg-prefix hits:", len(ms))
for off in ms[:3]:
    print(repr(d[off:off+120]))
