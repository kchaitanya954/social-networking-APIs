# Social Networking API

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Design Choices](#design-choices)
- [License](#license)

## Introduction
This is a social networking API built using Django and Django REST Framework. It allows users to create accounts, send friend requests, manage friendships, and interact with user activities. The application is containerized using Docker and can be easily deployed on cloud platforms.

### Features
- User authentication and management
- Sending and managing friend requests
- Friendship management
- User blocking/unblocking
- Activity logging
- Caching with Redis
- PostgreSQL as the database
- Dockerized for easy deployment

### Technologies Used

- Django
- Django REST Framework
- PostgreSQL
- Redis
- Docker
- Django Redis Cache

## Installation

### Prerequisites
- Python 3.8 or higher
- [Docker](https://www.docker.com/get-started) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.

### Steps to Set Up the Project
1. **Clone the repository:**
   ```bash
   git clone https://github.com/kchaitanya954/social-networking-APIs.git
   cd social-networking-APIs/social-networking-project
   ```
2. **Build and run the Docker containers:**
    ```bash
   sudo docker compose up --build
   ```
   This command will build the Docker images and start the containers.

## Usage

1. **The Django Application will be accessible at http://localhost:8000**.
2. Use Postman or any API client to interact with the endpoints. 
    Postman collections:
    [Postman collections](https://api.postman.com/collections/14846803-01efcb02-70c6-4f56-aebb-b8b43d9c2751?access_key=PMAT-01J8MRAWCSYCPTHGZAJ5PQEHHY)
3. To see available endpoints, access the Django admin panel at http://localhost:8000/admin/. or API Documentation (Swagger): http://127.0.0.1:8000/swagger/.

## API Documentation
- API documentation(Swagger) is available at [Swagger API documents](http://127.0.0.1:8000/swagger/).

### API Endpoints
1. User Login/SignUp:
    - API to SignUp: POST auth/signup/ 
    - API to Login: POST auth/login/
    - API to refresh token: POST token/refresh/
    
2. Friend List/ Requests:
    - API to send friend request: POST friends/request/
    - API to Accept/Reject friend request: PUT friends/request/<pk>
    - API to Block User: POST users/<user_id>/block/
    - API to UnBlock User: DELETE users/<user_id>/block/
    - API to list Pending friend request: GET friends/pending/
    - API to list friends: GET friends/list/

3. Other Functionalities:
    - API to search User: GET users/search/?q=<search_query>
    - API to fetch User activity: GET user/activity/


## Design Choices
- Django and Django REST Framework: Chosen for their ease of use, scalability, and community support.
- PostgreSQL: Used for its robustness and advanced features, such as full-text search.
- Redis: Implemented for caching frequently accessed data, enhancing performance.
- Docker: Enables easy deployment and management of the application across different environments.
- Swagger- For API documentation.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

