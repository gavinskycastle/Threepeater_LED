# gif_to_header.py

Small helper to convert a GIF file into a C header that embeds the raw GIF bytes
as a `const uint16_t` array.

Requirements
- Python 3.6+
- Pillow (optional - used to detect GIF width/height/frames)

Install Pillow (PowerShell):

```powershell
python -m pip install --user Pillow
```

Example

```powershell
python tools\gif_to_header.py my_anim.gif -o src\my_anim.h -n my_anim
```

Options of note
- `--assume-size W H` — if you want to force the dimensions (script will still embed full GIF bytes)
