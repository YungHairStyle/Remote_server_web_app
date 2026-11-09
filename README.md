# Personal dashboard server prototype

Flask-based experiments for a personal dashboard and file/media interface. The application includes calendar and notes API routes, browser views, file operations, and guest functionality.

## Layout

- `app.py`: routes, configuration, and access checks.
- `templates/`: browser interface.
- `requirements.txt`: Python dependencies.
- `dockerfile` and `docker-compose.yml`: container setup.
- `data/` and `media/`: deployment-related content.

The associated desktop clients are in [Fullscreen_kiosk_project_API_to_server](https://github.com/YungHairStyle/Fullscreen_kiosk_project_API_to_server).

## Local setup

Use an isolated Python environment and inspect `app.py`, the dependency list, and the container configuration before running. Configure your own secret key, authentication/API settings, data paths, and mounted directories. The supplied Compose configuration maps host port 80 to application port 4999 and mounts local folders.

This is a personal prototype with file-management operations and deployment-specific assumptions. It has not been presented as a production-ready or security-reviewed service. Do not expose it publicly without reviewing authentication, access controls, and configuration.

---
[Asaad Hanna — research, CV, and contact](https://yunghairstyle.github.io/)

