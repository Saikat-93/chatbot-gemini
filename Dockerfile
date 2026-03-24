FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

# Install torch CPU version
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]