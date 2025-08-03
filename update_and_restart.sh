#!/bin/bash
cd /home/chapter_3_kgf/supertg
git stash push vars.py
git pull
git stash pop
sudo systemctl restart tgbot
