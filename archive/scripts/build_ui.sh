#!/bin/bash
cd ~/gula-platform
python3 build_frontend_ui.py
docker restart gula-frontend
