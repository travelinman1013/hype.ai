FEATURE:
Build the backend service for a fitness application named hype.ai. The service will act as the core logic connecting a user's real-time heart rate from Apple HealthKit to their Spotify account, creating a bio-responsive workout playlist.

Core Functionality:

Authentication: Implement a secure, asynchronous authentication module using FastAPI that handles OAuth 2.0 for both Apple HealthKit and the Spotify Web API. The service must securely store and manage user tokens.

Real-time Data Ingestion: Create a WebSocket or long-polling endpoint to receive a continuous stream of heart rate data (in BPM) from the user's wearable device via the mobile frontend.

Heart Rate to Music Logic: Develop a central logic module that maps incoming BPM values to predefined workout zones (e.g., Warm-up: 90-110 BPM, Cardio: 111-140 BPM, Peak: 141+ BPM). Each zone should correspond to specific audio features in Spotify (e.g., target tempo, energy, danceability).

Spotify API Control: Build a robust Spotify API client that can:

Search for tracks matching the audio features determined by the user's current heart rate zone.

Control user playback by adding the selected track to the queue. The transition should be seamless, ideally waiting for the current song to finish before starting the next one.

Handle API rate limiting and errors gracefully.

Freemium Model Support: The architecture must support a freemium model. The core heart rate-to-music sync will be free. Design a database schema (using SQLModel) and API endpoints to manage user subscriptions and unlock premium features like workout history and advanced analytics.

EXAMPLES:
No examples currently exist in the examples/ folder. The following patterns should be created and used as a reference for the implementation:

examples/api_client/: Create a sample asynchronous API client pattern using httpx. It should include clear error handling, token refresh logic, and Pydantic models for data validation of API responses. This will serve as the template for both the HealthKit and Spotify clients.

examples/modular_fastapi/: Provide an example of a FastAPI application structured into modular components (e.g., a users module with routes.py, models.py, services.py). This will establish the architectural pattern for the main application.

DOCUMENTATION:
Spotify Web API Reference: https://developer.spotify.com/documentation/web-api/

Apple HealthKit Developer Documentation: https://developer.apple.com/documentation/healthkit/

FastAPI Documentation: https://fastapi.tiangolo.com/

OTHER CONSIDERATIONS:
Spotify API Commercialization Rules: This is the most critical constraint. The Spotify Developer Policy strictly limits the commercialization of "Streaming" applications. The app cannot be sold or have ads. Our freemium model, where the music control is free and we charge for separate fitness features, is designed to comply with these terms. The implementation must not violate this.

User Experience for Music Transition: Avoid abrupt music changes. The system should intelligently queue the next track to play after the current one finishes. Do not interrupt a song mid-play unless the user's heart rate changes dramatically for a sustained period.

Data Privacy: All user health data is sensitive. Ensure compliance with best practices for storing and handling this information, and only request the specific HealthKit permissions required.

Scalability: The backend should be designed to handle concurrent connections from many users streaming their heart rate data simultaneously. Choose an appropriate asynchronous server (like Uvicorn) for deployment.