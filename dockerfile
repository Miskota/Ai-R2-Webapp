FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libasound2 \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install torch==2.0.0+cpu torchaudio==2.0.1+cpu --extra-index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

#COPY . .
COPY app.py /app/
COPY utils /app/utils/
COPY models /app/models/

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]


# docker run -p 8501:8501 \
#  -v $(pwd):/app \
#  -v $(pwd)/models:/app/models \
#  -v $(pwd)/audio:/app/audio \
#  streamlit-webapp

#docker run -p 8501:8501 -v I:/ThesisCode/streamlit-webapp:/app -v I:/ThesisCode/streamlit-webapp/models:/app/models -v I:/ThesisCode/streamlit-webapp/audio:/app/audio streamlit-webapp