
# CHAPTER 4. METHODOLOGY

## 4.4 Module Description

This section explains about seven modules:

* Image Acquisition Module
* Preprocessing Module
* CNN Prediction Module
* Risk Assessment Module
* Authentication Module
* User Interface Module
* AI Consultation Module

### 4.4.1 Image Acquisition Module

Image acquisition is the first step that is performed in the proposed system. The system provides a web-based interface where users can upload high-resolution images of skin lesions. The module utilizes a Django form (`UploadForm`) to capture essential metadata such as the patient's name and scan type alongside the image file. This ensures that the input data is correctly associated with the specific patient record for tracking and analysis.

### 4.4.2 Preprocessing Module

Before the image can be analyzed by the deep learning model, it must undergo preprocessing to match the network's input requirements. The preprocessing module handles the conversion of the raw uploaded image into a numerical format. It leverages the TensorFlow Keras image utility to:
1.  Load the image from the in-memory byte stream.
2.  Resize the image to a fixed dimension of **28x28 pixels**, which is the input size expected by the trained model.
3.  Convert the image into a NumPy array.
4.  Expand the dimensions to create a batch of size one (1, 28, 28, 3), making it compatible with the model's prediction pipeline.

### 4.4.3 CNN Prediction Module

The core of the system is the Convolutional Neural Network (CNN) module. The system loads a pre-trained Keras model (`skin_cancer_model.h5`) which has been trained to recognize specific patterns associated with various skin diseases. When the preprocessed image is passed through this network, it performs feature extraction and classification across seven distinct classes of skin lesions, including Melanocytic nevi, Melanoma, and Basal cell carcinoma.

### 4.4.4 Risk Assessment Module

Once the CNN module generates a prediction, the Risk Assessment module interprets the results. It identifies the class with the highest probability score and maps this diagnosis to a clinical risk level. The system uses a predefined `risk_map` to categorize conditions into levels such as "Low Risk," "Moderate Risk," or "Very High Risk" (e.g., for Melanoma). This provides immediate, actionable context to the user beyond just the technical diagnosis name.

### 4.4.5 Authentication Module

To ensure the security and privacy of sensitive medical data, the Authentication Module manages user access. It employs Django's built-in authentication system to handle user registration, login, and session management. Only authenticated users can upload scans, view prediction results, and access their dashboard history, ensuring that patient data remains confidential.

### 4.4.6 User Interface Module

The User Interface (UI) module serves as the bridge between the user and the system's functionalities. Built using Django templates (`scan_detail.html`, `dashboard.html`), it provides a responsive and intuitive layout. Key features include a dashboard for viewing past scan history, a dedicated upload page for new analyses, and detailed results pages that display the diagnosis, confidence score, and risk level in a user-friendly format.

### 4.4.7 AI Consultation Module

The AI Consultation Module enhances the user experience by integrating **OncoDerma AI**, a chatbot powered by the Google Gemini 2.5 Flash model. This module allows users to ask follow-up questions regarding their specific diagnosis. It dynamically constructs a context-aware prompt containing the patient's name, diagnosis, and risk level, enabling the AI to provide tailored medical context, explanation of symptoms, and general treatment advice while adhering to safety protocols.
