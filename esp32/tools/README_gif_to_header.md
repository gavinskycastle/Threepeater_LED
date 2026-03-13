# gif_to_header.py

Small helper to convert a GIF file into a C header that embeds the raw GIF bytes
as a `const uint8_t` array to match the style used in
`include/AnimatedGIF/test_images/*.h`.

Requirements
- Python 3.6+
- Pillow (optional - used to detect GIF width/height/frames)

Install Pillow (PowerShell):

```powershell
python -m pip install --user Pillow
```

Example

```powershell
python tools\gif_to_header.py data\gifs\my_anim.gif -o include\AnimatedGIF\test_images\my_anim.h -n my_anim
```

Options of note
- `--assume-size W H` — if you want to force the dimensions (script will still embed full GIF bytes)
- `--no-progmem` — omit the `PROGMEM` token after the array declaration

Notes
- The script embeds the raw GIF file bytes (so the output header is identical in content to a byte-for-byte GIF dump).
- The header comment includes width/height and frame count (if Pillow is available to detect them).
