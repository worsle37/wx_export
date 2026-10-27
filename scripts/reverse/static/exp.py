import pefile
p=r"C:\Program Files\Tencent\Weixin\Weixin.dll"
pe=pefile.PE(p, fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
exps=[e.name.decode(errors='ignore') for e in (pe.DIRECTORY_ENTRY_EXPORT.symbols if hasattr(pe,'DIRECTORY_ENTRY_EXPORT') else [])]
print("total exports:", len(exps))
import re
pats=re.compile(r'key|cipher|kdf|pbkdf|sqlite|wcdb|aes|hmac', re.I)
sel=[e for e in exps if pats.search(e)]
print("key-related:", len(sel))
for e in sel[:60]: print("  ", e)
