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
    # Install dependencies for Chrome
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Step 4: Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb || apt-get install -f -y
RUN rm google-chrome-stable_current_amd64.deb

# Step 5: Install ChromeDriver using the new official JSON endpoints (more reliable)
RUN CHROMEDRIVER_URL=$(wget -q -O - https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') && \
    wget -q --continue -P /usr/local/bin/ $CHROMEDRIVER_URL && \
    unzip -q /usr/local/bin/chromedriver-linux64.zip -d /usr/local/bin/ && \
    rm /usr/local/bin/chromedriver-linux64.zip && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver

# Step 6: Copy and install Python requirements
# This is done in a separate step to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 7: Copy the rest of the application's code into the container
COPY . .

# Step 8: Expose the port the app runs on
EXPOSE 8000

# Step 9: Define the command to run the application
# This will start the FastAPI server and the background pipeline process
CMD ["python", "main.py"] 