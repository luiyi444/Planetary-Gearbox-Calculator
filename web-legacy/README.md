# Legacy web interface (optional)

The same calculator as a Streamlit page. It is **not** needed: the desktop app in
the project root does everything this does, with the standard library only.

Keep this folder only if you want the browser version. It needs third-party
packages, so it needs an internet connection the first time:

```powershell
cd web-legacy
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then either:

```powershell
.\.venv\Scripts\streamlit.exe run app_streamlit.py
```

or check that the page still renders:

```powershell
.\.venv\Scripts\python.exe -m pytest test_app_streamlit.py -q
```

`app_streamlit.py` imports `gearbox.py` from the parent folder, so both UIs always
share the same calculation core. `diagram.py` (matplotlib) is only used here.
`.streamlit/config.toml` pins port 8501 and suppresses the first-run email prompt.
