@echo off
cd /d "c:\Users\lenovo\Documents\stock-sight-ai-ind"
:loop
python -m streamlit run Home.py --server.port 8502 --server.headless true
timeout /t 5 /nobreak >nul
goto loop
