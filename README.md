# SkillLink
A Real-Time Freelance Service Marketplace

# Folder Structure
```
skilllink/
├── skilllink/
│   ├── __init__.py
│   ├── settings.py
│   ├── asgi.py
│   └── celery.py
├── manage.py
├── users/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── chat/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── payment/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
└── projects/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    └── views.py
```

# Tech Stack Categories:

1. Web Framework: Django (Python-based, supports both synchronous and asynchronous operations)
2. ASGI Server: Daphne (replaces the default WSGI server for async support)
3. Real-time Communication: Django Channels (WebSocket support)
4. API Framework: Django REST Framework
5. Task Queue: Celery (django-celery-results, django-celery-beat)
6. Database: SQLite/PostgreSQL (not yet visible in your setup)
7. Frontend: (not yet evident in your project)

Daphne is an ASGI (Asynchronous Server Gateway Interface) server for Django. Here's what it does:

1. Asynchronous Support: Unlike the synchronous Django development server, Daphne handles asynchronous requests and responses, allowing your Django application to handle multiple concurrent connections efficiently.

2. WebSocket Support: Daphne is required when using Django Channels for WebSocket functionality—enabling real-time, bidirectional communication between clients and server (chat, notifications, live updates).

3. Production-Ready: Daphne is designed to be used in production environments (alongside other components) as it's more robust than Django's development server.

4. Channels Integration: It's the standard ASGI server for running Django with the Channels library, which extends Django to handle protocols beyond HTTP (like WebSocket).

Django Channels extends Django to handle asynchronous protocols beyond HTTP, particularly WebSockets. Here's what it enables:

Key Features:

1. WebSocket Support: Enables real-time, bidirectional communication between client and server (unlike traditional HTTP request-response)

2. Asynchronous Handling: Allows Django to handle multiple connections simultaneously without blocking

3. Protocol Agnostic: Can handle HTTP, WebSocket, MQTT, chatbots, IoT protocols, etc.

4. Background Tasks: Run tasks outside the request-response cycle

Real-World Use Cases:

* Chat Applications: Real-time messaging (likely why you have a chat app)
* Live Notifications: Push notifications to users instantly
* Collaborative Editing: Multiple users editing simultaneously
* Live Dashboards: Real-time data updates
* Gaming: Multiplayer game state synchronization
* Live Feeds: Social media-style live updates

### ⚡ The Core Difference

* **Traditional Django:** One request → One response. (Static)
* **Django Channels:** One connection → Constant messages. (Live)
