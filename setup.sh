npm install
pip install -r requirements.txt
if ! pyenv versions | grep -q 3.12.0; then
    pyenv install 3.12.0
fi
pyenv local 3.12.0
python -m venv venv
. ./venv/bin/activate