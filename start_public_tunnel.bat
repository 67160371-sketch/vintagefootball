@echo off
chcp 65001 > nul
title Vintage Football Store - Online Server
echo ========================================================
echo   ⚽ Vintage Football Shirts E-Commerce System
echo   โครงงานพัฒนาระบบร้านขายเสื้อฟุตบอลมือสองวินเทจหายาก
echo ========================================================
echo.
echo [1/2] กำลังเปิดเว็บเซิร์ฟเวอร์ Flask (Port 5000)...
start "Flask Server" python app.py
timeout /t 3 /nobreak > nul

echo [2/2] กำลังเชื่อมต่อ Cloudflare Tunnel สร้างลิงก์ออนไลน์...
echo.
echo * สังเกตบรรทัดที่มีข้อความ "https://xxxx.trycloudflare.com"
echo * นั่นคือลิงก์ออนไลน์ที่สามารถก๊อปปี้ไปส่งให้อาจารย์หรือเพื่อนเปิดได้ทันที
echo * เปิดหน้าต่างนี้ทิ้งไว้ตลอดการใช้งาน (ห้ามปิดหน้าต่าง)
echo ========================================================
echo.
.\cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
