FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# compile Tailwind at build time (optional)
# RUN npm install -g tailwindcss && tailwindcss -i ./static/css/input.css -o ./static/css/tailwind.css --minify

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]