# a simple bash program to trigger the space removing python file
# and commit the changes
python3 rm_trailing_space.py
git add .
git commit -m "removed trailing spaces"
git push origin main
