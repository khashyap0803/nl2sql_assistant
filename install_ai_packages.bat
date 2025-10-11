@echo off
REM Temporary script to install AI packages by bypassing PostgreSQL SSL certificate issue

echo Installing PyTorch and AI packages...
echo This bypasses the PostgreSQL SSL certificate that's blocking pip

REM Clear SSL certificate environment variables
set SSL_CERT_FILE=
set REQUESTS_CA_BUNDLE=
set CURL_CA_BUNDLE=

REM Install PyTorch from regular PyPI (will be larger, includes CUDA)
echo.
echo Step 1: Installing PyTorch...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org torch torchvision torchaudio

REM Install sentence-transformers
echo.
echo Step 2: Installing sentence-transformers...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org sentence-transformers

REM Install faiss-cpu
echo.
echo Step 3: Installing faiss-cpu...
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org faiss-cpu

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Verifying installations...
python -c "import torch; import sentence_transformers; import faiss; print('✅ All packages installed successfully!')"

pause

