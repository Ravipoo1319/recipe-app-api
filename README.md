# Recipe APP
Welcome to the Recipe APP repository! This project is a Django REST Framework (DRF) based web application developed using Test Driven Development (TDD) practices. The app provides API endpoints for managing recipes, ingredients, users, and tags. Docker is used for project configuration, and GitHub Actions are employed for Continuous Integration/Continuous Deployment (CI/CD). The application is deployed on AWS EC2, utilizing PostgreSQL as the database. Additionally, the Django built-in authentication system is customized to use email instead of a username.

## Table of Contents
Installation
Usage
Running the API
API Documentation
Testing
Linting
Contact

## Installation
To set up the project locally, follow these steps:

Clone the repository:

bash
Copy code
git clone https://github.com/Ravipoo1319/recipe-app-api.git
cd recipe-app-api

## Running the API

To run the API using Docker Compose, execute the following commands:

```bash
docker-compose build
docker-compose up
```

The API will be available at `http://localhost:8000/api/`.

## API Documentation

API documentation is generated using the drf-spectacular library and is available at `http://localhost:8000/api/docs/`. You can explore and test the API using the Swagger interface provided.

## Testing

Tests are written following Test Driven Development (TDD) techniques and are located in the `tests/` directory of each app. You can run the tests using the following command:

```bash
docker-compose run --rm app sh -c "python manage.py test"
```

## Linting

We use flake8 for code linting. You can check for code formatting issues with the following command:

```bash
docker-compose run --rm app sh -c "flake8"
```

## Contact

If you have any questions or suggestions regarding this project, feel free to contact:

- Ravindra Pawar
- ravindrapawar1315@gmail.com
- Project Repository: [Link to GitHub Repository](https://github.com/Ravipoo1319/recipe-app-api.git)
