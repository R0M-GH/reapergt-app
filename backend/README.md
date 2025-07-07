# ReaperGT (@reaper_gt)

> Don't blink.

![Logo](logo.png)

## Architecture

![Architecture](./architecture.drawio.svg)

## Component Index

### 1. Event Trigger & Dispatch

-   **1. EventBridge – 1m**  
    Triggers a Lambda every minute to start the scraping cycle.

-   **2. Lambda – Dispatcher**  
    Fetches all CRNs from DynamoDB and dispatches each one to the scrape queue.

### 2. Scraper Service

-   **3. SQS – Scrape Queue**  
    Queue for CRNs to be scraped.

-   **4. Lambda – Scraper**  
    Scrapes the course page for availability and forwards open CRNs to the notify queue.

### 3. Notification Service

-   **5. SQS – Notify Queue**  
    Queue for open CRNs awaiting user notification.

-   **6. Lambda – Notifier**  
    Looks up subscribers and sends alerts to the Telegram bot.

### 4. Console Service

-   **7. Telegram**  
    Primary interface for users to subscribe, unsubscribe, or list CRNs.

-   **8. REST API (API Gateway)**  
    Handles incoming webhook messages from Telegram.

-   **9. Lambda – Console**  
    Parses commands and updates user/CRN data in DynamoDB.

### 5. Data Layer

-   **10. Secrets Manager**  
    Stores secrets for the application.

-   **11. DynamoDB – crns**  
    Stores course metadata and CRN subscription info.

-   **12. DynamoDB – users**  
    Stores user info and the CRNs they are subscribed to.

## Features

-   Serverless architecture using AWS Lambda and SQS
-   Real-time CRN alerts via Telegram
-   Fully decoupled and scalable services
-   Telegram command interface for user interaction
-   Simple infrastructure with no Redis or EC2 instances

## Example Commands

-   `/add 29333` – Subscribe to a CRN
-   `/rem 29333` – Unsubscribe
-   `/list` – List currently subscribed CRNs

## Deployment Notes

-   Polling interval: 60 seconds via EventBridge
-   Secrets and config stored in AWS Secrets Manager
-   All services are stateless and scale independently

## Future Improvements

-   Add web interface for user management
-   TTL support in DynamoDB to auto-clean expired CRNs
-   Waitlist parsing and advanced notification rules
