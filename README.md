# AirVision - AQI Prediction & Forecasting

A web-based Air Quality Index (AQI) prediction and forecasting system built with Django. Features image-based AQI classification using CNN and PM2.5 forecasting using Linear Regression.

## Features

- **AQI Prediction from Sky Images** — Upload a sky image and get AQI prediction using CNN model
- **7-Day AQI Forecast** — PM2.5-based AQI forecasting for major districts of Nepal
- **District-wise Dashboard** — View AQI data, status, and health recommendations for 6 districts
- **User Authentication** — Register, login, and track prediction history
- **Admin Panel** — Manage users, predictions, and AQI records

## Tech Stack

- **Backend:** Django 5.2, Python 3.11
- **Machine Learning:** TensorFlow/Keras (CNN), scikit-learn (Linear Regression)
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript
- **Database:** SQLite
- **Image Processing:** PIL, NumPy

## Districts Covered

| District | PM2.5 (x1, x2, x3) | Status |
|----------|-------------------|--------|
| Lalitpur | 99.8, 60.8, 65.8 | Unhealthy |
| Bhaktapur | 40.9, 34.5, 69.4 | Moderate |
| Kathmandu | 19.1, 19.2, 4.4 | Good |
| Dhankuta | 15.1, 13.1, 38.0 | Good |
| Kanchanpur | 3.2, 4.2, 5.1 | Good |
| Dang | 57.5, 50.3, 63.9 | Moderate |

## Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd AQI\ Prediction
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start server**
   ```bash
   python manage.py runserver
   ```

6. **Access the app** — Open `http://127.0.0.1:8000/`

## Usage

- **Landing Page** — View AQI overview for all districts
- **Forecast** — Navigate to `/forecast/<city>/` for 7-day AQI forecast
- **Dashboard** — Register/Login, upload sky images for AQI prediction, view history
- **Admin** — `/myadmin/` for managing data

## Model Architecture

- **CNN Classifier:** 3 convolutional layers (32, 64, 128 filters) + MaxPooling + Dense layers
- **Image Input:** 150×150 RGB
- **Classes:** Good (AQI 35), Moderate (AQI 75), Unhealthy (AQI 165)
- **PM2.5 Predictor:** Linear Regression model trained on historical PM2.5 data

## Dataset

- **Kaggle AQI Image Dataset** — ~8600 images across 4 classes (good, moderate, unhealthy, Unhealthy for Sensitive Groups)
- **PM2.5 Data** — Historical PM2.5 readings from `pm 2.5.xlsx`


