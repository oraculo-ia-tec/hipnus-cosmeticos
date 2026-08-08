"""
skills/ — Módulos reutilizáveis do HIPNUS COSMÉTICOS
=====================================================
Cada skill encapsula uma capacidade transversal que pode ser usada
tanto pelo backend (FastAPI) quanto pelo frontend (Streamlit).

Skills disponíveis:
  auth_skill   — JWT, bcrypt, normalização de roles
  asaas_skill  — cliente HTTP Asaas + cálculo de split
  email_skill  — envio de e-mails via SMTP
  db_skill     — resolução de DATABASE_URL e sessão SQLAlchemy
"""
