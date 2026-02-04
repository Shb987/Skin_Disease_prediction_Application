# OncoDerma AI - Project Deep Dive

## 1. Project Overview
OncoDerma AI is a web application designed to assist in the early detection of skin diseases, specifically focusing on skin cancer classification. It leverages a pre-trained Convolutional Neural Network (CNN) based on the **ResNet50** architecture to analyze user-uploaded skin lesion images. The application provides an instant diagnosis with a confidence score and includes an integrated AI chatbot (powered by Google's Gemini Pro) to answer user queries related to skin health.

## 2. Technical Architecture

### Backend Framework
-   **Django (Python)**: Serve as the core web framework, handling routing, database interactions, authentication, and view logic.
-   **Docker**: The entire application is containerized using Docker and Docker Compose, ensuring consistent environments across development and deployment.

### Machine Learning Pipeline
-   **Framework**: TensorFlow / Keras.
-   **Model**: ResNet50 (Pre-trained on ImageNet, fine-tuned for skin lesion classification).
-   **Flow**:
    1.  User uploads an image via the Dashboard.
    2.  Image is preprocessed (resized to 224x224, pixel normalization).
    3.  Model predicts the class probabilities.
    4.  The class with the highest probability is returned as the result.
-   **Classes**:
    -   `nv`: Melanocytic nevi
    -   `mel`: Melanoma
    -   `bkl`: Benign keratosis-like lesions
    -   `bcc`: Basal cell carcinoma
    -   `akiec`: Actinic keratoses
    -   `vasc`: Vascular lesions
    -   `df`: Dermatofibroma

### AI Chatbot
-   **Integration**: Google Generative AI (Gemini Pro).
-   **Functionality**: Users can ask questions in the chat interface. The backend sends the prompt to the Gemini API and streams the response back to the user.
-   **Context**: The chatbot is aware of the context of skin disease prediction but acts as a general helpful medical assistant.

### Database
-   **SQLite (Default)**: Used for development to store User data, Profiles, and Scan History (`ScanResult` model).

## 3. Code Structure (Modularized)
The project follows a standard Django app structure but with a modularized view layer for better maintainability.

```
Disease-Prediction/
├── manage.py
├── disease_prediction/       # Project Configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── prediction/               # Main Application
│   ├── models.py             # Database Models (ScanResult, UserProfile)
│   ├── urls.py               # App-level Routing
│   ├── forms.py              # Django Forms
│   ├── templates/            # HTML Templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── upload.html
│   │   ├── result.html
│   │   ├── history.html
│   │   └── ...
│   ├── views/                # Modular Views Package
│   │   ├── __init__.py       # Exposes views to urls.py
│   │   ├── auth_views.py     # Login, Register, Logout
│   │   ├── dashboard_views.py # Dashboard, History, Scan Details
│   │   ├── prediction_views.py # ML Inference Logic
│   │   └── chat_views.py     # Gemini Chatbot Logic
│   └── ...
├── media/                    # Uploaded Images
├── static/                   # CSS/JS Assets
├── Dockerfile
└── docker-compose.yml
```

## 4. Module Breakdown

The monolithic `views.py` has been refactored into focused modules within the `prediction/views/` directory:

### **`auth_views.py`**
Handles all user authentication and account management.
-   **`register_view`**: Handles user registration, including password confirmation and duplicate user checks.
-   **`login_view`**: Authenticates users using Django's built-in auth system.
-   **`logout_view`**: Logs out the current user and redirects to login.
-   *(Note: The `profile_view` was removed as per request).*

### **`dashboard_views.py`**
Manages the main user interface and data visualization.
-   **`dashboard_view`**: Aggregates statistics for the logged-in user (Total Scans, distribution of diagnoses) using Django's `Count` and `Q` objects.
-   **`history_view`**: Retrieves and displays a chronological list of past scan results.
-   **`scan_detail_view`**: Provides a detailed view of a specific scan result, ensuring users can only access their own data.

### **`prediction_views.py`**
Contains the core business logic for image analysis.
-   **`upload_skin_view`**:
    -   Handles the image upload form.
    -   Preprocesses the image (resizing, array conversion) for the TensorFlow model.
    -   Runs the inference (`model.predict`).
    -   Maps predictions to human-readable labels and confidence scores.
    -   Saves the result to the database (`ScanResult`) and redirects to the result page.

### **`chat_views.py`**
Integrates external AI services.
-   **`chat_view`**:
    -   Accepts user prompts via POST requests.
    -   Interfaces with the Google Gemini Pro API.
    -   Maintains a system instruction context for the AI ("You are a helpful medical assistant...").
    -   Returns the AI's response to the frontend.

### **`__init__.py`**
Acts as the package entry point, importing views from the above modules so they can be referenced simply as `views.view_name` in `urls.py`.

## 5. Key Workflows

### Authentication
-   Standard Django Authentication System.
-   `auth_views.py` handles registration (`User.objects.create_user`) and login (`authenticate`, `login`).

### Prediction Flow (`prediction_views.py`)
1.  **Input**: User submits a form with an image.
2.  **Processing**:
    -   Image is saved to `media/uploads/`.
    -   `load_img` and `img_to_array` prepare the image for the model.
    -   `model.predict()` returns a probability array.
3.  **Output**:
    -   The highest probability index maps to a disease name.
    -   A `ScanResult` record is saved to the database linked to the current user.
    -   User is redirected to the Result/Detail page.

### Dashboard & History (`dashboard_views.py`)
-   **Dashboard**: detailed statistics (Total Scans, distribution of diagnoses) are calculated using Django aggregations on the `ScanResult` model.
-   **History**: Lists all previous scans for the logged-in user, ordered by date.

## 6. Deployment
The application is defined in `docker-compose.yml`:
-   **Service**: `web`
-   **Build**: Uses the `Dockerfile` in the root.
-   **Port Mapping**: `8000:8000`
-   **Volume**: Mounts the project directory to `/app` for live reloading during development.
