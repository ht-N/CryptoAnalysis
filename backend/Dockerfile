# Step 1: Use an official Python runtime as a parent image
FROM python:3.11-slim

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Install system dependencies required for headless Chrome and other libraries
# Install wget, unzip, and jq (for parsing JSON)
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    jq \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libasound2 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create directories for Chrome user data and ensure proper permissions
RUN mkdir -p /tmp/chrome-data && chmod 777 /tmp/chrome-data && \
    mkdir -p /tmp/chrome_user_data && chmod 777 /tmp/chrome_user_data && \
    mkdir -p /app/chrome_logs && chmod 777 /app/chrome_logs

# Step 4: Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb || apt-get install -f -y
RUN rm google-chrome-stable_current_amd64.deb

# Step 5: Install ChromeDriver using the new official JSON endpoints (more reliable)
RUN apt-get update && apt-get install -y curl unzip jq && \
    # Chrome và ChromeDriver bản Stable mới nhất
    JSON_URL=https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json && \
    CHROME_URL=$(curl -s $JSON_URL | jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="linux64") | .url') && \
    CHROMEDRIVER_URL=$(curl -s $JSON_URL | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') && \
    # Chrome
    mkdir -p /opt/chrome && \
    curl -sSL $CHROME_URL -o /tmp/chrome-linux64.zip && \
    unzip -q /tmp/chrome-linux64.zip -d /opt/chrome && \
    rm /tmp/chrome-linux64.zip && \
    ln -s /opt/chrome/chrome-linux64/chrome /usr/bin/google-chrome && \
    # ChromeDriver
    curl -sSL $CHROMEDRIVER_URL -o /tmp/chromedriver-linux64.zip && \
    unzip -q /tmp/chromedriver-linux64.zip -d /usr/local/bin && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver-linux64.zip /usr/local/bin/chromedriver-linux64

# Step 6: Copy and install Python requirements
# This is done in a separate step to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 7: Copy the rest of the application's code into the container
COPY . .

# Step 8: Expose the port the app runs on
EXPOSE 8000

# Step 9: Define the command to run the application
# Add environment variables for Chrome stability
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome
ENV CHROME_NO_SANDBOX=1
ENV CHROME_DISABLE_GPU=1

# Create a non-root user for Chrome to run safely
RUN useradd -m -s /bin/bash chromeuser && \
    chown -R chromeuser:chromeuser /tmp && \
    chown -R chromeuser:chromeuser /app

# Switch to non-root user
USER chromeuser

# This will start the FastAPI server and the background pipeline process
CMD ["python", "main.py"] 