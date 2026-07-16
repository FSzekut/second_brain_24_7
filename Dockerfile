FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./.streamlit ./.streamlit
COPY ./src ./src

EXPOSE 8501

HEALTHCHECK CMD python -c "import urllib.request as u; u.urlopen('http://localhost:${PORT:-8501}/_stcore/health')" || exit 1

ENTRYPOINT streamlit run src/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0